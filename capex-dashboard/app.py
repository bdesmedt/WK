"""
Wakuli CAPEX Budget Dashboard
============================
Track construction budgets vs actuals for Wakuli stores.
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

# Asset accounts for CAPEX tracking
CAPEX_ACCOUNTS = {
    "037000": "CAPEX Winkels (Store Renovations)",
    "032000": "WIA - Assets Under Construction",
    "031000": "Bedrijfsinventaris (Business Inventory)",
    "021000": "Koffiemachines (Coffee Machines)",
    "013000": "Verbouwingen (Renovations)"
}


@st.cache_resource
def get_odoo_connection():
    """Initialize Odoo connection."""
    url = st.secrets.get("ODOO_URL", os.environ.get("ODOO_URL", "https://wakuli.odoo.com"))
    db = st.secrets.get("ODOO_DB", os.environ.get("ODOO_DB", "wakuli-production-10206791"))
    username = st.secrets.get("ODOO_USER", os.environ.get("ODOO_USER", "accounting@fidfinance.nl"))
    password = st.secrets.get("ODOO_PASSWORD", os.environ.get("ODOO_PASSWORD", ""))
    
    if not username or not password:
        return None, None, None, None
    
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        return url, db, uid, models, password
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None, None, None, None, None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_capex_actuals(_models, db, uid, password, account_codes, year):
    """Fetch actual CAPEX bookings from Odoo."""
    if not _models:
        return pd.DataFrame()
    
    # Build domain for selected accounts
    account_domain = ['|'] * (len(account_codes) - 1) if len(account_codes) > 1 else []
    for code in account_codes:
        account_domain.append(['account_id.code', '=', code])
    
    domain = [
        ['company_id', '=', 2],  # Wakuli Retail Holding
        ['date', '>=', f'{year}-01-01'],
        ['date', '<=', f'{year}-12-31'],
        ['parent_state', '=', 'posted']
    ] + account_domain
    
    try:
        lines = _models.execute_kw(db, uid, password, 'account.analytic.line', 'search_read',
            [domain],
            {'fields': ['date', 'amount', 'name', 'general_account_id', 'x_plan2_id', 'move_line_id'],
             'limit': 5000})
        
        if not lines:
            return pd.DataFrame()
        
        # Process data
        data = []
        for line in lines:
            store_code = "OOH"  # Default
            if line.get('x_plan2_id'):
                # Find store code from Odoo ID
                odoo_id = line['x_plan2_id'][0] if isinstance(line['x_plan2_id'], list) else line['x_plan2_id']
                for code, oid in STORE_ODOO_IDS.items():
                    if oid == odoo_id:
                        store_code = code
                        break
            
            account_code = line['general_account_id'][1].split()[0] if line.get('general_account_id') else 'Unknown'
            
            data.append({
                'date': line['date'],
                'month': line['date'][:7],
                'amount': abs(line['amount']),  # Convert to positive for display
                'description': line.get('name', ''),
                'account': account_code,
                'store_code': store_code,
                'store_name': STORE_LOCATIONS.get(store_code, {}).get('name', store_code)
            })
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def load_budgets():
    """Load budgets from local storage."""
    budget_file = "budgets.json"
    if os.path.exists(budget_file):
        with open(budget_file, 'r') as f:
            return json.load(f)
    return {}


def save_budgets(budgets):
    """Save budgets to local storage."""
    with open("budgets.json", 'w') as f:
        json.dump(budgets, f, indent=2)


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
        st.header("⚙️ Settings")
        
        # Year selection (multi-year)
        current_year = datetime.now().year
        year_options = list(range(current_year - 3, current_year + 2))
        selected_years = st.multiselect(
            "📅 Year(s)",
            options=year_options,
            default=[current_year]
        )
        if not selected_years:
            selected_years = [current_year]
        selected_years = sorted(selected_years)
        
        # Account selection
        st.subheader("📊 Accounts to Track")
        selected_accounts = []
        for code, name in CAPEX_ACCOUNTS.items():
            if st.checkbox(name, value=(code == "037000"), key=f"acc_{code}"):
                selected_accounts.append(code)
        
        if not selected_accounts:
            selected_accounts = ["037000"]
        
        st.divider()
        
        # Store filter
        st.subheader("🏪 Store Filter")
        store_options = ["All Stores"] + [f"{code} - {info['name']}" for code, info in STORE_LOCATIONS.items() if code != "OOH"]
        selected_stores = st.multiselect("Select stores", options=store_options, default=["All Stores"])
        
        if "All Stores" in selected_stores:
            store_filter = list(STORE_LOCATIONS.keys())
        else:
            store_filter = [s.split(" - ")[0] for s in selected_stores]
    
    # Check Odoo connection
    connection = get_odoo_connection()
    
    if connection[0] is None:
        st.warning("⚠️ Odoo credentials not configured. Using demo data.")
        st.info("To connect to Odoo, set these secrets in Streamlit Cloud or environment variables:\n- ODOO_URL\n- ODOO_DB\n- ODOO_USER\n- ODOO_PASSWORD")

        # Demo data for each selected year
        demo_frames = []
        for yr in selected_years:
            demo_data = {
                'date': [f'{yr}-01-15', f'{yr}-02-20', f'{yr}-03-10', f'{yr}-04-05', f'{yr}-05-12', f'{yr}-06-08'],
                'month': [f'{yr}-01', f'{yr}-02', f'{yr}-03', f'{yr}-04', f'{yr}-05', f'{yr}-06'],
                'amount': [15000, 8500, 22000, 5000, 18000, 12000],
                'description': ['Renovation', 'Equipment', 'Construction', 'Repairs', 'Renovation', 'Equipment'],
                'account': ['037000', '037000', '037000', '037000', '037000', '037000'],
                'store_code': ['HAS', 'VIS', 'THER', 'PIET', 'STOEL', 'MEENT'],
                'store_name': ['Haarlemmerstraat', 'Visstraat', 'Theresiastraat', 'Piet Heinstraat', 'Stoeldraaierstraat', 'Meent'],
                'year': [yr] * 6
            }
            demo_frames.append(pd.DataFrame(demo_data))
        actuals_df = pd.concat(demo_frames, ignore_index=True)
    else:
        url, db, uid, models, password = connection
        # Fetch data for each selected year and combine
        year_frames = []
        for yr in selected_years:
            yr_df = fetch_capex_actuals(models, db, uid, password, selected_accounts, yr)
            if not yr_df.empty:
                yr_df['year'] = yr
                year_frames.append(yr_df)
        actuals_df = pd.concat(year_frames, ignore_index=True) if year_frames else pd.DataFrame()
    
    # Load budgets
    budgets = load_budgets()
    budget_keys = [f"{yr}_{'-'.join(selected_accounts)}" for yr in selected_years]
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💰 Budget Management", "🗺️ Store Map", "📋 Detailed Data"])
    
    # TAB 1: DASHBOARD
    with tab1:
        if actuals_df.empty:
            st.info("No data available for the selected criteria.")
        else:
            # Filter by selected stores
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)]
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_actual = filtered_df['amount'].sum()
            total_budget = sum(
                budgets.get(bk, {}).get(store, 0)
                for bk in budget_keys
                for store in store_filter
            )
            variance = total_budget - total_actual
            variance_pct = (variance / total_budget * 100) if total_budget > 0 else 0
            
            with col1:
                st.metric("💵 Total Budget", f"€{total_budget:,.0f}")
            with col2:
                st.metric("📈 Total Actual", f"€{total_actual:,.0f}")
            with col3:
                st.metric("📊 Variance", f"€{variance:,.0f}", 
                         delta=f"{variance_pct:+.1f}%",
                         delta_color="normal" if variance >= 0 else "inverse")
            with col4:
                num_stores = filtered_df['store_code'].nunique()
                st.metric("🏪 Active Stores", num_stores)
            
            st.divider()
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 CAPEX per Store")
                store_summary = filtered_df.groupby(['store_code', 'store_name'])['amount'].sum().reset_index()
                store_summary = store_summary.sort_values('amount', ascending=True)
                
                fig = px.bar(store_summary, x='amount', y='store_name', orientation='h',
                            color='amount', color_continuous_scale='Greens',
                            labels={'amount': 'Amount (€)', 'store_name': 'Store'})
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📈 Monthly Trend")
                monthly = filtered_df.groupby('month')['amount'].sum().reset_index()
                monthly = monthly.sort_values('month')
                
                fig = px.area(monthly, x='month', y='amount',
                             labels={'amount': 'Amount (€)', 'month': 'Month'},
                             color_discrete_sequence=['#2E4A3F'])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # Budget vs Actual comparison
            st.subheader("🎯 Budget vs Actual by Store")
            
            comparison_data = []
            for store_code in store_filter:
                if store_code in STORE_LOCATIONS:
                    actual = filtered_df[filtered_df['store_code'] == store_code]['amount'].sum()
                    budget = sum(budgets.get(bk, {}).get(store_code, 0) for bk in budget_keys)
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
    
    # TAB 2: BUDGET MANAGEMENT
    with tab2:
        st.subheader("💰 Set Budgets per Store")

        # Year selector for budget editing (pick one year at a time)
        budget_year = st.selectbox(
            "Select year to edit budget",
            options=selected_years,
            index=0,
            key="budget_year_select"
        )
        budget_key = f"{budget_year}_{'-'.join(selected_accounts)}"
        st.info(f"Setting budgets for **{budget_year}** | Accounts: {', '.join(selected_accounts)}")

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
                    f"🏪 {info['name']} ({code})",
                    min_value=0,
                    value=int(current_budget),
                    step=1000,
                    key=f"budget_{budget_year}_{code}"
                )
                budgets[budget_key][code] = new_budget

        with col2:
            for code, info in stores_list[half:]:
                current_budget = budgets[budget_key].get(code, 0)
                new_budget = st.number_input(
                    f"🏪 {info['name']} ({code})",
                    min_value=0,
                    value=int(current_budget),
                    step=1000,
                    key=f"budget_{budget_year}_{code}"
                )
                budgets[budget_key][code] = new_budget

        st.divider()

        # Quick budget templates
        st.subheader("📋 Quick Templates")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🆕 New Store Template (€50k)", use_container_width=True):
                for code in STORE_LOCATIONS.keys():
                    budgets[budget_key][code] = 50000
                st.success(f"Applied €50k budget to all stores for {budget_year}")
                st.rerun()

        with col2:
            if st.button("🔄 Renovation Template (€25k)", use_container_width=True):
                for code in STORE_LOCATIONS.keys():
                    budgets[budget_key][code] = 25000
                st.success(f"Applied €25k budget to all stores for {budget_year}")
                st.rerun()

        with col3:
            if st.button("🗑️ Clear All Budgets", use_container_width=True):
                budgets[budget_key] = {}
                st.warning(f"All budgets cleared for {budget_year}")
                st.rerun()

        # Save button
        st.divider()
        if st.button("💾 Save Budgets", type="primary", use_container_width=True):
            save_budgets(budgets)
            st.success("✅ Budgets saved successfully!")
            st.balloons()
    
    # TAB 3: STORE MAP
    with tab3:
        st.subheader("🗺️ Wakuli Store Locations")
        
        # Create map data
        map_data = []
        for code, info in STORE_LOCATIONS.items():
            if code != "OOH" and 'lat' in info:
                actual = actuals_df[actuals_df['store_code'] == code]['amount'].sum() if not actuals_df.empty else 0
                budget = sum(budgets.get(bk, {}).get(code, 0) for bk in budget_keys)
                map_data.append({
                    'lat': info['lat'],
                    'lon': info['lon'],
                    'name': info['name'],
                    'code': code,
                    'city': info['city'],
                    'address': info['address'],
                    'actual': actual,
                    'budget': budget,
                    'size': max(actual / 1000, 10)  # Scale for visibility
                })
        
        map_df = pd.DataFrame(map_data)
        
        # Create plotly map
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
                'actual': ':€,.0f',
                'budget': ':€,.0f',
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
        st.subheader("📍 Store Directory")
        
        cols = st.columns(3)
        for i, (code, info) in enumerate([(c, i) for c, i in STORE_LOCATIONS.items() if c != "OOH"]):
            with cols[i % 3]:
                actual = actuals_df[actuals_df['store_code'] == code]['amount'].sum() if not actuals_df.empty else 0
                st.markdown(f"""
                <div class="store-card">
                    <strong>{info['name']}</strong> ({code})<br>
                    📍 {info['address']}, {info['city']}<br>
                    💰 CAPEX: €{actual:,.0f}
                </div>
                """, unsafe_allow_html=True)
    
    # TAB 4: DETAILED DATA
    with tab4:
        st.subheader("📋 Detailed Transactions")
        
        if actuals_df.empty:
            st.info("No data available.")
        else:
            filtered_df = actuals_df[actuals_df['store_code'].isin(store_filter)]
            
            # Summary table
            st.dataframe(
                filtered_df[['date', 'store_name', 'account', 'amount', 'description']].sort_values('date', ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'date': 'Date',
                    'store_name': 'Store',
                    'account': 'Account',
                    'amount': st.column_config.NumberColumn('Amount', format='€%.2f'),
                    'description': 'Description'
                }
            )
            
            # Export button
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"wakuli_capex_{'_'.join(str(y) for y in selected_years)}.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
