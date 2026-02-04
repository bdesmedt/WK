"""
Wakuli Retail Analytics - Odoo Connector
==========================================
Handles all Odoo XML-RPC API communication for fetching financial data.
Supports CAPEX actuals, invoice details, and PDF attachments.
"""

import streamlit as st
import pandas as pd
import xmlrpc.client
import os
from config import (
    RETAIL_HOLDING_ID, ODOO_ID_TO_STORE, STORE_LOCATIONS,
    CAPEX_ACCOUNTS, APP_CONFIG,
)


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


@st.cache_data(ttl=APP_CONFIG["cache_ttl_data"])
def fetch_capex_actuals(db, uid, password, account_codes_tuple, years_tuple):
    """Fetch actual CAPEX bookings from Odoo journal items.

    Odoo 18 compatible: filters on account.move.line with account code pattern.
    """
    if not uid:
        return pd.DataFrame()

    account_codes = list(account_codes_tuple)
    years = list(years_tuple)

    try:
        models = _get_odoo_models_proxy()

        # Build account domain with OR operators
        account_domain = ['|'] * (len(account_codes) - 1) if len(account_codes) > 1 else []
        for code in account_codes:
            account_domain.append(['account_id.code', '=like', f'{code}%'])

        # Build year domain
        if len(years) == 1:
            year_domain = [
                ['date', '>=', f'{years[0]}-01-01'],
                ['date', '<=', f'{years[0]}-12-31'],
            ]
        else:
            year_domain = ['|'] * (len(years) - 1)
            for y in years:
                year_domain += ['&', ['date', '>=', f'{y}-01-01'], ['date', '<=', f'{y}-12-31']]

        domain = [
            ['company_id', '=', RETAIL_HOLDING_ID],
            ['parent_state', '=', 'posted'],
        ] + year_domain + account_domain

        lines = models.execute_kw(
            db, uid, password, 'account.move.line', 'search_read',
            [domain],
            {'fields': ['date', 'debit', 'credit', 'balance', 'name', 'account_id',
                        'analytic_distribution', 'move_id', 'move_name'],
             'limit': APP_CONFIG["max_odoo_records"]},
        )

        if not lines:
            return pd.DataFrame()

        data = []
        for line in lines:
            store_code = "OOH"
            analytic_dist = line.get('analytic_distribution') or {}
            if analytic_dist:
                for analytic_id_str, _pct in analytic_dist.items():
                    try:
                        analytic_id = int(analytic_id_str)
                        if analytic_id in ODOO_ID_TO_STORE:
                            store_code = ODOO_ID_TO_STORE[analytic_id]
                            break
                    except (ValueError, TypeError):
                        continue

            account_code = "Unknown"
            account_label = "Unknown"
            if line.get('account_id'):
                account_name = line['account_id'][1] if len(line['account_id']) > 1 else ""
                account_code = account_name.split()[0] if account_name else "Unknown"
                account_label = CAPEX_ACCOUNTS.get(account_code, account_name)

            amount = abs(line.get('balance', 0) or (line.get('debit', 0) - line.get('credit', 0)))

            move_id_field = line.get('move_id', [None, ''])
            move_db_id = move_id_field[0] if move_id_field else None
            move_name = move_id_field[1] if move_id_field and len(move_id_field) > 1 else (line.get('move_name', '') or '')

            if amount > 0:
                data.append({
                    'date': line['date'],
                    'year': int(line['date'][:4]),
                    'month': line['date'][:7],
                    'amount': amount,
                    'description': line.get('name', '') or '',
                    'account': account_code,
                    'account_label': account_label,
                    'store_code': store_code,
                    'store_name': STORE_LOCATIONS.get(store_code, {}).get('name', store_code),
                    'move_id': move_db_id,
                    'move_name': move_name,
                })

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Error fetching CAPEX data: {e}")
        return pd.DataFrame()


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
