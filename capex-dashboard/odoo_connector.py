"""
Wakuli Retail Analytics - Odoo Connector
==========================================
Handles all Odoo XML-RPC API communication.

Generic P&L fetcher: reads ACCOUNT_MAP from config.py and queries
account.move.line for any configured account code range. Outputs a
standardized DataFrame that the KPI engine can consume directly.

Also provides:
  - Account discovery (list all accounts in the chart of accounts)
  - Invoice detail viewer
  - PDF attachment fetcher
  - Optional POS / HR / Stock model queries
"""

import streamlit as st
import pandas as pd
import xmlrpc.client
import os
from config import (
    RETAIL_HOLDING_ID, ODOO_ID_TO_STORE, STORE_LOCATIONS,
    CAPEX_ACCOUNTS, ACCOUNT_MAP, APP_CONFIG, ODOO_MODULES,
    REVENUE_TO_PRODUCT_CATEGORY, PRODUCT_CATEGORIES,
    get_category_for_account_code, get_sign_multiplier,
)


# ──────────────────────────────────────────────
# CONNECTION HELPERS
# ──────────────────────────────────────────────

def get_secret(key, default=""):
    """Safely get a secret from Streamlit secrets or environment."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)


def _get_odoo_models_proxy():
    """Create a fresh XML-RPC models proxy (avoids CannotSendRequest on reuse)."""
    url = get_secret("ODOO_URL", "https://wakuli.odoo.com")
    return xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')


@st.cache_data(ttl=APP_CONFIG["cache_ttl_auth"])
def authenticate_odoo():
    """Authenticate with Odoo and return (db, uid, password, url) or Nones."""
    url = get_secret("ODOO_URL", "https://wakuli.odoo.com")
    db = get_secret("ODOO_DB", "wakuli-production-10206791")
    username = get_secret("ODOO_USER", "")
    password = get_secret("ODOO_PASSWORD", "")

    if not username or not password:
        return None, None, None, None

    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        if not uid:
            return None, None, None, None
        return db, uid, password, url
    except Exception:
        return None, None, None, None


# ──────────────────────────────────────────────
# ACCOUNT DISCOVERY (diagnostic tool)
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_chart_of_accounts(db, uid, password):
    """Fetch the full chart of accounts for the retail holding company.

    Returns a DataFrame with columns: code, name, account_type, reconcile.
    Use this to discover what account codes exist before configuring ACCOUNT_MAP.
    """
    if not uid:
        return pd.DataFrame()

    try:
        models = _get_odoo_models_proxy()
        accounts = models.execute_kw(
            db, uid, password, 'account.account', 'search_read',
            [[['company_id', '=', RETAIL_HOLDING_ID]]],
            {'fields': ['code', 'name', 'account_type', 'reconcile'],
             'order': 'code ASC',
             'limit': 5000},
        )
        if not accounts:
            return pd.DataFrame()

        rows = []
        for acc in accounts:
            rows.append({
                'code': acc.get('code', ''),
                'name': acc.get('name', ''),
                'account_type': acc.get('account_type', ''),
                'reconcile': acc.get('reconcile', False),
            })
        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"Error fetching chart of accounts: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_analytic_accounts(db, uid, password):
    """Fetch all analytic accounts (cost centers / stores).

    Returns a DataFrame with columns: id, name, code, plan_id.
    Use this to verify STORE_ODOO_IDS mapping.
    """
    if not uid:
        return pd.DataFrame()

    try:
        models = _get_odoo_models_proxy()
        analytics = models.execute_kw(
            db, uid, password, 'account.analytic.account', 'search_read',
            [[['company_id', '=', RETAIL_HOLDING_ID]]],
            {'fields': ['id', 'name', 'code', 'plan_id'],
             'limit': 500},
        )
        if not analytics:
            return pd.DataFrame()

        rows = []
        for a in analytics:
            plan = a.get('plan_id', [None, ''])
            rows.append({
                'id': a['id'],
                'name': a.get('name', ''),
                'code': a.get('code', ''),
                'plan': plan[1] if isinstance(plan, list) and len(plan) > 1 else '',
            })
        return pd.DataFrame(rows)

    except Exception as e:
        st.error(f"Error fetching analytic accounts: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────
# GENERIC P&L FETCHER
# ──────────────────────────────────────────────

def _build_account_domain(account_codes):
    """Build Odoo domain filter for a list of account code patterns.

    Supports both exact codes ("800000") and prefix patterns ("8%").
    """
    if not account_codes:
        return []

    if len(account_codes) == 1:
        code = account_codes[0]
        if '%' in code:
            return [['account_id.code', '=like', code]]
        else:
            return [['account_id.code', '=', code]]

    # Multiple codes: OR them together
    domain = ['|'] * (len(account_codes) - 1)
    for code in account_codes:
        if '%' in code:
            domain.append(['account_id.code', '=like', code])
        else:
            domain.append(['account_id.code', '=', code])
    return domain


def _build_year_domain(years):
    """Build Odoo domain filter for a list of years."""
    if not years:
        return []

    if len(years) == 1:
        return [
            ['date', '>=', f'{years[0]}-01-01'],
            ['date', '<=', f'{years[0]}-12-31'],
        ]

    domain = ['|'] * (len(years) - 1)
    for y in years:
        domain += ['&', ['date', '>=', f'{y}-01-01'], ['date', '<=', f'{y}-12-31']]
    return domain


def _resolve_store_code(analytic_dist):
    """Resolve a store code from the analytic_distribution dict."""
    if not analytic_dist:
        return "OOH"

    for analytic_id_str, _pct in analytic_dist.items():
        try:
            analytic_id = int(analytic_id_str)
            if analytic_id in ODOO_ID_TO_STORE:
                return ODOO_ID_TO_STORE[analytic_id]
        except (ValueError, TypeError):
            continue
    return "OOH"


def _extract_account_code(account_id_field):
    """Extract the raw account code string from an account_id field.

    account_id comes from Odoo as [id, "code name"] or False.
    """
    if not account_id_field or not isinstance(account_id_field, (list, tuple)):
        return ""
    if len(account_id_field) < 2:
        return ""
    # Format is typically "800000 Coffee Sales" — extract the code part
    name_str = str(account_id_field[1])
    return name_str.split()[0] if name_str else ""


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_pl_data(db, uid, password, section, years_tuple):
    """Generic P&L data fetcher. Queries account.move.line for all account
    codes configured in ACCOUNT_MAP[section] and returns a standardized DataFrame.

    Args:
        db, uid, password: Odoo connection credentials
        section: Key in ACCOUNT_MAP ("revenue", "cogs", "opex", "capex")
        years_tuple: Tuple of years to query (hashable for caching)

    Returns:
        DataFrame with columns:
            date, year, month, amount, description, account_code, account_label,
            cost_category, cost_label, store_code, store_name, move_id, move_name,
            section, group
    """
    if not uid:
        return pd.DataFrame()

    section_config = ACCOUNT_MAP.get(section, {})
    if not section_config:
        return pd.DataFrame()

    # Collect all account codes for this section
    all_codes = []
    for entry in section_config.values():
        all_codes.extend(entry["codes"])

    if not all_codes:
        return pd.DataFrame()

    years = list(years_tuple)

    try:
        models = _get_odoo_models_proxy()

        account_domain = _build_account_domain(all_codes)
        year_domain = _build_year_domain(years)

        domain = [
            ['company_id', '=', RETAIL_HOLDING_ID],
            ['parent_state', '=', 'posted'],
        ] + year_domain + account_domain

        lines = models.execute_kw(
            db, uid, password, 'account.move.line', 'search_read',
            [domain],
            {'fields': ['date', 'debit', 'credit', 'balance', 'name',
                         'account_id', 'analytic_distribution',
                         'move_id', 'move_name'],
             'limit': APP_CONFIG["max_odoo_records"]},
        )

        if not lines:
            return pd.DataFrame()

        data = []
        for line in lines:
            raw_code = _extract_account_code(line.get('account_id'))
            matched_section, cat_key, entry = get_category_for_account_code(raw_code, section)

            if not entry:
                # Account code not in our map — skip
                continue

            # Calculate amount based on sign convention
            sign = entry.get("sign", "abs")
            balance = line.get('balance', 0) or 0
            debit = line.get('debit', 0) or 0
            credit = line.get('credit', 0) or 0

            if sign == "credit":
                amount = credit - debit  # positive for revenue
            elif sign == "debit":
                amount = debit - credit  # positive for expenses
            else:
                amount = abs(balance or (debit - credit))

            if amount == 0:
                continue

            store_code = _resolve_store_code(line.get('analytic_distribution'))

            move_id_field = line.get('move_id', [None, ''])
            move_db_id = move_id_field[0] if move_id_field else None
            move_name = (move_id_field[1] if move_id_field and len(move_id_field) > 1
                         else (line.get('move_name', '') or ''))

            data.append({
                'date': line['date'],
                'year': int(line['date'][:4]),
                'month': line['date'][:7],
                'amount': round(amount, 2),
                'description': line.get('name', '') or '',
                'account_code': raw_code,
                'account_label': entry["label"],
                'cost_category': cat_key,
                'cost_label': entry["label"],
                'store_code': store_code,
                'store_name': STORE_LOCATIONS.get(store_code, {}).get('name', store_code),
                'move_id': move_db_id,
                'move_name': move_name,
                'section': matched_section,
                'group': entry.get("group", section),
            })

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Error fetching {section} data from Odoo: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_revenue_data(db, uid, password, years_tuple):
    """Fetch revenue data from Odoo and format for the dashboard.

    Returns a DataFrame matching the format expected by kpi_engine:
        year, month, store_code, store_name, category, category_label,
        channel, revenue
    """
    raw = fetch_pl_data(db, uid, password, "revenue", years_tuple)
    if raw.empty:
        return pd.DataFrame()

    # Map cost_category (ACCOUNT_MAP key) to product category
    raw['category'] = raw['cost_category'].map(REVENUE_TO_PRODUCT_CATEGORY).fillna('coffee')
    raw['category_label'] = raw['category'].map(
        lambda c: PRODUCT_CATEGORIES.get(c, {}).get('label', c)
    )
    # Channel is not available from accounting data — mark as "all"
    raw['channel'] = 'all'

    result = raw.rename(columns={'amount': 'revenue'})
    return result[['year', 'month', 'store_code', 'store_name',
                    'category', 'category_label', 'channel', 'revenue',
                    'cost_category', 'account_code', 'account_label',
                    'description', 'move_id', 'move_name']]


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_cost_data(db, uid, password, years_tuple):
    """Fetch COGS + OpEx data from Odoo and merge into a unified cost DataFrame.

    Returns a DataFrame matching the format expected by kpi_engine:
        year, month, store_code, store_name, cost_category, cost_label, amount
    """
    cogs_df = fetch_pl_data(db, uid, password, "cogs", years_tuple)
    opex_df = fetch_pl_data(db, uid, password, "opex", years_tuple)

    frames = [df for df in [cogs_df, opex_df] if not df.empty]
    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return combined[['year', 'month', 'store_code', 'store_name',
                      'cost_category', 'cost_label', 'amount',
                      'account_code', 'account_label', 'group',
                      'description', 'move_id', 'move_name']]


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_capex_actuals(db, uid, password, account_codes_tuple, years_tuple):
    """Fetch CAPEX data (backward-compatible with original function).

    Uses the generic fetcher but filters to only the requested CAPEX account codes.
    """
    full_capex = fetch_pl_data(db, uid, password, "capex", years_tuple)
    if full_capex.empty:
        return pd.DataFrame()

    # Filter to requested account codes
    requested = set(account_codes_tuple)
    mask = full_capex['account_code'].apply(
        lambda c: any(c.startswith(r.rstrip('%')) for r in requested)
    )
    return full_capex[mask]


# ──────────────────────────────────────────────
# OPTIONAL: POS DATA (if Odoo POS module installed)
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_pos_orders(db, uid, password, years_tuple):
    """Fetch POS order data for customer/transaction metrics.

    Only works if Odoo POS module is installed (ODOO_MODULES["pos"] = True).
    Returns a DataFrame with order-level data including timestamps for daypart.
    """
    if not uid or not ODOO_MODULES.get("pos"):
        return pd.DataFrame()

    years = list(years_tuple)

    try:
        models = _get_odoo_models_proxy()
        year_domain = _build_year_domain(years)

        # Replace date filter with date_order for POS
        pos_year_domain = []
        for item in year_domain:
            if isinstance(item, list) and item[0] == 'date':
                pos_year_domain.append(['date_order', item[1], item[2]])
            else:
                pos_year_domain.append(item)

        domain = [
            ['company_id', '=', RETAIL_HOLDING_ID],
            ['state', 'in', ['paid', 'done', 'invoiced']],
        ] + pos_year_domain

        orders = models.execute_kw(
            db, uid, password, 'pos.order', 'search_read',
            [domain],
            {'fields': ['date_order', 'amount_total', 'amount_tax',
                         'partner_id', 'session_id', 'config_id',
                         'lines', 'pos_reference'],
             'limit': APP_CONFIG["max_odoo_records"]},
        )

        if not orders:
            return pd.DataFrame()

        rows = []
        for order in orders:
            date_str = order.get('date_order', '')
            # date_order is datetime string "2025-01-15 09:23:45"
            date_only = date_str[:10] if date_str else ''
            hour = int(date_str[11:13]) if len(date_str) > 13 else 12

            # Determine daypart from hour
            if hour < 9:
                daypart = 'early_morning'
            elif hour < 12:
                daypart = 'morning'
            elif hour < 15:
                daypart = 'afternoon'
            elif hour < 18:
                daypart = 'late_afternoon'
            else:
                daypart = 'evening'

            # Try to resolve store from config_id (POS config = store)
            config = order.get('config_id', [None, ''])
            config_name = config[1] if isinstance(config, list) and len(config) > 1 else ''

            partner = order.get('partner_id')
            has_partner = bool(partner and partner[0]) if isinstance(partner, (list, tuple)) else bool(partner)

            rows.append({
                'date': date_only,
                'year': int(date_only[:4]) if date_only else 0,
                'month': date_only[:7] if date_only else '',
                'hour': hour,
                'daypart': daypart,
                'amount_total': order.get('amount_total', 0),
                'amount_tax': order.get('amount_tax', 0),
                'has_partner': has_partner,
                'partner_id': partner[0] if has_partner and isinstance(partner, (list, tuple)) else None,
                'pos_config': config_name,
                'order_ref': order.get('pos_reference', ''),
            })

        return pd.DataFrame(rows)

    except Exception as e:
        st.warning(f"POS data not available: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────
# OPTIONAL: HR DATA (if Odoo HR module installed)
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_employees(db, uid, password):
    """Fetch employee headcount data.

    Only works if Odoo HR module is installed (ODOO_MODULES["hr"] = True).
    """
    if not uid or not ODOO_MODULES.get("hr"):
        return pd.DataFrame()

    try:
        models = _get_odoo_models_proxy()
        employees = models.execute_kw(
            db, uid, password, 'hr.employee', 'search_read',
            [[['company_id', '=', RETAIL_HOLDING_ID],
              ['active', '=', True]]],
            {'fields': ['name', 'department_id', 'job_title',
                         'work_location_id', 'resource_calendar_id'],
             'limit': 500},
        )

        if not employees:
            return pd.DataFrame()

        rows = []
        for emp in employees:
            dept = emp.get('department_id', [None, ''])
            loc = emp.get('work_location_id', [None, ''])
            rows.append({
                'name': emp.get('name', ''),
                'department': dept[1] if isinstance(dept, list) and len(dept) > 1 else '',
                'job_title': emp.get('job_title', ''),
                'work_location': loc[1] if isinstance(loc, list) and len(loc) > 1 else '',
            })
        return pd.DataFrame(rows)

    except Exception as e:
        st.warning(f"HR data not available: {e}")
        return pd.DataFrame()


# ──────────────────────────────────────────────
# INVOICE DETAIL VIEWER
# ──────────────────────────────────────────────

@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_invoice_details(db, uid, password, move_id):
    """Fetch full invoice / journal entry details for a given move_id."""
    if not uid or not move_id:
        return None, []

    try:
        models = _get_odoo_models_proxy()

        moves = models.execute_kw(
            db, uid, password, 'account.move', 'search_read',
            [[['id', '=', move_id]]],
            {'fields': ['name', 'date', 'ref', 'partner_id', 'state',
                         'amount_total', 'move_type', 'invoice_date',
                         'invoice_date_due', 'narration'],
             'limit': 1},
        )
        move = moves[0] if moves else None

        lines = models.execute_kw(
            db, uid, password, 'account.move.line', 'search_read',
            [[['move_id', '=', move_id]]],
            {'fields': ['name', 'account_id', 'debit', 'credit', 'balance',
                         'analytic_distribution', 'date', 'quantity',
                         'price_unit', 'product_id'],
             'limit': 200},
        )

        return move, lines

    except Exception as e:
        st.error(f"Error fetching invoice details: {e}")
        return None, []


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_invoice_pdf(db, uid, password, move_id):
    """Fetch the PDF attachment for an invoice/move."""
    if not uid or not move_id:
        return None

    try:
        models = _get_odoo_models_proxy()
        attachments = models.execute_kw(
            db, uid, password, 'ir.attachment', 'search_read',
            [[['res_model', '=', 'account.move'],
              ['res_id', '=', move_id],
              ['mimetype', '=like', '%pdf%']]],
            {'fields': ['name', 'datas', 'mimetype'], 'limit': 1},
        )
        return attachments[0] if attachments else None
    except Exception:
        return None


# ──────────────────────────────────────────────
# DATA QUALITY CHECK
# ──────────────────────────────────────────────

def check_data_availability(db, uid, password, years_tuple):
    """Check which ACCOUNT_MAP sections have actual data in Odoo.

    Returns a dict: {section: {"configured": bool, "has_data": bool, "row_count": int}}
    """
    results = {}
    for section in ACCOUNT_MAP:
        codes = []
        for entry in ACCOUNT_MAP[section].values():
            codes.extend(entry["codes"])

        configured = len(codes) > 0
        has_data = False
        row_count = 0

        if configured and uid:
            try:
                models = _get_odoo_models_proxy()
                account_domain = _build_account_domain(codes)
                year_domain = _build_year_domain(list(years_tuple))
                domain = [
                    ['company_id', '=', RETAIL_HOLDING_ID],
                    ['parent_state', '=', 'posted'],
                ] + year_domain + account_domain

                row_count = models.execute_kw(
                    db, uid, password, 'account.move.line', 'search_count',
                    [domain],
                )
                has_data = row_count > 0
            except Exception:
                pass

        results[section] = {
            "configured": configured,
            "has_data": has_data,
            "row_count": row_count,
        }

    return results
