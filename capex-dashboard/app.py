"""
Wakuli CAPEX Budget Dashboard
============================
Track construction budgets vs actuals for Wakuli stores.
Compatible with Odoo 18.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import xmlrpc.client
from datetime import datetime, date
import json
import os
import base64
import streamlit.components.v1 as components

# Page config
st.set_page_config(
    page_title="Wakuli CAPEX Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E4A3F;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2E4A3F;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .store-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    .invoice-modal {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Store locations mapping (from wakuli.com)
STORE_LOCATIONS = {
    "LIN": {"name": "Linnaeusstraat", "address": "Linnaeusstraat 237a", "city": "Amsterdam", "lat": 52.3579, "lon": 4.9274},
    "JPH": {"name": "Jan Pieter Heijestraat", "address": "Jan Pieter Heijestraat 76", "city": "Amsterdam", "lat": 52.3627, "lon": 4.8583},
    "HAP": {"name": "Haarlemmerplein", "address": "Haarlemmerplein 43", "city": "Amsterdam", "lat": 52.3847, "lon": 4.8819},
    "WAG": {"name": "Wagenaarstraat", "address": "Wagenaarstraat 70H", "city": "Amsterdam", "lat": 52.3615, "lon": 4.9285},
    "AMS": {"name": "Amstelveenseweg", "address": "Amstelveenseweg 210", "city": "Amsterdam", "lat": 52.3489, "lon": 4.8658},
    "VIJZ": {"name": "Vijzelgracht", "address": "Vijzelgracht 37H", "city": "Amsterdam", "lat": 52.3630, "lon": 4.8908},
    "TWIJN": {"name": "Twijnstraat", "address": "Twijnstraat 1", "city": "Utrecht", "lat": 52.0894, "lon": 5.1180},
    "ZIEK": {"name": "Ziekerstraat", "address": "Ziekerstraat 169", "city": "Nijmegen", "lat": 51.8463, "lon": 5.8642},
    "WOU": {"name": "Van Woustraat", "address": "Van Woustraat 54", "city": "Amsterdam", "lat": 52.3530, "lon": 4.9040},
    "NOB": {"name": "Nobelstraat", "address": "Nobelstraat 143", "city": "Utrecht", "lat": 52.0907, "lon": 5.1230},
    "JAC": {"name": "Jacob van Campenstraat", "address": "Tweede Jacob van Campenstraat 1", "city": "Amsterdam", "lat": 52.3505, "lon": 4.8925},
    "BAJES": {"name": "Bajes", "address": "H.J.E. Wenckebachweg 48", "city": "Amsterdam", "lat": 52.3456, "lon": 4.9356},
    "FAH": {"name": "Fahrenheitstraat", "address": "Fahrenheitstraat 496", "city": "Den Haag", "lat": 52.0705, "lon": 4.2805},
    "MEENT": {"name": "Meent", "address": "Meent 3A", "city": "Rotterdam", "lat": 51.9225, "lon": 4.4792},
    "LUST": {"name": "Lusthofstraat", "address": "Lusthofstraat 54B", "city": "Rotterdam", "lat": 51.9178, "lon": 4.4935},
    "VIS": {"name": "Visstraat", "address": "Visstraat 4", "city": "Den Bosch", "lat": 51.6878, "lon": 5.3069},
    "THER": {"name": "Theresiastraat", "address": "Theresiastraat 108", "city": "Den Haag", "lat": 52.0763, "lon": 4.3015},
    "PIET": {"name": "Piet Heinstraat", "address": "Piet Heinstraat 84", "city": "Den Haag", "lat": 52.0716, "lon": 4.3132},
    "HAS": {"name": "Haarlemmerstraat", "address": "Haarlemmerstraat 127", "city": "Leiden", "lat": 52.1601, "lon": 4.4894},
    "STOEL": {"name": "Stoeldraaierstraat", "address": "Stoeldraaierstraat 70", "city": "Groningen", "lat": 53.2171, "lon": 6.5613},
    "OOH": {"name": "Overhead (All Stores)", "address": "Central Office", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041},
}

# Odoo store analytics IDs mapping
STORE_ODOO_IDS = {
    "LIN": 17046, "JPH": 17047, "HAP": 17048, "WAG": 17049, "AMS": 17050,
    "VIJZ": 17051, "TWIJN": 17052, "ZIEK": 17053, "WOU": 17054, "NOB": 17055,
    "JAC": 22869, "BAJES": 28826, "FAH": 18393, "MEENT": 53942, "LUST": 51003,
    "VIS": 58577, "THER": 58498, "PIET": 58578, "HAS": 58596, "STOEL": 58603,
    "OOH": 19878
}

# Reverse mapping: Odoo ID -> Store Code
ODOO_ID_TO_STORE = {v: k for k, v in STORE_ODOO_IDS.items()}

# Asset accounts for CAPEX tracking
CAPEX_ACCOUNTS = {
    "037000": "CAPEX Winkels (Store Renovations)",
    "032000": "WIA - Assets Under Construction",
    "031000": "Bedrijfsinventaris (Business Inventory)",
    "021000": "Koffiemachines (Coffee Machines)",
    "013000": "Verbouwingen (Renovations)"
}

# Wakuli Retail Holding company ID
RETAIL_HOLDING_ID = 2


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


@st.cache_data(ttl=600)
def authenticate_odoo():
    """Authenticate with Odoo and return uid. Cached separately from proxies."""
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


@st.cache_data(ttl=300)
def fetch_capex_actuals(db, uid, password, account_codes_tuple, years_tuple):
    """Fetch actual CAPEX bookings from Odoo using journal items.

    Odoo 18 compatible: filters on account.move.line with account code pattern.
    Creates a fresh XML-RPC proxy per call to avoid CannotSendRequest errors.
    """
    if not uid:
        return pd.DataFrame()

    account_codes = list(account_codes_tuple)
    years = list(years_tuple)

    try:
        models = _get_odoo_models_proxy()

        # Build account domain
        account_domain = ['|'] * (len(account_codes) - 1) if len(account_codes) > 1 else []
        for code in account_codes:
            account_domain.append(['account_id.code', '=like', f'{code}%'])

        # Build year domain for multiple years
        if len(years) == 1:
            year_domain = [
                ['date', '>=', f'{years[0]}-01-01'],
                ['date', '<=', f'{years[0]}-12-31'],
            ]
        else:
            # OR across years
            year_domain = ['|'] * (len(years) - 1)
            for y in years:
                year_domain += [
                    '&',
                    ['date', '>=', f'{y}-01-01'],
                    ['date', '<=', f'{y}-12-31'],
                ]

        domain = [
            ['company_id', '=', RETAIL_HOLDING_ID],
            ['parent_state', '=', 'posted']
        ] + year_domain + account_domain

        lines = models.execute_kw(db, uid, password, 'account.move.line', 'search_read',
            [domain],
            {'fields': ['date', 'debit', 'credit', 'balance', 'name', 'account_id',
                        'analytic_distribution', 'move_id', 'move_name'],
             'limit': 10000})

        if not lines:
            return pd.DataFrame()

        # Process data
        data = []
        for line in lines:
            # Parse analytic distribution to find store
            store_code = "OOH"  # Default to overhead
            analytic_dist = line.get('analytic_distribution') or {}

            if analytic_dist:
                for analytic_id_str, percentage in analytic_dist.items():
                    try:
                        analytic_id = int(analytic_id_str)
                        if analytic_id in ODOO_ID_TO_STORE:
                            store_code = ODOO_ID_TO_STORE[analytic_id]
                            break
                    except (ValueError, TypeError):
                        continue

            # Get account code from the account_id tuple [id, name]
            account_code = "Unknown"
            account_label = "Unknown"
            if line.get('account_id'):
                account_name = line['account_id'][1] if len(line['account_id']) > 1 else ""
                account_code = account_name.split()[0] if account_name else "Unknown"
                account_label = CAPEX_ACCOUNTS.get(account_code, account_name)

            # Use absolute value of balance (negative = cost)
            amount = abs(line.get('balance', 0) or (line.get('debit', 0) - line.get('credit', 0)))

            # move_id is [id, name] tuple
            move_id = line.get('move_id', [None, ''])
            move_db_id = move_id[0] if move_id else None
            move_name = move_id[1] if move_id and len(move_id) > 1 else (line.get('move_name', '') or '')

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
        st.error(f"Error fetching data: {e}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_invoice_details(db, uid, password, move_id):
    """Fetch full invoice / journal entry details for a given move_id."""
    if not uid or not move_id:
        return None, []

    try:
        models = _get_odoo_models_proxy()

        # Fetch the move header
        moves = models.execute_kw(db, uid, password, 'account.move', 'search_read',
            [[['id', '=', move_id]]],
            {'fields': ['name', 'date', 'ref', 'partner_id', 'state',
                        'amount_total', 'move_type', 'invoice_date',
                        'invoice_date_due', 'narration'],
             'limit': 1})

        move = moves[0] if moves else None

        # Fetch all lines for this move
        lines = models.execute_kw(db, uid, password, 'account.move.line', 'search_read',
            [[['move_id', '=', move_id]]],
            {'fields': ['name', 'account_id', 'debit', 'credit', 'balance',
                        'analytic_distribution', 'date', 'quantity',
                        'price_unit', 'product_id'],
             'limit': 200})

        return move, lines

    except Exception as e:
        st.error(f"Error fetching invoice details: {e}")
        return None, []


@st.cache_data(ttl=300)
def fetch_invoice_pdf(db, uid, password, move_id):
    """Fetch the PDF attachment for an invoice/move."""
    if not uid or not move_id:
        return None

    try:
        models = _get_odoo_models_proxy()

        # Search for PDF attachments linked to this move
        attachments = models.execute_kw(db, uid, password, 'ir.attachment', 'search_read',
            [[['res_model', '=', 'account.move'],
              ['res_id', '=', move_id],
              ['mimetype', '=like', '%pdf%']]],
            {'fields': ['name', 'datas', 'mimetype'],
             'limit': 1})

        if attachments:
            return attachments[0]
        return None
    except Exception:
        return None


def load_budgets():
    """Load budgets from session state."""
    if 'budgets' not in st.session_state:
        st.session_state.budgets = {}
    return st.session_state.budgets


def save_budgets(budgets):
    """Save budgets to session state."""
    st.session_state.budgets = budgets


def render_invoice_popup(db, uid, password, move_id, move_name):
    """Render invoice detail view inside an expander (acts as popup)."""
    move, lines = fetch_invoice_details(db, uid, password, move_id)

    if not move:
        st.warning("Could not load invoice details.")
        return

    # Header info
    cols = st.columns([2, 1, 1, 1])
    with cols[0]:
        st.markdown(f"**Invoice/Entry:** {move.get('name', 'N/A')}")
        partner = move.get('partner_id')
        if partner:
            st.markdown(f"**Partner:** {partner[1] if isinstance(partner, list) else partner}")
    with cols[1]:
        st.markdown(f"**Date:** {move.get('date', 'N/A')}")
        st.markdown(f"**Due:** {move.get('invoice_date_due', 'N/A')}")
    with cols[2]:
        st.markdown(f"**State:** {move.get('state', 'N/A')}")
        move_type = move.get('move_type', '')
        type_labels = {
            'out_invoice': 'Customer Invoice',
            'in_invoice': 'Vendor Bill',
            'out_refund': 'Credit Note',
            'in_refund': 'Vendor Credit',
            'entry': 'Journal Entry',
        }
        st.markdown(f"**Type:** {type_labels.get(move_type, move_type)}")
    with cols[3]:
        total = move.get('amount_total', 0)
        st.metric("Total", f"\u20ac{total:,.2f}")

    ref = move.get('ref', '')
    if ref:
        st.markdown(f"**Reference:** {ref}")

    narration = move.get('narration', '')
    if narration and narration.strip():
        st.markdown(f"**Notes:** {narration}")

    # Lines table
    if lines:
        line_data = []
        for l in lines:
            acc = l.get('account_id', [None, ''])
            acc_name = acc[1] if isinstance(acc, list) and len(acc) > 1 else str(acc)
            prod = l.get('product_id', [None, ''])
            prod_name = prod[1] if isinstance(prod, list) and len(prod) > 1 else ''
            line_data.append({
                'Account': acc_name,
                'Description': l.get('name', ''),
                'Product': prod_name,
                'Qty': l.get('quantity', 0),
                'Unit Price': l.get('price_unit', 0),
                'Debit': l.get('debit', 0),
                'Credit': l.get('credit', 0),
            })
        line_df = pd.DataFrame(line_data)
        st.dataframe(line_df, use_container_width=True, hide_index=True,
                      column_config={
                          'Debit': st.column_config.NumberColumn(format='\u20ac%.2f'),
                          'Credit': st.column_config.NumberColumn(format='\u20ac%.2f'),
                          'Unit Price': st.column_config.NumberColumn(format='\u20ac%.2f'),
                      })

    # PDF attachment
    pdf_data = fetch_invoice_pdf(db, uid, password, move_id)
    if pdf_data and pdf_data.get('datas'):
        st.divider()
        st.markdown(f"**Attachment:** {pdf_data.get('name', 'document.pdf')}")
        pdf_bytes = base64.b64decode(pdf_data['datas'])
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=pdf_data.get('name', 'invoice.pdf'),
            mime='application/pdf',
            key=f"pdf_dl_{move_id}"
        )
        # Embed PDF viewer using blob URL (data: URIs are blocked by most browsers)
        b64 = pdf_data['datas']
        pdf_html = f"""
        <iframe id="pdfViewer" width="100%" height="580" style="border:none;"></iframe>
        <script>
            const b64 = "{b64}";
            const byteChars = atob(b64);
            const byteNums = new Uint8Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) {{
                byteNums[i] = byteChars.charCodeAt(i);
            }}
            const blob = new Blob([byteNums], {{type: 'application/pdf'}});
            const url = URL.createObjectURL(blob);
            document.getElementById('pdfViewer').src = url;
        </script>
        """
        components.html(pdf_html, height=600)


def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<p class="main-header">☕ Wakuli CAPEX Dashboard</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Track construction budgets vs actuals for store renovations</p>', unsafe_allow_html=True)
    with col2:
        st.image("https://www.wakuli.com/cdn/shop/files/logo_green.png?v=1719823287&width=200", width=120)

    st.divider()

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        # Year selection - multi-select
        current_year = datetime.now().year
        year_options = list(range(current_year - 5, current_year + 2))
        selected_years = st.multiselect(
            "Years",
            options=year_options,
            default=[current_year],
            help="Select one or more years (CAPEX investments span multiple years)"
        )
        if not selected_years:
            selected_years = [current_year]

        # Account selection
        st.subheader("Accounts to Track")
        selected_accounts = []
        for code, name in CAPEX_ACCOUNTS.items():
            if st.checkbox(name, value=(code == "037000"), key=f"acc_{code}"):
                selected_accounts.append(code)

        if not selected_accounts:
            selected_accounts = ["037000"]

        st.divider()

        # Store filter
        st.subheader("Store Filter")
        store_options = ["All Stores"] + [f"{code} - {info['name']}" for code, info in STORE_LOCATIONS.items() if code != "OOH"]
        selected_stores = st.multiselect("Select stores", options=store_options, default=["All Stores"])

        if "All Stores" in selected_stores:
            store_filter = list(STORE_LOCATIONS.keys())
        else:
            store_filter = [s.split(" - ")[0] for s in selected_stores]

        # Connection status
        st.divider()
        st.subheader("Connection")
        odoo_user = get_secret("ODOO_USER", "")
        if odoo_user:
            st.success(f"User: {odoo_user[:20]}...")
        else:
            st.warning("Not configured")

    # Check Odoo connection
    auth = authenticate_odoo()
    db, uid, password, odoo_url = auth

    has_odoo = db is not None and uid is not None

    if not has_odoo:
        st.warning("Odoo credentials not configured or authentication failed.")

        with st.expander("How to configure Odoo connection"):
            st.markdown("""
            ### In Streamlit Cloud:
            1. Go to your app > Settings > Secrets
            2. Add these secrets:

            ```toml
            ODOO_URL = "https://wakuli.odoo.com"
            ODOO_DB = "wakuli-production-10206791"
            ODOO_USER = "your.email@company.com"
            ODOO_PASSWORD = "your-api-key-here"
            ```

            ### How to get an API key:
            1. Login to Odoo
            2. Click your profile > My Profile
            3. Go to Account Security tab
            4. Click "New API Key"
            5. Copy the key (shown only once!)
            """)

        st.info("Using demo data for preview...")

        # Demo data across multiple years
        demo_data = {
            'date': ['2024-06-15', '2024-09-20', '2025-01-15', '2025-02-20', '2025-03-10',
                     '2025-04-05', '2025-05-12', '2025-06-08', '2025-07-15', '2025-08-22'],
            'year': [2024, 2024, 2025, 2025, 2025, 2025, 2025, 2025, 2025, 2025],
            'month': ['2024-06', '2024-09', '2025-01', '2025-02', '2025-03',
                      '2025-04', '2025-05', '2025-06', '2025-07', '2025-08'],
            'amount': [12000, 9500, 15000, 8500, 22000, 5000, 18000, 12000, 7500, 14000],
            'description': ['Equipment LIN', 'Renovation JPH', 'Renovation HAS', 'Equipment VIS',
                           'Construction THER', 'Repairs PIET', 'Renovation STOEL', 'Equipment MEENT',
                           'Coffee machines WAG', 'Renovation FAH'],
            'account': ['021000', '037000', '037000', '031000', '037000',
                       '013000', '037000', '021000', '021000', '037000'],
            'account_label': ['Koffiemachines (Coffee Machines)', 'CAPEX Winkels (Store Renovations)',
                             'CAPEX Winkels (Store Renovations)', 'Bedrijfsinventaris (Business Inventory)',
                             'CAPEX Winkels (Store Renovations)', 'Verbouwingen (Renovations)',
                             'CAPEX Winkels (Store Renovations)', 'Koffiemachines (Coffee Machines)',
                             'Koffiemachines (Coffee Machines)', 'CAPEX Winkels (Store Renovations)'],
            'store_code': ['LIN', 'JPH', 'HAS', 'VIS', 'THER', 'PIET', 'STOEL', 'MEENT', 'WAG', 'FAH'],
            'store_name': ['Linnaeusstraat', 'Jan Pieter Heijestraat', 'Haarlemmerstraat', 'Visstraat',
                          'Theresiastraat', 'Piet Heinstraat', 'Stoeldraaierstraat', 'Meent',
                          'Wagenaarstraat', 'Fahrenheitstraat'],
            'move_id': [None]*10,
            'move_name': ['']*10,
        }
        actuals_df = pd.DataFrame(demo_data)
    else:
        st.success(f"Connected to Odoo (User ID: {uid})")
        actuals_df = fetch_capex_actuals(db, uid, password, tuple(selected_accounts), tuple(selected_years))

    # Load budgets - budget key is NOT per year, it's total CAPEX budget
    budgets = load_budgets()
    budget_key = f"capex_{'-'.join(sorted(selected_accounts))}"

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Dashboard", "Graphs & Trends", "Variance Analysis",
        "Budget Management", "Store Map", "Detailed Data"
    ])

    # ==========================================
    # TAB 1: DASHBOARD
    # ==========================================
    with tab1:
        if actuals_df.empty:
            st.info("No data available for the selected criteria.")
        else:
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)]

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            total_actual = filtered_df['amount'].sum()
            total_budget = sum(budgets.get(budget_key, {}).get(store, 0) for store in store_filter)
            variance = total_budget - total_actual
            variance_pct = (variance / total_budget * 100) if total_budget > 0 else 0

            with col1:
                st.metric("Total CAPEX Budget", f"\u20ac{total_budget:,.0f}")
            with col2:
                st.metric("Total Actual", f"\u20ac{total_actual:,.0f}")
            with col3:
                st.metric("Variance", f"\u20ac{variance:,.0f}",
                         delta=f"{variance_pct:+.1f}%",
                         delta_color="normal" if variance >= 0 else "inverse")
            with col4:
                num_stores = filtered_df['store_code'].nunique()
                st.metric("Active Stores", num_stores)

            st.divider()

            # Charts row
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("CAPEX per Store")
                store_summary = filtered_df.groupby(['store_code', 'store_name'])['amount'].sum().reset_index()
                store_summary = store_summary.sort_values('amount', ascending=True)

                fig = px.bar(store_summary, x='amount', y='store_name', orientation='h',
                            color='amount', color_continuous_scale='Greens',
                            labels={'amount': 'Amount (\u20ac)', 'store_name': 'Store'})
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Monthly Trend")
                monthly = filtered_df.groupby('month')['amount'].sum().reset_index()
                monthly = monthly.sort_values('month')

                fig = px.area(monthly, x='month', y='amount',
                             labels={'amount': 'Amount (\u20ac)', 'month': 'Month'},
                             color_discrete_sequence=['#2E4A3F'])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            # Budget vs Actual comparison
            st.subheader("Budget vs Actual by Store")

            comparison_data = []
            for store_code in store_filter:
                if store_code in STORE_LOCATIONS:
                    actual = filtered_df[filtered_df['store_code'] == store_code]['amount'].sum()
                    budget = budgets.get(budget_key, {}).get(store_code, 0)
                    comparison_data.append({
                        'Store': STORE_LOCATIONS[store_code]['name'],
                        'Code': store_code,
                        'Budget': budget,
                        'Actual': actual,
                        'Variance': budget - actual,
                        'Variance %': ((budget - actual) / budget * 100) if budget > 0 else 0
                    })

            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df[comparison_df['Actual'] > 0].sort_values('Actual', ascending=False)

            if not comparison_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(name='Budget', x=comparison_df['Store'], y=comparison_df['Budget'],
                                    marker_color='lightgray'))
                fig.add_trace(go.Bar(name='Actual', x=comparison_df['Store'], y=comparison_df['Actual'],
                                    marker_color='#2E4A3F'))
                fig.update_layout(barmode='group', height=400)
                st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # TAB 2: GRAPHS & TRENDS (with account breakdown)
    # ==========================================
    with tab2:
        if actuals_df.empty:
            st.info("No data available for the selected criteria.")
        else:
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)]

            st.subheader("Spending by Account Category")
            account_summary = filtered_df.groupby(['account', 'account_label'])['amount'].sum().reset_index()
            account_summary = account_summary.sort_values('amount', ascending=False)

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(account_summary, values='amount', names='account_label',
                            color_discrete_sequence=px.colors.sequential.Greens_r,
                            hole=0.4)
                fig.update_layout(height=400, title="Account Distribution")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(account_summary, x='account_label', y='amount',
                            color='account_label',
                            color_discrete_sequence=px.colors.sequential.Greens_r,
                            labels={'amount': 'Amount (\u20ac)', 'account_label': 'Account'})
                fig.update_layout(height=400, showlegend=False, title="Total per Account",
                                 xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Monthly trend per account
            st.subheader("Monthly Trend by Account")
            monthly_acc = filtered_df.groupby(['month', 'account_label'])['amount'].sum().reset_index()
            monthly_acc = monthly_acc.sort_values('month')

            fig = px.bar(monthly_acc, x='month', y='amount', color='account_label',
                        labels={'amount': 'Amount (\u20ac)', 'month': 'Month', 'account_label': 'Account'},
                        color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=450, barmode='stack')
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Account trend per store
            st.subheader("Account Breakdown per Store")
            store_acc = filtered_df.groupby(['store_name', 'account_label'])['amount'].sum().reset_index()
            store_acc = store_acc.sort_values('amount', ascending=False)

            fig = px.bar(store_acc, x='store_name', y='amount', color='account_label',
                        labels={'amount': 'Amount (\u20ac)', 'store_name': 'Store', 'account_label': 'Account'},
                        color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=450, barmode='stack', xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Year-over-year comparison if multiple years
            if len(selected_years) > 1 and 'year' in filtered_df.columns:
                st.subheader("Year-over-Year Comparison")

                col1, col2 = st.columns(2)
                with col1:
                    yearly = filtered_df.groupby('year')['amount'].sum().reset_index()
                    fig = px.bar(yearly, x='year', y='amount',
                                labels={'amount': 'Amount (\u20ac)', 'year': 'Year'},
                                color_discrete_sequence=['#2E4A3F'],
                                text_auto=True)
                    fig.update_layout(height=350, title="Total CAPEX per Year")
                    fig.update_xaxes(dtick=1)
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    yearly_store = filtered_df.groupby(['year', 'store_name'])['amount'].sum().reset_index()
                    fig = px.bar(yearly_store, x='year', y='amount', color='store_name',
                                labels={'amount': 'Amount (\u20ac)', 'year': 'Year', 'store_name': 'Store'},
                                color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_layout(height=350, barmode='stack', title="CAPEX per Store per Year")
                    fig.update_xaxes(dtick=1)
                    st.plotly_chart(fig, use_container_width=True)

            # Cumulative spend over time
            st.subheader("Cumulative CAPEX Spend")
            cumulative = filtered_df.groupby('month')['amount'].sum().reset_index()
            cumulative = cumulative.sort_values('month')
            cumulative['cumulative'] = cumulative['amount'].cumsum()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cumulative['month'], y=cumulative['cumulative'],
                                     mode='lines+markers', name='Cumulative Actual',
                                     line=dict(color='#2E4A3F', width=3)))
            # Add budget line if set
            total_budget = sum(budgets.get(budget_key, {}).get(s, 0) for s in store_filter)
            if total_budget > 0:
                fig.add_hline(y=total_budget, line_dash="dash", line_color="red",
                             annotation_text=f"Total Budget: \u20ac{total_budget:,.0f}")
            fig.update_layout(height=400,
                             xaxis_title='Month', yaxis_title='Cumulative Amount (\u20ac)')
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # TAB 3: VARIANCE ANALYSIS
    # ==========================================
    with tab3:
        if actuals_df.empty:
            st.info("No data available for the selected criteria.")
        else:
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)]

            st.subheader("Variance Analysis: Budget vs Actual")

            # Build store-level variance data
            var_data = []
            for store_code in store_filter:
                if store_code in STORE_LOCATIONS:
                    actual = filtered_df[filtered_df['store_code'] == store_code]['amount'].sum()
                    budget = budgets.get(budget_key, {}).get(store_code, 0)
                    var_amt = budget - actual
                    var_pct = (var_amt / budget * 100) if budget > 0 else (0 if actual == 0 else -100)
                    status = "Under Budget" if var_amt >= 0 else "Over Budget"
                    if budget == 0 and actual == 0:
                        status = "No Activity"
                    elif budget == 0 and actual > 0:
                        status = "No Budget Set"
                    var_data.append({
                        'Store': STORE_LOCATIONS[store_code]['name'],
                        'Code': store_code,
                        'City': STORE_LOCATIONS[store_code]['city'],
                        'Budget': budget,
                        'Actual': actual,
                        'Variance': var_amt,
                        'Variance %': var_pct,
                        'Status': status,
                    })

            var_df = pd.DataFrame(var_data)
            # Only show stores with budget or actual activity
            active_var_df = var_df[(var_df['Budget'] > 0) | (var_df['Actual'] > 0)].copy()

            if active_var_df.empty:
                st.info("Set budgets in the Budget Management tab to see variance analysis.")
            else:
                # Summary cards
                total_budget = active_var_df['Budget'].sum()
                total_actual = active_var_df['Actual'].sum()
                total_var = total_budget - total_actual
                over_count = len(active_var_df[active_var_df['Variance'] < 0])
                under_count = len(active_var_df[active_var_df['Variance'] >= 0])

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Total Budget", f"\u20ac{total_budget:,.0f}")
                with c2:
                    st.metric("Total Actual", f"\u20ac{total_actual:,.0f}")
                with c3:
                    pct = (total_var / total_budget * 100) if total_budget > 0 else 0
                    st.metric("Total Variance", f"\u20ac{total_var:,.0f}",
                             delta=f"{pct:+.1f}%",
                             delta_color="normal" if total_var >= 0 else "inverse")
                with c4:
                    st.metric("Over / Under Budget", f"{over_count} / {under_count}")

                st.divider()

                # Waterfall-style variance chart
                st.subheader("Variance by Store")
                chart_df = active_var_df.sort_values('Variance')
                colors = ['#dc3545' if v < 0 else '#28a745' for v in chart_df['Variance']]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=chart_df['Store'], y=chart_df['Variance'],
                    marker_color=colors,
                    text=[f"\u20ac{v:,.0f}" for v in chart_df['Variance']],
                    textposition='outside'
                ))
                fig.add_hline(y=0, line_color="black", line_width=1)
                fig.update_layout(height=450, yaxis_title='Variance (\u20ac)',
                                 title="Red = Over Budget | Green = Under Budget")
                st.plotly_chart(fig, use_container_width=True)

                # Variance % chart
                st.subheader("Variance Percentage by Store")
                pct_df = active_var_df[active_var_df['Budget'] > 0].sort_values('Variance %')
                pct_colors = ['#dc3545' if v < 0 else '#28a745' for v in pct_df['Variance %']]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=pct_df['Store'], y=pct_df['Variance %'],
                    marker_color=pct_colors,
                    text=[f"{v:+.1f}%" for v in pct_df['Variance %']],
                    textposition='outside'
                ))
                fig.add_hline(y=0, line_color="black", line_width=1)
                fig.update_layout(height=400, yaxis_title='Variance %')
                st.plotly_chart(fig, use_container_width=True)

                st.divider()

                # Variance by account
                st.subheader("Variance by Account Category")
                acc_actual = filtered_df.groupby('account_label')['amount'].sum().reset_index()
                acc_actual.columns = ['Account', 'Actual']
                st.dataframe(acc_actual.sort_values('Actual', ascending=False),
                            use_container_width=True, hide_index=True,
                            column_config={
                                'Actual': st.column_config.NumberColumn(format='\u20ac%.2f')
                            })

                st.divider()

                # Detailed variance table
                st.subheader("Detailed Variance Table")
                st.dataframe(
                    active_var_df[['Store', 'City', 'Budget', 'Actual', 'Variance', 'Variance %', 'Status']].sort_values('Variance'),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Budget': st.column_config.NumberColumn(format='\u20ac%.0f'),
                        'Actual': st.column_config.NumberColumn(format='\u20ac%.0f'),
                        'Variance': st.column_config.NumberColumn(format='\u20ac%.0f'),
                        'Variance %': st.column_config.NumberColumn(format='%.1f%%'),
                    }
                )

    # ==========================================
    # TAB 4: BUDGET MANAGEMENT
    # ==========================================
    with tab4:
        st.subheader("Set CAPEX Budgets per Store")
        st.info("Budgets are set as **total CAPEX budget** per store (not per year). Accounts: " + ', '.join(selected_accounts))

        # Initialize budget dict for this key
        if budget_key not in budgets:
            budgets[budget_key] = {}

        # Budget input form
        col1, col2 = st.columns(2)

        stores_list = [(code, info) for code, info in STORE_LOCATIONS.items()]
        half = len(stores_list) // 2

        with col1:
            for code, info in stores_list[:half]:
                current_budget = budgets[budget_key].get(code, 0)
                new_budget = st.number_input(
                    f"{info['name']} ({code})",
                    min_value=0,
                    value=int(current_budget),
                    step=1000,
                    key=f"budget_{code}"
                )
                budgets[budget_key][code] = new_budget

        with col2:
            for code, info in stores_list[half:]:
                current_budget = budgets[budget_key].get(code, 0)
                new_budget = st.number_input(
                    f"{info['name']} ({code})",
                    min_value=0,
                    value=int(current_budget),
                    step=1000,
                    key=f"budget_{code}"
                )
                budgets[budget_key][code] = new_budget

        st.divider()

        # Quick budget templates
        st.subheader("Quick Templates")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("New Store Template (50k)", use_container_width=True):
                for code in STORE_LOCATIONS.keys():
                    budgets[budget_key][code] = 50000
                save_budgets(budgets)
                st.success("Applied 50k budget to all stores")
                st.rerun()

        with col2:
            if st.button("Renovation Template (25k)", use_container_width=True):
                for code in STORE_LOCATIONS.keys():
                    budgets[budget_key][code] = 25000
                save_budgets(budgets)
                st.success("Applied 25k budget to all stores")
                st.rerun()

        with col3:
            if st.button("Clear All Budgets", use_container_width=True):
                budgets[budget_key] = {}
                save_budgets(budgets)
                st.warning("All budgets cleared")
                st.rerun()

        # Save button
        st.divider()
        if st.button("Save Budgets", type="primary", use_container_width=True):
            save_budgets(budgets)
            st.success("Budgets saved!")
            st.balloons()

    # ==========================================
    # TAB 5: STORE MAP
    # ==========================================
    with tab5:
        st.subheader("Wakuli Store Locations")

        # Create map data
        map_data = []
        for code, info in STORE_LOCATIONS.items():
            if code != "OOH" and 'lat' in info:
                actual = actuals_df[actuals_df['store_code'] == code]['amount'].sum() if not actuals_df.empty else 0
                budget = budgets.get(budget_key, {}).get(code, 0)
                map_data.append({
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'name': info['name'],
                    'code': code,
                    'city': info['city'],
                    'address': info['address'],
                    'actual': actual,
                    'budget': budget,
                    'size': max(actual / 1000, 10)
                })

        map_df = pd.DataFrame(map_data)

        fig = px.scatter_mapbox(
            map_df,
            lat='lat',
            lon='lon',
            size='size',
            color='actual',
            color_continuous_scale='Greens',
            hover_name='name',
            hover_data={
                'city': True,
                'address': True,
                'actual': ':\u20ac,.0f',
                'budget': ':\u20ac,.0f',
                'lat': False,
                'lon': False,
                'size': False
            },
            zoom=6.5,
            center={'lat': 52.1, 'lon': 5.0}
        )
        fig.update_layout(
            mapbox_style='carto-positron',
            height=600,
            margin={'r': 0, 't': 0, 'l': 0, 'b': 0}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Store directory
        st.subheader("Store Directory")

        cols = st.columns(3)
        for i, (code, info) in enumerate([(c, i) for c, i in STORE_LOCATIONS.items() if c != "OOH"]):
            with cols[i % 3]:
                actual = actuals_df[actuals_df['store_code'] == code]['amount'].sum() if not actuals_df.empty else 0
                st.markdown(f"""
                <div class="store-card">
                    <strong>{info['name']}</strong> ({code})<br>
                    {info['address']}, {info['city']}<br>
                    CAPEX: \u20ac{actual:,.0f}
                </div>
                """, unsafe_allow_html=True)

    # ==========================================
    # TAB 6: DETAILED DATA with invoice popup
    # ==========================================
    with tab6:
        st.subheader("Detailed Transactions")

        if actuals_df.empty:
            st.info("No data available.")
        else:
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)].copy()

            # Summary stats
            st.metric("Total transactions", len(filtered_df))

            # Show table with clickable invoice references
            display_df = filtered_df[['date', 'store_name', 'account', 'account_label', 'amount', 'description', 'move_name', 'move_id']].sort_values('date', ascending=False).reset_index(drop=True)

            st.dataframe(
                display_df[['date', 'store_name', 'account_label', 'amount', 'description', 'move_name']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'date': 'Date',
                    'store_name': 'Store',
                    'account_label': 'Account',
                    'amount': st.column_config.NumberColumn('Amount', format='\u20ac%.2f'),
                    'description': 'Description',
                    'move_name': 'Invoice/Entry',
                }
            )

            st.divider()

            # Invoice detail viewer
            st.subheader("Invoice / Entry Detail Viewer")

            if has_odoo:
                # Get unique move references
                moves_with_ids = filtered_df[filtered_df['move_id'].notna()][['move_id', 'move_name']].drop_duplicates()
                if not moves_with_ids.empty:
                    move_options = {f"{row['move_name']} (ID: {int(row['move_id'])})": int(row['move_id'])
                                   for _, row in moves_with_ids.iterrows() if row['move_id']}

                    if move_options:
                        selected_move = st.selectbox("Select an invoice/entry to view details:",
                                                     options=["-- Select --"] + list(move_options.keys()))

                        if selected_move != "-- Select --":
                            move_id = move_options[selected_move]
                            with st.expander(f"Details: {selected_move}", expanded=True):
                                render_invoice_popup(db, uid, password, move_id, selected_move)
                    else:
                        st.info("No invoice references found in the current data.")
                else:
                    st.info("No invoice references found in the current data.")
            else:
                st.info("Connect to Odoo to view invoice details and PDFs.")

            st.divider()

            # Export button
            csv = filtered_df.to_csv(index=False)
            years_str = '-'.join(str(y) for y in selected_years)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"wakuli_capex_{years_str}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
