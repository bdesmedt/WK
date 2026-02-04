"""
Wakuli Retail Analytics - CFO Dashboard
=========================================
Comprehensive financial analytics platform for Wakuli coffee stores.
Calculates ROI, profitability, revenue metrics, cost analysis,
operational efficiency, and mission-aligned impact KPIs.

Brewing Profit with Purpose.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

from config import (
    STORE_LOCATIONS, STORE_ODOO_IDS, CAPEX_ACCOUNTS, COLORS, CHART_COLORS,
    TARGETS, SOURCING_ORIGINS, PRODUCT_CATEGORIES, DAYPARTS,
    APP_CONFIG, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING,
    ACCOUNT_MAP, ODOO_MODULES, ODOO_ID_TO_STORE, get_all_account_codes,
    NMBRS_CONFIG, NMBRS_DEPARTMENT_TO_STORE,
)
from styles import get_brand_css
from odoo_connector import (
    authenticate_odoo, fetch_capex_actuals, fetch_revenue_data,
    fetch_cost_data, fetch_pos_orders, fetch_employees,
    fetch_chart_of_accounts, fetch_analytic_accounts,
    check_data_availability, get_secret,
)
from nmbrs_connector import (
    is_nmbrs_configured, build_labor_data_from_nmbrs,
    check_nmbrs_connection, fetch_nmbrs_employees,
    fetch_nmbrs_departments, fetch_nmbrs_salary_data,
)
from demo_data import generate_all_demo_data
from kpi_engine import (
    calculate_store_roi, calculate_break_even, calculate_profitability,
    calculate_profitability_by_store, calculate_revenue_metrics,
    calculate_revenue_by_period, calculate_cost_structure,
    calculate_customer_metrics, calculate_labor_efficiency,
    calculate_inventory_metrics, calculate_cash_flow,
    calculate_impact_summary, calculate_executive_summary,
)
from components import (
    metric_card, impact_card, progress_bar, section_header, badge,
    apply_brand_layout, waterfall_chart, gauge_chart, donut_chart,
    bar_chart, line_chart, area_chart, render_invoice_popup,
    fmt_eur, fmt_pct, fmt_number,
)


# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"],
    initial_sidebar_state=APP_CONFIG["initial_sidebar_state"],
)

# Inject brand CSS
st.markdown(get_brand_css(), unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────
def render_sidebar():
    """Render the sidebar with all filters and controls."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <img src="https://www.wakuli.com/cdn/shop/files/logo_green.png?v=1719823287&width=200"
                 width="100" style="filter: brightness(0) invert(1); opacity: 0.9;">
            <div style="font-family: Poppins; font-size: 0.75rem; color: rgba(255,255,255,0.6);
                        margin-top: 4px; letter-spacing: 1px;">RETAIL ANALYTICS</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Year selection
        st.markdown("**Select Years**")
        current_year = datetime.now().year
        year_options = list(range(current_year - 4, current_year + 1))
        selected_years = st.multiselect(
            "Years", options=year_options, default=[current_year - 1, current_year],
            label_visibility="collapsed",
            help="Select one or more years to analyze",
        )
        if not selected_years:
            selected_years = [current_year]

        st.markdown("---")

        # Store filter
        st.markdown("**Store Filter**")
        store_options = ["All Stores"] + [
            f"{code} - {info['name']}" for code, info in STORE_LOCATIONS.items() if code != "OOH"
        ]
        selected_stores = st.multiselect(
            "Stores", options=store_options, default=["All Stores"],
            label_visibility="collapsed",
        )
        if "All Stores" in selected_stores or not selected_stores:
            store_filter = [c for c in STORE_LOCATIONS if c != "OOH"]
        else:
            store_filter = [s.split(" - ")[0] for s in selected_stores]

        st.markdown("---")

        # CAPEX accounts (for CAPEX tab)
        st.markdown("**CAPEX Accounts**")
        selected_accounts = []
        for code, name in CAPEX_ACCOUNTS.items():
            if st.checkbox(name, value=(code == "037000"), key=f"acc_{code}"):
                selected_accounts.append(code)
        if not selected_accounts:
            selected_accounts = ["037000"]

        st.markdown("---")

        # Connection status
        st.markdown("**Data Sources**")
        odoo_user = get_secret("ODOO_USER", "")
        if odoo_user:
            st.success(f"Odoo: {odoo_user[:20]}...")
        else:
            st.info("Odoo: not configured")

        if is_nmbrs_configured():
            st.success("Nmbrs: connected")
        else:
            st.info("Nmbrs: not configured")

        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; font-size: 0.7rem; color: rgba(255,255,255,0.4);
                    padding-top: 0.5rem;">
            Built by FidFinance for Wakuli<br>
            Brewing Profit with Purpose
        </div>
        """, unsafe_allow_html=True)

    return selected_years, store_filter, selected_accounts


# ──────────────────────────────────────────────
# DATA LOADING — per-section Odoo with demo fallback
# ──────────────────────────────────────────────
def load_data(selected_years, selected_accounts):
    """Load data from Odoo where configured, fall back to demo per section.

    For each data category (revenue, costs, capex), attempts to fetch from
    Odoo first. If Odoo returns data, it's used; otherwise demo data is used
    for that section. This allows a gradual rollout: configure real account
    codes in ACCOUNT_MAP section by section.
    """
    auth = authenticate_odoo()
    db, uid, password, odoo_url = auth
    has_odoo = db is not None and uid is not None

    # Always generate demo data as a complete fallback
    demo = generate_all_demo_data(selected_years)
    years_tuple = tuple(selected_years)

    # Track which sections are using real vs demo data
    data_sources = {}

    if has_odoo:
        # --- Revenue ---
        odoo_revenue = fetch_revenue_data(db, uid, password, years_tuple)
        if not odoo_revenue.empty:
            demo['revenue'] = odoo_revenue
            data_sources['revenue'] = 'odoo'
        else:
            data_sources['revenue'] = 'demo'

        # --- Costs (COGS + OpEx) ---
        odoo_costs = fetch_cost_data(db, uid, password, years_tuple)
        if not odoo_costs.empty:
            demo['costs'] = odoo_costs
            data_sources['costs'] = 'odoo'
        else:
            data_sources['costs'] = 'demo'

        # --- CAPEX ---
        odoo_capex = fetch_capex_actuals(db, uid, password, tuple(selected_accounts), years_tuple)
        if not odoo_capex.empty:
            demo['capex'] = odoo_capex
            data_sources['capex'] = 'odoo'
        else:
            data_sources['capex'] = 'demo'

        # --- POS (optional, for customer metrics) ---
        if ODOO_MODULES.get("pos"):
            pos_data = fetch_pos_orders(db, uid, password, years_tuple)
            if not pos_data.empty:
                demo['pos_orders'] = pos_data
                data_sources['pos'] = 'odoo'

        # --- HR (optional, for labor metrics) ---
        if ODOO_MODULES.get("hr"):
            hr_data = fetch_employees(db, uid, password)
            if not hr_data.empty:
                demo['employees'] = hr_data
                data_sources['hr'] = 'odoo'

        demo['has_odoo'] = True
        demo['db'] = db
        demo['uid'] = uid
        demo['password'] = password
    else:
        demo['has_odoo'] = False
        demo['db'] = None
        demo['uid'] = None
        demo['password'] = None
        data_sources = {s: 'demo' for s in ['revenue', 'costs', 'capex']}

    # --- Nmbrs: labor/employee data (independent of Odoo) ---
    if NMBRS_CONFIG.get("enabled") and is_nmbrs_configured():
        nmbrs_labor = build_labor_data_from_nmbrs(demo['revenue'], years_tuple)
        if not nmbrs_labor.empty:
            demo['labor'] = nmbrs_labor
            data_sources['labor'] = 'nmbrs'
        else:
            data_sources['labor'] = 'demo'
    else:
        data_sources['labor'] = 'demo'

    demo['data_sources'] = data_sources
    return demo


# ──────────────────────────────────────────────
# BUDGET HELPERS
# ──────────────────────────────────────────────
def load_budgets():
    if 'budgets' not in st.session_state:
        st.session_state.budgets = {}
    return st.session_state.budgets


def save_budgets(budgets):
    st.session_state.budgets = budgets


# ──────────────────────────────────────────────
# TAB: EXECUTIVE SUMMARY
# ──────────────────────────────────────────────
def render_executive_tab(data, store_filter):
    """Hero section + executive-level KPI overview."""
    revenue_df = data['revenue']
    cost_df = data['costs']
    customer_df = data['customers']
    investment_df = data['investment']
    impact_df = data['impact']

    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
    if not cost_df.empty:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]
    if not customer_df.empty:
        customer_df = customer_df[customer_df['store_code'].isin(store_filter)]

    summary = calculate_executive_summary(
        revenue_df, cost_df, customer_df, investment_df, impact_df, store_filter
    )

    # Hero row
    st.markdown("""
    <div style="background: linear-gradient(135deg, #004E64 0%, #2D3142 100%);
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;
                box-shadow: 0 4px 20px rgba(0,78,100,0.3);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
            <div>
                <div style="font-family: Poppins; font-size: 1.6rem; font-weight: 800; color: white;">
                    Brewing Profit with Purpose
                </div>
                <div style="font-family: Poppins; font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-top: 4px;">
                    Wakuli Retail Analytics &mdash; CFO Dashboard
                </div>
            </div>
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-family: Poppins; font-size: 2rem; font-weight: 800; color: #F7B801;">
                        """ + fmt_eur(summary['total_revenue']) + """
                    </div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">TOTAL REVENUE</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-family: Poppins; font-size: 2rem; font-weight: 800; color: #25A18E;">
                        """ + fmt_pct(summary['net_margin_pct']) + """
                    </div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">NET MARGIN</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-family: Poppins; font-size: 2rem; font-weight: 800; color: #FF6B35;">
                        """ + fmt_pct(summary['avg_roi_pct']) + """
                    </div>
                    <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">AVG STORE ROI</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Primary KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        metric_card("EBITDA", fmt_eur(summary['ebitda']), color="teal")
    with c2:
        metric_card("Gross Margin", fmt_pct(summary['gross_margin_pct']),
                     delta=summary['gross_margin_pct'] - TARGETS['gross_margin_pct'] * 100,
                     delta_suffix="% vs target", color="green")
    with c3:
        metric_card("Revenue Growth", fmt_pct(summary['growth_pct']),
                     delta=summary['growth_pct'], delta_suffix="% (3mo)", color="orange")
    with c4:
        metric_card("Avg Ticket", f"\u20ac{summary['avg_transaction_value']:.2f}", color="yellow")
    with c5:
        metric_card("Active Stores", str(summary['active_stores']), color="teal")
    with c6:
        metric_card("Total Customers", fmt_number(summary['total_customers']), color="green")

    st.markdown("")

    # Revenue trend + profitability side by side
    col1, col2 = st.columns(2)

    with col1:
        section_header("Revenue Trend", "Monthly revenue across all selected stores")
        rev_by_month = calculate_revenue_by_period(revenue_df, 'month')
        if not rev_by_month.empty:
            fig = area_chart(rev_by_month, x='period', y='revenue',
                            title=None, height=350,
                            color_sequence=[COLORS['orange']])
            fig.update_traces(
                hovertemplate='%{x}<br>\u20ac%{y:,.0f}<extra></extra>',
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Profitability Overview", "Revenue vs costs breakdown")
        profit = calculate_profitability(revenue_df, cost_df, store_filter)
        if profit:
            categories = ['Revenue', 'COGS', 'Operating\nExpenses', 'Net Profit']
            values = [
                profit['total_revenue'],
                -profit['cogs'],
                -(profit['total_costs'] - profit['cogs']),
                profit['net_profit'],
            ]
            fig = waterfall_chart(categories, values, height=350)
            st.plotly_chart(fig, use_container_width=True)

    # Impact spotlight
    st.markdown("")
    section_header("Impact Spotlight", "How your coffee is making a difference")
    impact = calculate_impact_summary(impact_df)
    if impact:
        i1, i2, i3, i4, i5 = st.columns(5)
        with i1:
            impact_card(f"{impact.get('current_farmers_supported', 0):,}", "Farmers Supported")
        with i2:
            impact_card(fmt_eur(impact.get('total_premium_paid', 0)), "Premium Paid to Farmers")
        with i3:
            impact_card(f"{impact.get('avg_direct_trade_pct', 0):.0f}", "Direct Trade", suffix="%")
        with i4:
            impact_card(f"{impact.get('total_cups_served', 0):,}", "Cups Served")
        with i5:
            impact_card(f"{impact.get('current_co2_per_cup', 0):.0f}g", "CO2 per Cup")


# ──────────────────────────────────────────────
# TAB: FINANCIAL DEEP DIVE
# ──────────────────────────────────────────────
def render_financial_tab(data, store_filter):
    """ROI analysis, break-even, P&L, and profitability deep dive."""
    revenue_df = data['revenue']
    cost_df = data['costs']
    investment_df = data['investment']

    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
    if not cost_df.empty:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]

    # ROI Analysis
    section_header("Store ROI Analysis", "Return on investment per location")

    roi_df = calculate_store_roi(revenue_df, cost_df, investment_df)
    if not roi_df.empty:
        roi_df = roi_df[roi_df['store_code'].isin(store_filter)]

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            avg_roi = roi_df['roi_pct'].mean()
            metric_card("Average ROI", fmt_pct(avg_roi), color="orange",
                        tooltip="(Cumulative Net Profit / Total Investment) x 100")
        with c2:
            total_inv = roi_df['total_investment'].sum()
            metric_card("Total Investment", fmt_eur(total_inv), color="teal")
        with c3:
            total_profit = roi_df['net_profit'].sum()
            metric_card("Total Net Profit", fmt_eur(total_profit),
                        delta=total_profit, delta_suffix="", color="green")
        with c4:
            best = roi_df.loc[roi_df['roi_pct'].idxmax()]
            metric_card("Best Performer", f"{best['store_name']}",
                        delta=best['roi_pct'], delta_suffix="% ROI", color="yellow")

        st.markdown("")

        # ROI bar chart per store
        roi_sorted = roi_df.sort_values('roi_pct', ascending=True)
        colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in roi_sorted['roi_pct']]

        fig = go.Figure(go.Bar(
            x=roi_sorted['roi_pct'], y=roi_sorted['store_name'],
            orientation='h', marker_color=colors,
            text=[f"{v:+.1f}%" for v in roi_sorted['roi_pct']],
            textposition='outside',
            hovertemplate='%{y}<br>ROI: %{x:.1f}%<extra></extra>',
        ))
        fig.add_vline(x=0, line_color=COLORS['charcoal'], line_width=1)
        fig = apply_brand_layout(fig, height=max(300, len(roi_sorted) * 32),
                                 title="ROI by Store", show_legend=False)
        fig.update_layout(xaxis_title="ROI %", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    # Break-even Analysis
    st.markdown("")
    section_header("Break-Even Analysis", "Months to payback initial investment")

    be_df = calculate_break_even(revenue_df, cost_df, investment_df)
    if not be_df.empty:
        be_df = be_df[be_df['store_code'].isin(store_filter)]
        be_display = be_df[be_df['months_to_payback'].notna()].copy()

        if not be_display.empty:
            col1, col2 = st.columns(2)

            with col1:
                be_sorted = be_display.sort_values('months_to_payback')
                colors_be = [COLOR_POSITIVE if m <= TARGETS['break_even_months'] else COLOR_WARNING
                             for m in be_sorted['months_to_payback']]
                fig = go.Figure(go.Bar(
                    x=be_sorted['store_name'], y=be_sorted['months_to_payback'],
                    marker_color=colors_be,
                    text=[f"{m:.0f}mo" for m in be_sorted['months_to_payback']],
                    textposition='outside',
                ))
                fig.add_hline(y=TARGETS['break_even_months'], line_dash="dash",
                              line_color=COLORS['orange'],
                              annotation_text=f"Target: {TARGETS['break_even_months']}mo")
                fig = apply_brand_layout(fig, height=400, title="Months to Payback", show_legend=False)
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Contribution margin by store
                fig = go.Figure(go.Bar(
                    x=be_display['store_name'],
                    y=[cm * 100 for cm in be_display['contribution_margin']],
                    marker_color=CHART_COLORS[:len(be_display)],
                    text=[f"{cm*100:.1f}%" for cm in be_display['contribution_margin']],
                    textposition='outside',
                ))
                fig = apply_brand_layout(fig, height=400, title="Contribution Margin by Store",
                                         show_legend=False)
                fig.update_layout(yaxis_title="Contribution Margin %", xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)

    # P&L Summary
    st.markdown("")
    section_header("P&L Summary", "Profit and loss breakdown")

    profit = calculate_profitability(revenue_df, cost_df, store_filter)
    if profit:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fig = gauge_chart(profit['gross_margin_pct'], TARGETS['gross_margin_pct'] * 100,
                              "Gross Margin", max_val=100)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = gauge_chart(profit['net_margin_pct'], TARGETS['net_margin_pct'] * 100,
                              "Net Margin", max_val=30)
            st.plotly_chart(fig, use_container_width=True)
        with c3:
            fig = gauge_chart(profit['ebitda_margin_pct'], (TARGETS['net_margin_pct'] + 0.04) * 100,
                              "EBITDA Margin", max_val=30)
            st.plotly_chart(fig, use_container_width=True)
        with c4:
            fig = gauge_chart(profit['opex_ratio'], 55, "OpEx Ratio", max_val=80)
            st.plotly_chart(fig, use_container_width=True)

    # Cash Flow
    st.markdown("")
    section_header("Cash Flow Trend", "Operating cash flow over time")

    cf_df = calculate_cash_flow(revenue_df, cost_df, store_filter)
    if not cf_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cf_df['month'], y=cf_df['operating_cash_flow'],
            name='Monthly Operating CF',
            marker_color=[COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in cf_df['operating_cash_flow']],
        ))
        fig.add_trace(go.Scatter(
            x=cf_df['month'], y=cf_df['cumulative_cash_flow'],
            name='Cumulative CF', mode='lines+markers',
            line=dict(color=COLORS['orange'], width=3),
        ))
        fig = apply_brand_layout(fig, height=400)
        fig.update_layout(yaxis_title="EUR", barmode='relative')
        st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────
# TAB: REVENUE ANALYTICS
# ──────────────────────────────────────────────
def render_revenue_tab(data, store_filter):
    """Revenue deep dive: by category, channel, daypart, and store."""
    revenue_df = data['revenue']
    customer_df = data['customers']

    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
    if not customer_df.empty:
        customer_df = customer_df[customer_df['store_code'].isin(store_filter)]

    rev_metrics = calculate_revenue_metrics(revenue_df, customer_df, store_filter)

    if not rev_metrics:
        st.info("No revenue data available for the selected filters.")
        return

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Revenue", fmt_eur(rev_metrics['total_revenue']), color="orange")
    with c2:
        metric_card("Avg Monthly", fmt_eur(rev_metrics['avg_monthly_revenue']), color="teal")
    with c3:
        metric_card("Revenue/sqm/mo", f"\u20ac{rev_metrics['revenue_per_sqm_month']:,.0f}",
                     delta=rev_metrics['revenue_per_sqm_month'] - TARGETS['revenue_per_sqm_month'],
                     delta_suffix=" vs target", color="green")
    with c4:
        metric_card("Avg Ticket", f"\u20ac{rev_metrics['avg_transaction_value']:.2f}",
                     delta=rev_metrics['avg_transaction_value'] - TARGETS['avg_transaction_value'],
                     delta_suffix="", color="yellow")
    with c5:
        metric_card("3-Month Growth", fmt_pct(rev_metrics['growth_pct_3m']),
                     delta=rev_metrics['growth_pct_3m'], delta_suffix="%", color="orange")

    st.markdown("")

    # Revenue by category + by channel
    col1, col2 = st.columns(2)

    with col1:
        section_header("Revenue by Category")
        cat_data = revenue_df.groupby('category_label')['revenue'].sum().reset_index()
        cat_data = cat_data.sort_values('revenue', ascending=False)
        fig = donut_chart(cat_data['category_label'].tolist(), cat_data['revenue'].tolist(),
                          height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Revenue by Channel")
        ch_labels = {'dine_in': 'Dine-in', 'takeaway': 'Takeaway', 'delivery': 'Delivery', 'subscription': 'Subscription'}
        ch_data = revenue_df.copy()
        ch_data['channel_label'] = ch_data['channel'].map(ch_labels)
        ch_summary = ch_data.groupby('channel_label')['revenue'].sum().reset_index()
        ch_summary = ch_summary.sort_values('revenue', ascending=False)
        fig = donut_chart(ch_summary['channel_label'].tolist(), ch_summary['revenue'].tolist(),
                          height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Revenue by store
    st.markdown("")
    section_header("Revenue by Store", "Monthly revenue performance ranked by total")

    store_rev = revenue_df.groupby(['store_code', 'store_name'])['revenue'].sum().reset_index()
    store_rev = store_rev.sort_values('revenue', ascending=True)

    fig = go.Figure(go.Bar(
        x=store_rev['revenue'], y=store_rev['store_name'],
        orientation='h',
        marker=dict(color=store_rev['revenue'], colorscale=[[0, COLORS['teal']], [1, COLORS['orange']]]),
        text=[fmt_eur(v) for v in store_rev['revenue']],
        textposition='outside',
        hovertemplate='%{y}<br>\u20ac%{x:,.0f}<extra></extra>',
    ))
    fig = apply_brand_layout(fig, height=max(350, len(store_rev) * 28), show_legend=False)
    fig.update_layout(xaxis_title="Revenue (EUR)")
    st.plotly_chart(fig, use_container_width=True)

    # Monthly trend by category
    st.markdown("")
    section_header("Monthly Revenue by Category", "Stacked view of revenue composition over time")

    monthly_cat = revenue_df.groupby(['month', 'category_label'])['revenue'].sum().reset_index()
    monthly_cat = monthly_cat.sort_values('month')

    fig = px.bar(monthly_cat, x='month', y='revenue', color='category_label',
                 color_discrete_sequence=CHART_COLORS, barmode='stack')
    fig = apply_brand_layout(fig, height=400)
    fig.update_layout(yaxis_title="Revenue (EUR)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    # Daypart analysis
    if not customer_df.empty:
        st.markdown("")
        section_header("Customer Traffic by Daypart", "When are customers visiting?")

        daypart_cols = [c for c in customer_df.columns if c.startswith('daypart_')]
        if daypart_cols:
            dp_means = {c.replace('daypart_', '').replace('_pct', '').replace('_', ' ').title():
                        customer_df[c].mean() * 100 for c in daypart_cols}
            dp_df = pd.DataFrame({'Daypart': list(dp_means.keys()), 'Share': list(dp_means.values())})

            dp_colors = [COLORS['yellow'], COLORS['orange'], COLORS['teal'],
                         COLORS['green'], COLORS['charcoal']]

            fig = go.Figure(go.Bar(
                x=dp_df['Daypart'], y=dp_df['Share'],
                marker_color=dp_colors[:len(dp_df)],
                text=[f"{v:.1f}%" for v in dp_df['Share']],
                textposition='outside',
            ))
            fig = apply_brand_layout(fig, height=350, show_legend=False)
            fig.update_layout(yaxis_title="% of Traffic")
            st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────
# TAB: COST & EFFICIENCY
# ──────────────────────────────────────────────
def render_cost_tab(data, store_filter):
    """Cost structure analysis, labor efficiency, and inventory management."""
    revenue_df = data['revenue']
    cost_df = data['costs']
    labor_df = data['labor']
    inventory_df = data['inventory']

    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
    if not cost_df.empty:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]
    if not labor_df.empty:
        labor_df = labor_df[labor_df['store_code'].isin(store_filter)]
    if not inventory_df.empty:
        inventory_df = inventory_df[inventory_df['store_code'].isin(store_filter)]

    # Cost Structure
    section_header("Cost Structure", "All costs as percentage of revenue")

    cost_summary = calculate_cost_structure(cost_df, revenue_df, store_filter)
    if not cost_summary.empty:
        col1, col2 = st.columns(2)

        with col1:
            fig = donut_chart(
                cost_summary['cost_label'].tolist(),
                cost_summary['amount'].tolist(),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure(go.Bar(
                x=cost_summary['pct_of_revenue'],
                y=cost_summary['cost_label'],
                orientation='h',
                marker_color=CHART_COLORS[:len(cost_summary)],
                text=[f"{v:.1f}%" for v in cost_summary['pct_of_revenue']],
                textposition='outside',
            ))
            fig = apply_brand_layout(fig, height=380, show_legend=False)
            fig.update_layout(xaxis_title="% of Revenue")
            st.plotly_chart(fig, use_container_width=True)

    # Cost trend over time
    st.markdown("")
    section_header("Cost Trend", "Monthly cost evolution by category")

    if not cost_df.empty:
        monthly_costs = cost_df.groupby(['month', 'cost_label'])['amount'].sum().reset_index()
        monthly_costs = monthly_costs.sort_values('month')
        fig = px.area(monthly_costs, x='month', y='amount', color='cost_label',
                      color_discrete_sequence=CHART_COLORS)
        fig = apply_brand_layout(fig, height=400)
        fig.update_layout(yaxis_title="Cost (EUR)")
        st.plotly_chart(fig, use_container_width=True)

    # Labor Efficiency
    st.markdown("")
    section_header("Labor Efficiency", "Productivity and cost metrics")

    labor_metrics = calculate_labor_efficiency(labor_df, store_filter)
    if labor_metrics:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Revenue/Labor Hour", f"\u20ac{labor_metrics['revenue_per_labor_hour']:.0f}",
                        delta=labor_metrics['revenue_per_labor_hour'] - TARGETS['revenue_per_labor_hour'],
                        delta_suffix=" vs target", color="orange")
        with c2:
            metric_card("Labor Cost %", fmt_pct(labor_metrics['labor_cost_pct']),
                        delta=-labor_metrics['vs_target'],
                        delta_suffix="% vs target", color="teal")
        with c3:
            metric_card("Avg FTE/Store", f"{labor_metrics['avg_fte']:.1f}", color="green")
        with c4:
            metric_card("Rev/Employee/Mo", fmt_eur(labor_metrics['revenue_per_employee_month']), color="yellow")

        # Labor productivity by store
        if not labor_df.empty:
            st.markdown("")
            store_labor = labor_df.groupby('store_name').agg({
                'revenue_per_labor_hour': 'mean',
                'labor_cost_pct': 'mean',
            }).reset_index().sort_values('revenue_per_labor_hour', ascending=True)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=store_labor['revenue_per_labor_hour'], y=store_labor['store_name'],
                orientation='h', name='Rev/Labor Hr',
                marker_color=COLORS['orange'],
                text=[f"\u20ac{v:.0f}" for v in store_labor['revenue_per_labor_hour']],
                textposition='outside',
            ))
            fig.add_vline(x=TARGETS['revenue_per_labor_hour'], line_dash="dash",
                          line_color=COLORS['charcoal'],
                          annotation_text=f"Target: \u20ac{TARGETS['revenue_per_labor_hour']}")
            fig = apply_brand_layout(fig, height=max(300, len(store_labor) * 28), show_legend=False)
            fig.update_layout(xaxis_title="EUR per Labor Hour")
            st.plotly_chart(fig, use_container_width=True)

    # Inventory Management
    st.markdown("")
    section_header("Inventory Management", "Stock efficiency and waste control")

    inv_metrics = calculate_inventory_metrics(inventory_df, cost_df, store_filter)
    if inv_metrics:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Turnover Ratio", f"{inv_metrics['annualized_turnover']:.1f}x",
                        delta=inv_metrics['annualized_turnover'] - TARGETS['inventory_turnover'],
                        delta_suffix="x vs target", color="orange")
        with c2:
            metric_card("Avg Stock Value", fmt_eur(inv_metrics['avg_stock_value']), color="teal")
        with c3:
            metric_card("Waste Rate", fmt_pct(inv_metrics['waste_rate_pct']),
                        delta=-inv_metrics['waste_rate_pct'], delta_suffix="%", color="green")
        with c4:
            metric_card("Days Inventory", f"{inv_metrics['days_inventory_outstanding']:.0f} days", color="yellow")


# ──────────────────────────────────────────────
# TAB: CUSTOMERS
# ──────────────────────────────────────────────
def render_customers_tab(data, store_filter):
    """Customer analytics: acquisition, retention, lifetime value."""
    customer_df = data['customers']
    cost_df = data['costs']

    if not customer_df.empty:
        customer_df = customer_df[customer_df['store_code'].isin(store_filter)]
    if not cost_df.empty:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]

    cust_metrics = calculate_customer_metrics(customer_df, cost_df, store_filter)

    if not cust_metrics:
        st.info("No customer data available for the selected filters.")
        return

    section_header("Customer Overview", "Acquisition, retention, and lifetime value metrics")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("Total Customers", fmt_number(cust_metrics['total_customers']), color="orange")
    with c2:
        metric_card("Retention Rate", fmt_pct(cust_metrics['avg_retention_rate'] * 100),
                     delta=cust_metrics['avg_retention_rate'] * 100 - TARGETS['customer_retention_pct'] * 100,
                     delta_suffix="% vs target", color="green")
    with c3:
        metric_card("CLV", f"\u20ac{cust_metrics['customer_lifetime_value']:.0f}", color="teal")
    with c4:
        metric_card("CAC", f"\u20ac{cust_metrics['customer_acquisition_cost']:.2f}", color="yellow")
    with c5:
        metric_card("CLV:CAC Ratio", f"{cust_metrics['clv_cac_ratio']:.1f}x",
                     delta=cust_metrics['clv_cac_ratio'] - 3.0,
                     delta_suffix="x vs 3x target", color="orange")

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        section_header("New vs Returning Customers")
        fig = donut_chart(
            ['New Customers', 'Returning Customers'],
            [cust_metrics['new_customers'], cust_metrics['returning_customers']],
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Customer Trend")
        if not customer_df.empty:
            monthly_cust = customer_df.groupby('month').agg({
                'new_customers': 'sum',
                'returning_customers': 'sum',
            }).reset_index().sort_values('month')

            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly_cust['month'], y=monthly_cust['returning_customers'],
                                 name='Returning', marker_color=COLORS['teal']))
            fig.add_trace(go.Bar(x=monthly_cust['month'], y=monthly_cust['new_customers'],
                                 name='New', marker_color=COLORS['orange']))
            fig = apply_brand_layout(fig, height=350)
            fig.update_layout(barmode='stack', yaxis_title="Customers")
            st.plotly_chart(fig, use_container_width=True)

    # Customer metrics by store
    st.markdown("")
    section_header("Customer Metrics by Store")

    if not customer_df.empty:
        store_cust = customer_df.groupby('store_name').agg({
            'unique_customers': 'sum',
            'avg_transaction_value': 'mean',
            'retention_rate': 'mean',
            'total_transactions': 'sum',
        }).reset_index()
        store_cust['visits_per_customer'] = (
            store_cust['total_transactions'] / store_cust['unique_customers']
        ).round(1)

        st.dataframe(
            store_cust.sort_values('unique_customers', ascending=False),
            use_container_width=True, hide_index=True,
            column_config={
                'store_name': 'Store',
                'unique_customers': st.column_config.NumberColumn('Customers', format="%d"),
                'avg_transaction_value': st.column_config.NumberColumn('Avg Ticket', format='\u20ac%.2f'),
                'retention_rate': st.column_config.NumberColumn('Retention', format='%.1f%%'),
                'total_transactions': st.column_config.NumberColumn('Transactions', format="%d"),
                'visits_per_customer': st.column_config.NumberColumn('Visits/Customer', format="%.1f"),
            },
        )


# ──────────────────────────────────────────────
# TAB: CAPEX TRACKING
# ──────────────────────────────────────────────
def render_capex_tab(data, store_filter, selected_accounts, selected_years):
    """Original CAPEX budget tracking with brand styling."""
    capex_df = data['capex']
    has_odoo = data['has_odoo']
    db, uid, password = data['db'], data['uid'], data['password']
    budgets = load_budgets()
    budget_key = f"capex_{'-'.join(sorted(selected_accounts))}"

    if capex_df.empty:
        st.info("No CAPEX data available for the selected criteria.")
        return

    filtered_df = capex_df[capex_df['store_code'].isin(store_filter)]

    # Summary metrics
    section_header("CAPEX Overview", "Capital expenditure tracking across stores")

    total_actual = filtered_df['amount'].sum()
    total_budget = sum(budgets.get(budget_key, {}).get(store, 0) for store in store_filter)
    variance = total_budget - total_actual
    variance_pct = (variance / total_budget * 100) if total_budget > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("CAPEX Budget", fmt_eur(total_budget), color="teal")
    with c2:
        metric_card("Actual Spent", fmt_eur(total_actual), color="orange")
    with c3:
        metric_card("Variance", fmt_eur(variance),
                     delta=variance_pct, delta_suffix="%", color="green" if variance >= 0 else "red")
    with c4:
        num_stores = filtered_df['store_code'].nunique()
        metric_card("Active Stores", str(num_stores), color="yellow")

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        section_header("CAPEX per Store")
        store_summary = filtered_df.groupby(['store_code', 'store_name'])['amount'].sum().reset_index()
        store_summary = store_summary.sort_values('amount', ascending=True)

        fig = go.Figure(go.Bar(
            x=store_summary['amount'], y=store_summary['store_name'],
            orientation='h',
            marker=dict(color=store_summary['amount'],
                        colorscale=[[0, COLORS['teal']], [1, COLORS['orange']]]),
            text=[fmt_eur(v) for v in store_summary['amount']],
            textposition='outside',
        ))
        fig = apply_brand_layout(fig, height=max(300, len(store_summary) * 28), show_legend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Monthly CAPEX Trend")
        monthly = filtered_df.groupby('month')['amount'].sum().reset_index().sort_values('month')
        fig = area_chart(monthly, x='month', y='amount', height=max(300, len(store_summary) * 28),
                         color_sequence=[COLORS['orange']])
        st.plotly_chart(fig, use_container_width=True)

    # Account breakdown
    st.markdown("")
    section_header("CAPEX by Account Category")
    account_summary = filtered_df.groupby('account_label')['amount'].sum().reset_index()
    account_summary = account_summary.sort_values('amount', ascending=False)

    col1, col2 = st.columns(2)
    with col1:
        fig = donut_chart(account_summary['account_label'].tolist(),
                          account_summary['amount'].tolist(), height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure(go.Bar(
            x=account_summary['account_label'], y=account_summary['amount'],
            marker_color=CHART_COLORS[:len(account_summary)],
            text=[fmt_eur(v) for v in account_summary['amount']],
            textposition='outside',
        ))
        fig = apply_brand_layout(fig, height=350, show_legend=False)
        fig.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    # Budget vs Actual comparison
    st.markdown("")
    section_header("Budget vs Actual by Store")

    comparison_data = []
    for store_code in store_filter:
        if store_code in STORE_LOCATIONS:
            actual = filtered_df[filtered_df['store_code'] == store_code]['amount'].sum()
            budget = budgets.get(budget_key, {}).get(store_code, 0)
            if actual > 0 or budget > 0:
                comparison_data.append({
                    'Store': STORE_LOCATIONS[store_code]['name'],
                    'Budget': budget, 'Actual': actual,
                    'Variance': budget - actual,
                })

    if comparison_data:
        comp_df = pd.DataFrame(comparison_data).sort_values('Actual', ascending=False)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Budget', x=comp_df['Store'], y=comp_df['Budget'],
                             marker_color=COLORS['grey_light']))
        fig.add_trace(go.Bar(name='Actual', x=comp_df['Store'], y=comp_df['Actual'],
                             marker_color=COLORS['orange']))
        fig = apply_brand_layout(fig, height=400)
        fig.update_layout(barmode='group', xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    # Budget Management Section
    st.markdown("")
    section_header("Budget Management", "Set CAPEX budgets per store")

    if budget_key not in budgets:
        budgets[budget_key] = data.get('budgets', {}).copy()

    col1, col2 = st.columns(2)
    stores_list = [(c, i) for c, i in STORE_LOCATIONS.items()]
    half = len(stores_list) // 2

    with col1:
        for code, info in stores_list[:half]:
            current = budgets[budget_key].get(code, 0)
            new_val = st.number_input(f"{info['name']} ({code})", min_value=0,
                                       value=int(current), step=1000, key=f"budget_{code}")
            budgets[budget_key][code] = new_val

    with col2:
        for code, info in stores_list[half:]:
            current = budgets[budget_key].get(code, 0)
            new_val = st.number_input(f"{info['name']} ({code})", min_value=0,
                                       value=int(current), step=1000, key=f"budget_{code}")
            budgets[budget_key][code] = new_val

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        if st.button("Apply 50K Template", use_container_width=True):
            for code in STORE_LOCATIONS:
                budgets[budget_key][code] = 50000
            save_budgets(budgets)
            st.rerun()
    with bc2:
        if st.button("Apply 25K Template", use_container_width=True):
            for code in STORE_LOCATIONS:
                budgets[budget_key][code] = 25000
            save_budgets(budgets)
            st.rerun()
    with bc3:
        if st.button("Clear All Budgets", use_container_width=True):
            budgets[budget_key] = {}
            save_budgets(budgets)
            st.rerun()
    with bc4:
        if st.button("Save Budgets", type="primary", use_container_width=True):
            save_budgets(budgets)
            st.success("Budgets saved!")

    # Detailed transaction table
    st.markdown("")
    section_header("CAPEX Transactions")

    display_df = filtered_df[['date', 'store_name', 'account_label', 'amount', 'description', 'move_name']].sort_values('date', ascending=False)
    st.dataframe(
        display_df, use_container_width=True, hide_index=True,
        column_config={
            'date': 'Date', 'store_name': 'Store', 'account_label': 'Account',
            'amount': st.column_config.NumberColumn('Amount', format='\u20ac%.2f'),
            'description': 'Description', 'move_name': 'Invoice/Entry',
        },
    )

    # Invoice detail viewer (Odoo only)
    if has_odoo:
        st.markdown("")
        section_header("Invoice Detail Viewer")
        moves = filtered_df[filtered_df['move_id'].notna()][['move_id', 'move_name']].drop_duplicates()
        if not moves.empty:
            move_opts = {f"{r['move_name']} (ID: {int(r['move_id'])})": int(r['move_id'])
                         for _, r in moves.iterrows() if r['move_id']}
            if move_opts:
                sel = st.selectbox("Select invoice/entry:", ["-- Select --"] + list(move_opts.keys()))
                if sel != "-- Select --":
                    with st.expander(f"Details: {sel}", expanded=True):
                        render_invoice_popup(db, uid, password, move_opts[sel], sel)

    # CSV Export
    csv = filtered_df.to_csv(index=False)
    years_str = '-'.join(str(y) for y in selected_years)
    st.download_button("Download CAPEX CSV", data=csv,
                       file_name=f"wakuli_capex_{years_str}.csv", mime="text/csv")


# ──────────────────────────────────────────────
# TAB: HR / LABOR
# ──────────────────────────────────────────────
def render_hr_tab(data, store_filter):
    """HR & Labor analytics — headcount, FTE, salary costs, efficiency.

    Pulls from Nmbrs when connected, otherwise uses demo labor data.
    Shows per-company breakdowns when multiple Nmbrs companies are configured.
    """
    labor_df = data['labor']
    revenue_df = data['revenue']
    data_sources = data.get('data_sources', {})
    labor_source = data_sources.get('labor', 'demo')

    if not labor_df.empty:
        labor_df = labor_df[labor_df['store_code'].isin(store_filter)]
    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]

    # Source indicator
    if labor_source == 'nmbrs':
        companies = NMBRS_CONFIG.get("companies", {})
        company_names = ', '.join(companies.values()) if companies else "Nmbrs"
        st.success(f"Live HR data from Nmbrs ({company_names})")
    else:
        st.info("Showing demo labor data. Connect Nmbrs in the Settings tab for real HR/payroll data.")

    # ── TOP-LINE KPIs ──
    section_header("Workforce Overview", "Headcount, FTE, and labor cost summary")

    labor_metrics = calculate_labor_efficiency(labor_df, store_filter)
    if labor_metrics:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            total_headcount = labor_df['store_code'].nunique() if labor_df.empty else 0
            # Calculate actual headcount from FTE data
            if not labor_df.empty:
                latest_month = labor_df[['year', 'month']].drop_duplicates().sort_values(
                    ['year', 'month']).iloc[-1]
                latest_labor = labor_df[
                    (labor_df['year'] == latest_month['year']) &
                    (labor_df['month'] == latest_month['month'])
                ]
                total_fte = latest_labor['fte_count'].sum()
            else:
                total_fte = 0
            metric_card("Total FTE", f"{total_fte:.1f}", color="orange")
        with c2:
            metric_card("Total Labor Cost", fmt_eur(labor_metrics['total_labor_cost']),
                        color="teal")
        with c3:
            metric_card("Labor Cost %", fmt_pct(labor_metrics['labor_cost_pct']),
                        delta=-labor_metrics['vs_target'],
                        delta_suffix="% vs target", color="green")
        with c4:
            metric_card("Rev/Labor Hour", f"\u20ac{labor_metrics['revenue_per_labor_hour']:.0f}",
                        delta=labor_metrics['revenue_per_labor_hour'] - TARGETS['revenue_per_labor_hour'],
                        delta_suffix=" vs target", color="yellow")
        with c5:
            metric_card("Rev/Employee/Mo", fmt_eur(labor_metrics['revenue_per_employee_month']),
                        color="orange")

    if labor_df.empty:
        st.info("No labor data available for the selected stores.")
        return

    st.markdown("")

    # ── HEADCOUNT & FTE BY STORE ──
    col1, col2 = st.columns(2)

    with col1:
        section_header("FTE by Store", "Full-time equivalents per location")
        if not labor_df.empty:
            # Use latest month's snapshot
            latest_month = labor_df[['year', 'month']].drop_duplicates().sort_values(
                ['year', 'month']).iloc[-1]
            latest_labor = labor_df[
                (labor_df['year'] == latest_month['year']) &
                (labor_df['month'] == latest_month['month'])
            ]
            store_fte = latest_labor.groupby('store_name')['fte_count'].sum().reset_index()
            store_fte = store_fte.sort_values('fte_count', ascending=True)

            fig = go.Figure(go.Bar(
                x=store_fte['fte_count'], y=store_fte['store_name'],
                orientation='h',
                marker=dict(color=store_fte['fte_count'],
                            colorscale=[[0, COLORS['teal']], [1, COLORS['orange']]]),
                text=[f"{v:.1f}" for v in store_fte['fte_count']],
                textposition='outside',
            ))
            fig = apply_brand_layout(fig, height=max(300, len(store_fte) * 28), show_legend=False)
            fig.update_layout(xaxis_title="FTE")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Monthly Labor Cost by Store", "Total employer cost per location")
        if not labor_df.empty:
            store_cost = latest_labor.groupby('store_name')['labor_cost'].sum().reset_index()
            store_cost = store_cost.sort_values('labor_cost', ascending=True)

            fig = go.Figure(go.Bar(
                x=store_cost['labor_cost'], y=store_cost['store_name'],
                orientation='h',
                marker=dict(color=store_cost['labor_cost'],
                            colorscale=[[0, COLORS['orange']], [1, COLORS['red']]]),
                text=[fmt_eur(v) for v in store_cost['labor_cost']],
                textposition='outside',
            ))
            fig = apply_brand_layout(fig, height=max(300, len(store_cost) * 28), show_legend=False)
            fig.update_layout(xaxis_title="Monthly Cost (EUR)")
            st.plotly_chart(fig, use_container_width=True)

    # ── LABOR COST TREND ──
    st.markdown("")
    section_header("Labor Cost Trend", "Monthly total labor cost over time")

    monthly_labor = labor_df.groupby(['year', 'month']).agg(
        total_cost=('labor_cost', 'sum'),
        total_fte=('fte_count', 'sum'),
        total_revenue=('revenue', 'sum'),
    ).reset_index()
    monthly_labor['period'] = monthly_labor['year'].astype(str) + '-' + monthly_labor['month'].astype(str).str.zfill(2)
    monthly_labor['labor_pct'] = (monthly_labor['total_cost'] / monthly_labor['total_revenue'] * 100).round(1)
    monthly_labor = monthly_labor.sort_values('period')

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_labor['period'], y=monthly_labor['total_cost'],
        name='Labor Cost', marker_color=COLORS['orange'],
        text=[fmt_eur(v) for v in monthly_labor['total_cost']],
        textposition='outside',
    ))
    fig.add_trace(go.Scatter(
        x=monthly_labor['period'], y=monthly_labor['labor_pct'],
        name='Labor %', yaxis='y2',
        line=dict(color=COLORS['teal'], width=3),
        mode='lines+markers',
    ))
    fig = apply_brand_layout(fig, height=400)
    fig.update_layout(
        yaxis_title="Labor Cost (EUR)",
        yaxis2=dict(title="Labor %", overlaying='y', side='right',
                    showgrid=False, ticksuffix='%'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    # Target line for labor %
    fig.add_hline(y=TARGETS['labor_cost_pct'] * 100, line_dash="dash",
                  line_color=COLORS['charcoal'], yref='y2',
                  annotation_text=f"Target: {TARGETS['labor_cost_pct']*100:.0f}%")
    st.plotly_chart(fig, use_container_width=True)

    # ── LABOR EFFICIENCY BY STORE ──
    st.markdown("")
    section_header("Labor Efficiency by Store", "Revenue per labor hour and labor cost % per store")

    col1, col2 = st.columns(2)

    with col1:
        store_efficiency = labor_df.groupby('store_name').agg({
            'revenue_per_labor_hour': 'mean',
        }).reset_index().sort_values('revenue_per_labor_hour', ascending=True)

        colors = [COLOR_POSITIVE if v >= TARGETS['revenue_per_labor_hour']
                  else COLOR_WARNING if v >= TARGETS['revenue_per_labor_hour'] * 0.8
                  else COLOR_NEGATIVE
                  for v in store_efficiency['revenue_per_labor_hour']]

        fig = go.Figure(go.Bar(
            x=store_efficiency['revenue_per_labor_hour'], y=store_efficiency['store_name'],
            orientation='h',
            marker_color=colors,
            text=[f"\u20ac{v:.0f}" for v in store_efficiency['revenue_per_labor_hour']],
            textposition='outside',
        ))
        fig.add_vline(x=TARGETS['revenue_per_labor_hour'], line_dash="dash",
                      line_color=COLORS['charcoal'],
                      annotation_text=f"Target: \u20ac{TARGETS['revenue_per_labor_hour']}")
        fig = apply_brand_layout(fig, height=max(300, len(store_efficiency) * 28), show_legend=False)
        fig.update_layout(xaxis_title="Revenue per Labor Hour (EUR)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        store_labor_pct = labor_df.groupby('store_name').agg({
            'labor_cost_pct': 'mean',
        }).reset_index()
        store_labor_pct['labor_cost_pct'] = store_labor_pct['labor_cost_pct'] * 100
        store_labor_pct = store_labor_pct.sort_values('labor_cost_pct', ascending=True)

        target_pct = TARGETS['labor_cost_pct'] * 100
        colors = [COLOR_POSITIVE if v <= target_pct
                  else COLOR_WARNING if v <= target_pct * 1.1
                  else COLOR_NEGATIVE
                  for v in store_labor_pct['labor_cost_pct']]

        fig = go.Figure(go.Bar(
            x=store_labor_pct['labor_cost_pct'], y=store_labor_pct['store_name'],
            orientation='h',
            marker_color=colors,
            text=[f"{v:.1f}%" for v in store_labor_pct['labor_cost_pct']],
            textposition='outside',
        ))
        fig.add_vline(x=target_pct, line_dash="dash",
                      line_color=COLORS['charcoal'],
                      annotation_text=f"Target: {target_pct:.0f}%")
        fig = apply_brand_layout(fig, height=max(300, len(store_labor_pct) * 28), show_legend=False)
        fig.update_layout(xaxis_title="Labor Cost % of Revenue")
        st.plotly_chart(fig, use_container_width=True)

    # ── FTE TREND ──
    st.markdown("")
    section_header("FTE Trend", "Total FTE across all stores over time")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_labor['period'], y=monthly_labor['total_fte'],
        mode='lines+markers+text',
        line=dict(color=COLORS['orange'], width=3),
        marker=dict(size=8),
        text=[f"{v:.1f}" for v in monthly_labor['total_fte']],
        textposition='top center',
        name='Total FTE',
    ))
    fig = apply_brand_layout(fig, height=350, show_legend=False)
    fig.update_layout(yaxis_title="Total FTE")
    st.plotly_chart(fig, use_container_width=True)

    # ── STORE DETAIL TABLE ──
    st.markdown("")
    section_header("Store Labor Detail", "Complete labor metrics per store")

    store_detail = labor_df.groupby(['store_code', 'store_name']).agg(
        avg_fte=('fte_count', 'mean'),
        total_labor_cost=('labor_cost', 'sum'),
        total_revenue=('revenue', 'sum'),
        avg_rev_per_hour=('revenue_per_labor_hour', 'mean'),
        avg_labor_pct=('labor_cost_pct', 'mean'),
    ).reset_index()
    store_detail['avg_labor_pct'] = store_detail['avg_labor_pct'] * 100

    st.dataframe(
        store_detail.sort_values('total_labor_cost', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            'store_code': 'Code',
            'store_name': 'Store',
            'avg_fte': st.column_config.NumberColumn('Avg FTE', format='%.1f'),
            'total_labor_cost': st.column_config.NumberColumn('Total Labor Cost', format='\u20ac%,.0f'),
            'total_revenue': st.column_config.NumberColumn('Total Revenue', format='\u20ac%,.0f'),
            'avg_rev_per_hour': st.column_config.NumberColumn('Rev/Labor Hr', format='\u20ac%.0f'),
            'avg_labor_pct': st.column_config.NumberColumn('Labor %', format='%.1f%%'),
        },
    )

    # ── NMBRS EMPLOYEE DETAIL (only when live data) ──
    if labor_source == 'nmbrs':
        st.markdown("")
        section_header("Employee Detail", "Live employee data from Nmbrs (across all companies)")

        emp_df = fetch_nmbrs_employees()
        if not emp_df.empty:
            emp_df = emp_df[emp_df['store_code'].isin(store_filter)]

            # Company breakdown
            if 'nmbrs_company' in emp_df.columns and emp_df['nmbrs_company'].nunique() > 1:
                company_summary = emp_df.groupby('nmbrs_company').agg(
                    headcount=('employee_id', 'count'),
                    total_fte=('fte_factor', 'sum'),
                ).reset_index()

                fig = go.Figure()
                for i, (_, row) in enumerate(company_summary.iterrows()):
                    fig.add_trace(go.Bar(
                        x=[row['nmbrs_company']],
                        y=[row['total_fte']],
                        name=row['nmbrs_company'],
                        text=[f"{row['total_fte']:.1f} FTE\n({int(row['headcount'])} employees)"],
                        textposition='outside',
                        marker_color=CHART_COLORS[i % len(CHART_COLORS)],
                    ))
                fig = apply_brand_layout(fig, height=300, show_legend=True)
                fig.update_layout(yaxis_title="FTE", showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

            # Employee table
            display_cols = ['name', 'store_name', 'department', 'job_title', 'fte_factor', 'start_date']
            if 'nmbrs_company' in emp_df.columns and emp_df['nmbrs_company'].nunique() > 1:
                display_cols.append('nmbrs_company')

            col_config = {
                'name': 'Name',
                'store_name': 'Store',
                'department': 'Department',
                'job_title': 'Job Title',
                'fte_factor': st.column_config.NumberColumn('FTE', format='%.2f'),
                'start_date': 'Start Date',
                'nmbrs_company': 'Company',
            }

            st.dataframe(
                emp_df[display_cols].sort_values(['store_name', 'name']),
                use_container_width=True, hide_index=True,
                column_config=col_config,
            )


# ──────────────────────────────────────────────
# TAB: IMPACT DASHBOARD
# ──────────────────────────────────────────────
def render_impact_tab(data):
    """Wakuli mission-aligned impact metrics and sourcing visualization."""
    impact_df = data['impact']

    if impact_df.empty:
        st.info("No impact data available.")
        return

    impact = calculate_impact_summary(impact_df)

    # Hero impact section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #004E64 0%, #25A18E 100%);
                padding: 2rem; border-radius: 16px; margin-bottom: 1.5rem;
                box-shadow: 0 4px 20px rgba(37, 161, 142, 0.3);">
        <div style="text-align: center;">
            <div style="font-family: Poppins; font-size: 1.5rem; font-weight: 800; color: white;">
                Impact Per Cup
            </div>
            <div style="font-family: Poppins; font-size: 0.9rem; color: rgba(255,255,255,0.7); margin-top: 4px;">
                Every cup of Wakuli coffee directly supports farmers and communities
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Impact KPIs
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        impact_card(f"{impact.get('current_farmers_supported', 0):,}", "Farmers Supported")
    with c2:
        impact_card(fmt_eur(impact.get('total_premium_paid', 0)), "Premium to Farmers")
    with c3:
        impact_card(f"{impact.get('avg_direct_trade_pct', 0):.0f}", "Direct Trade", suffix="%")
    with c4:
        impact_card(f"{impact.get('total_kg_sourced', 0):,.0f}", "KG Coffee Sourced")
    with c5:
        impact_card(f"{impact.get('avg_compostable_pct', 0):.0f}", "Compostable Pkg", suffix="%")
    with c6:
        impact_card(f"\u20ac{impact.get('premium_per_cup', 0):.3f}", "Premium Per Cup")

    st.markdown("")

    col1, col2 = st.columns(2)

    with col1:
        section_header("Farmer Premium Trend", "Price premium paid above market rate")
        monthly_impact = impact_df.sort_values('month')
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_impact['month'], y=monthly_impact['wakuli_price_per_kg'],
            name='Wakuli Price', mode='lines+markers',
            line=dict(color=COLORS['orange'], width=3),
        ))
        fig.add_trace(go.Scatter(
            x=monthly_impact['month'], y=monthly_impact['market_price_per_kg'],
            name='Market Price', mode='lines+markers',
            line=dict(color=COLORS['grey_medium'], width=2, dash='dash'),
        ))
        fig = apply_brand_layout(fig, height=380)
        fig.update_layout(yaxis_title="EUR per KG")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        section_header("Coffee Sourced Monthly", "KG of directly traded coffee")
        fig = go.Figure(go.Bar(
            x=monthly_impact['month'], y=monthly_impact['kg_coffee_sourced'],
            marker_color=COLORS['green'],
            text=[f"{v:,.0f}" for v in monthly_impact['kg_coffee_sourced']],
            textposition='outside',
        ))
        fig = apply_brand_layout(fig, height=380, show_legend=False)
        fig.update_layout(yaxis_title="KG")
        st.plotly_chart(fig, use_container_width=True)

    # Sourcing origins map
    st.markdown("")
    section_header("Coffee Sourcing Origins", "Where Wakuli coffee comes from")

    origins_df = pd.DataFrame(SOURCING_ORIGINS)
    fig = px.scatter_geo(
        origins_df,
        lat='lat', lon='lon',
        size='farmers', color='pct',
        hover_name='country',
        hover_data={'region': True, 'farmers': True, 'pct': ':.0%',
                    'lat': False, 'lon': False},
        color_continuous_scale=[[0, COLORS['teal']], [1, COLORS['orange']]],
        size_max=30,
        projection='natural earth',
    )
    fig.update_layout(
        height=450,
        geo=dict(
            showland=True, landcolor=COLORS['cream'],
            showocean=True, oceancolor='#E3F2FD',
            showcountries=True, countrycolor=COLORS['grey_light'],
            lataxis=dict(range=[-35, 25]),
            lonaxis=dict(range=[-100, 120]),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Share"),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sourcing table
    st.dataframe(
        origins_df[['country', 'region', 'farmers', 'pct']].sort_values('pct', ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            'country': 'Country', 'region': 'Region',
            'farmers': st.column_config.NumberColumn('Farmers'),
            'pct': st.column_config.NumberColumn('Share', format='%.0f%%'),
        },
    )

    # Sustainability trend
    st.markdown("")
    section_header("Sustainability Progress", "CO2 reduction and packaging improvements")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Scatter(
            x=monthly_impact['month'], y=monthly_impact['co2_per_cup_grams'],
            mode='lines+markers', line=dict(color=COLORS['green'], width=3),
            fill='tozeroy', fillcolor=f"rgba(37, 161, 142, 0.15)",
        ))
        fig = apply_brand_layout(fig, height=350, show_legend=False)
        fig.update_layout(yaxis_title="Grams CO2 per Cup", title=dict(text="CO2 per Cup Trend"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure(go.Scatter(
            x=monthly_impact['month'],
            y=[p * 100 for p in monthly_impact['compostable_packaging_pct']],
            mode='lines+markers', line=dict(color=COLORS['teal'], width=3),
            fill='tozeroy', fillcolor=f"rgba(0, 78, 100, 0.15)",
        ))
        fig = apply_brand_layout(fig, height=350, show_legend=False)
        fig.update_layout(yaxis_title="% Compostable", title=dict(text="Compostable Packaging"))
        st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────
# TAB: STORE MAP
# ──────────────────────────────────────────────
def render_map_tab(data, store_filter):
    """Interactive store map with performance overlay."""
    revenue_df = data['revenue']
    capex_df = data['capex']
    budgets = load_budgets()

    section_header("Store Locations", "Wakuli coffee bars across the Netherlands")

    map_data = []
    for code, info in STORE_LOCATIONS.items():
        if code == "OOH" or 'lat' not in info:
            continue
        rev = revenue_df[revenue_df['store_code'] == code]['revenue'].sum() if not revenue_df.empty else 0
        capex = capex_df[capex_df['store_code'] == code]['amount'].sum() if not capex_df.empty else 0
        map_data.append({
            'lat': info['lat'], 'lon': info['lon'],
            'name': info['name'], 'code': code, 'city': info['city'],
            'address': info['address'], 'sqm': info.get('sqm', 0),
            'revenue': rev, 'capex': capex,
            'size': max(rev / 5000, 12),
        })

    map_df = pd.DataFrame(map_data)

    fig = px.scatter_mapbox(
        map_df, lat='lat', lon='lon', size='size',
        color='revenue', color_continuous_scale=[[0, COLORS['teal']], [1, COLORS['orange']]],
        hover_name='name',
        hover_data={
            'city': True, 'address': True, 'sqm': True,
            'revenue': ':\u20ac,.0f', 'capex': ':\u20ac,.0f',
            'lat': False, 'lon': False, 'size': False,
        },
        zoom=6.5, center={'lat': 52.1, 'lon': 5.0},
    )
    fig.update_layout(
        mapbox_style='carto-positron', height=550,
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        coloraxis_colorbar=dict(title="Revenue"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Store directory
    st.markdown("")
    section_header("Store Directory")

    cols = st.columns(3)
    store_items = [(c, i) for c, i in STORE_LOCATIONS.items() if c != "OOH"]
    for idx, (code, info) in enumerate(store_items):
        with cols[idx % 3]:
            rev = revenue_df[revenue_df['store_code'] == code]['revenue'].sum() if not revenue_df.empty else 0
            capex = capex_df[capex_df['store_code'] == code]['amount'].sum() if not capex_df.empty else 0
            st.markdown(f"""
            <div class="store-card">
                <strong>{info['name']}</strong> ({code})<br>
                <span style="font-size: 0.85rem; color: #666;">{info['address']}, {info['city']}</span><br>
                <span class="store-amount">Revenue: {fmt_eur(rev)}</span> |
                <span style="color: #004E64; font-weight: 600;">CAPEX: {fmt_eur(capex)}</span>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# TAB: COMPARATIVE ANALYSIS
# ──────────────────────────────────────────────
def render_comparative_tab(data, store_filter, selected_years):
    """Store benchmarking and period-over-period comparison."""
    revenue_df = data['revenue']
    cost_df = data['costs']
    customer_df = data['customers']
    labor_df = data['labor']

    if not revenue_df.empty:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
    if not cost_df.empty:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]

    # Store Performance Benchmarks
    section_header("Store Performance Ranking", "Compare stores across key metrics")

    prof_by_store = calculate_profitability_by_store(revenue_df, cost_df)
    if not prof_by_store.empty:
        prof_by_store = prof_by_store[prof_by_store['store_code'].isin(store_filter)]

        # Scorecard
        display = prof_by_store[['store_name', 'total_revenue', 'gross_margin_pct',
                                  'net_margin_pct', 'ebitda', 'opex_ratio']].copy()
        display = display.sort_values('total_revenue', ascending=False)

        st.dataframe(
            display, use_container_width=True, hide_index=True,
            column_config={
                'store_name': 'Store',
                'total_revenue': st.column_config.NumberColumn('Revenue', format='\u20ac%.0f'),
                'gross_margin_pct': st.column_config.NumberColumn('Gross Margin %', format='%.1f%%'),
                'net_margin_pct': st.column_config.NumberColumn('Net Margin %', format='%.1f%%'),
                'ebitda': st.column_config.NumberColumn('EBITDA', format='\u20ac%.0f'),
                'opex_ratio': st.column_config.NumberColumn('OpEx Ratio %', format='%.1f%%'),
            },
        )

        st.markdown("")

        # Margin comparison chart
        col1, col2 = st.columns(2)

        with col1:
            section_header("Gross Margin by Store")
            sorted_gm = prof_by_store.sort_values('gross_margin_pct', ascending=True)
            colors_gm = [COLOR_POSITIVE if v >= TARGETS['gross_margin_pct'] * 100 else COLOR_WARNING
                         for v in sorted_gm['gross_margin_pct']]
            fig = go.Figure(go.Bar(
                x=sorted_gm['gross_margin_pct'], y=sorted_gm['store_name'],
                orientation='h', marker_color=colors_gm,
                text=[f"{v:.1f}%" for v in sorted_gm['gross_margin_pct']],
                textposition='outside',
            ))
            fig.add_vline(x=TARGETS['gross_margin_pct'] * 100, line_dash="dash",
                          line_color=COLORS['charcoal'],
                          annotation_text=f"Target: {TARGETS['gross_margin_pct']*100}%")
            fig = apply_brand_layout(fig, height=max(300, len(sorted_gm) * 28), show_legend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            section_header("Net Margin by Store")
            sorted_nm = prof_by_store.sort_values('net_margin_pct', ascending=True)
            colors_nm = [COLOR_POSITIVE if v >= TARGETS['net_margin_pct'] * 100 else COLOR_NEGATIVE
                         for v in sorted_nm['net_margin_pct']]
            fig = go.Figure(go.Bar(
                x=sorted_nm['net_margin_pct'], y=sorted_nm['store_name'],
                orientation='h', marker_color=colors_nm,
                text=[f"{v:.1f}%" for v in sorted_nm['net_margin_pct']],
                textposition='outside',
            ))
            fig.add_vline(x=TARGETS['net_margin_pct'] * 100, line_dash="dash",
                          line_color=COLORS['charcoal'],
                          annotation_text=f"Target: {TARGETS['net_margin_pct']*100}%")
            fig = apply_brand_layout(fig, height=max(300, len(sorted_nm) * 28), show_legend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Year-over-Year comparison
    if len(selected_years) > 1:
        st.markdown("")
        section_header("Year-over-Year Comparison", "How performance changed across years")

        yearly_rev = revenue_df.groupby('year')['revenue'].sum().reset_index()
        yearly_rev['year'] = yearly_rev['year'].astype(str)

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(go.Bar(
                x=yearly_rev['year'], y=yearly_rev['revenue'],
                marker_color=CHART_COLORS[:len(yearly_rev)],
                text=[fmt_eur(v) for v in yearly_rev['revenue']],
                textposition='outside',
            ))
            fig = apply_brand_layout(fig, height=380, title="Revenue by Year", show_legend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            if not cost_df.empty:
                yearly_costs = cost_df.groupby('year')['amount'].sum().reset_index()
                yearly_costs['year'] = yearly_costs['year'].astype(str)
                yearly_merged = yearly_rev.merge(yearly_costs, on='year', how='outer').fillna(0)
                yearly_merged['profit'] = yearly_merged['revenue'] - yearly_merged['amount']

                fig = go.Figure()
                fig.add_trace(go.Bar(name='Revenue', x=yearly_merged['year'],
                                     y=yearly_merged['revenue'], marker_color=COLORS['orange']))
                fig.add_trace(go.Bar(name='Costs', x=yearly_merged['year'],
                                     y=yearly_merged['amount'], marker_color=COLORS['teal']))
                fig.add_trace(go.Scatter(name='Profit', x=yearly_merged['year'],
                                          y=yearly_merged['profit'],
                                          mode='lines+markers+text',
                                          text=[fmt_eur(v) for v in yearly_merged['profit']],
                                          textposition='top center',
                                          line=dict(color=COLORS['green'], width=3)))
                fig = apply_brand_layout(fig, height=380, title="Revenue vs Costs by Year")
                fig.update_layout(barmode='group')
                st.plotly_chart(fig, use_container_width=True)

        # Same-store sales growth
        st.markdown("")
        section_header("Same-Store Revenue Growth", "Year-over-year change per store")

        if len(selected_years) >= 2:
            yr1, yr2 = sorted(selected_years)[-2], sorted(selected_years)[-1]
            rev_yr1 = revenue_df[revenue_df['year'] == yr1].groupby('store_name')['revenue'].sum()
            rev_yr2 = revenue_df[revenue_df['year'] == yr2].groupby('store_name')['revenue'].sum()

            common_stores = set(rev_yr1.index) & set(rev_yr2.index)
            if common_stores:
                growth_data = []
                for store in common_stores:
                    g = ((rev_yr2[store] - rev_yr1[store]) / rev_yr1[store] * 100) if rev_yr1[store] > 0 else 0
                    growth_data.append({'Store': store, 'Growth': g})
                growth_df = pd.DataFrame(growth_data).sort_values('Growth', ascending=True)

                colors_g = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in growth_df['Growth']]
                fig = go.Figure(go.Bar(
                    x=growth_df['Growth'], y=growth_df['Store'],
                    orientation='h', marker_color=colors_g,
                    text=[f"{v:+.1f}%" for v in growth_df['Growth']],
                    textposition='outside',
                ))
                fig.add_vline(x=0, line_color=COLORS['charcoal'], line_width=1)
                fig = apply_brand_layout(fig, height=max(300, len(growth_df) * 28), show_legend=False,
                                         title=f"Same-Store Growth: {yr1} to {yr2}")
                st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────
# TAB: SETTINGS & DIAGNOSTICS
# ──────────────────────────────────────────────
def render_settings_tab(data, selected_years):
    """Account Explorer, data source diagnostics, and configuration helper."""
    db = data['db']
    uid = data['uid']
    password = data['password']
    has_odoo = data['has_odoo']
    data_sources = data.get('data_sources', {})

    # Data Source Status
    section_header("Data Source Status", "Which sections are pulling from Odoo vs demo data")

    source_labels = {
        'odoo': ('Odoo (live)', 'good'),
        'nmbrs': ('Nmbrs (live)', 'good'),
        'demo': ('Demo data', 'warning'),
    }

    status_items = []
    for section_key, source in data_sources.items():
        label, badge_class = source_labels.get(source, ('Unknown', 'danger'))
        status_items.append(f"<tr>"
                            f"<td style='padding: 6px 12px; font-weight: 600;'>{section_key.upper()}</td>"
                            f"<td style='padding: 6px 12px;'>{badge(label, badge_class)}</td>"
                            f"</tr>")

    st.markdown(f"""
    <table style="border-collapse: collapse; width: 100%; max-width: 400px;
                   background: white; border-radius: 8px; overflow: hidden;
                   box-shadow: 0 1px 4px rgba(0,0,0,0.08);">
        <thead><tr style="background: {COLORS['teal']}; color: white;">
            <th style="padding: 8px 12px; text-align: left;">Section</th>
            <th style="padding: 8px 12px; text-align: left;">Source</th>
        </tr></thead>
        <tbody>{''.join(status_items)}</tbody>
    </table>
    """, unsafe_allow_html=True)

    if not has_odoo:
        st.markdown("")
        st.warning("Odoo credentials not configured. All data is demo. "
                    "Add ODOO_USER and ODOO_PASSWORD to .streamlit/secrets.toml or Streamlit Cloud secrets.")

    # Account Map Configuration
    st.markdown("")
    section_header("Current Account Map", "Account code patterns configured in config.py")

    for sec_name, sec_entries in ACCOUNT_MAP.items():
        with st.expander(f"{sec_name.upper()} ({len(sec_entries)} categories)", expanded=False):
            rows = []
            for cat_key, entry in sec_entries.items():
                rows.append({
                    'Category Key': cat_key,
                    'Label': entry['label'],
                    'Account Codes': ', '.join(entry['codes']),
                    'Sign': entry.get('sign', 'abs'),
                    'Group': entry.get('group', ''),
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Account Explorer (Odoo only)
    if has_odoo:
        st.markdown("")
        section_header("Account Explorer", "Discover actual account codes in your Odoo instance")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Chart of Accounts**")
            if st.button("Fetch Chart of Accounts", key="fetch_coa"):
                coa_df = fetch_chart_of_accounts(db, uid, password)
                if not coa_df.empty:
                    st.session_state['coa_df'] = coa_df
                    st.success(f"Found {len(coa_df)} accounts")
                else:
                    st.warning("No accounts found or access denied.")

            if 'coa_df' in st.session_state and not st.session_state['coa_df'].empty:
                coa = st.session_state['coa_df']
                # Filter
                type_filter = st.multiselect(
                    "Filter by account type:",
                    options=sorted(coa['account_type'].unique()),
                    key="coa_type_filter",
                )
                code_search = st.text_input("Search by code prefix:", key="coa_code_search",
                                            placeholder="e.g. 8 or 40")
                filtered_coa = coa.copy()
                if type_filter:
                    filtered_coa = filtered_coa[filtered_coa['account_type'].isin(type_filter)]
                if code_search:
                    filtered_coa = filtered_coa[filtered_coa['code'].str.startswith(code_search)]

                st.dataframe(filtered_coa, use_container_width=True, hide_index=True,
                             height=400)
                st.caption(f"Showing {len(filtered_coa)} of {len(coa)} accounts")

        with col2:
            st.markdown("**Analytic Accounts (Store Mapping)**")
            if st.button("Fetch Analytic Accounts", key="fetch_analytics"):
                analytics_df = fetch_analytic_accounts(db, uid, password)
                if not analytics_df.empty:
                    st.session_state['analytics_df'] = analytics_df
                    st.success(f"Found {len(analytics_df)} analytic accounts")
                else:
                    st.warning("No analytic accounts found.")

            if 'analytics_df' in st.session_state and not st.session_state['analytics_df'].empty:
                analytics = st.session_state['analytics_df']
                # Show mapping status
                for _, row in analytics.iterrows():
                    mapped_store = ODOO_ID_TO_STORE.get(row['id'])
                    icon = "mapped" if mapped_store else "unmapped"
                    status = badge(mapped_store, "good") if mapped_store else badge("not mapped", "warning")
                    st.markdown(f"ID **{row['id']}** — {row['name']} {status}",
                                unsafe_allow_html=True)

        # Data Availability Check
        st.markdown("")
        section_header("Data Availability Check", "Test which ACCOUNT_MAP sections have real data")

        if st.button("Run Availability Check", key="check_avail"):
            with st.spinner("Checking Odoo for data in each section..."):
                avail = check_data_availability(db, uid, password, tuple(selected_years))
                st.session_state['data_avail'] = avail

        if 'data_avail' in st.session_state:
            avail = st.session_state['data_avail']
            for sec, info in avail.items():
                status = "good" if info["has_data"] else ("warning" if info["configured"] else "danger")
                label = (f"{info['row_count']:,} rows" if info["has_data"]
                         else ("configured, no data" if info["configured"] else "not configured"))
                st.markdown(f"**{sec.upper()}**: {badge(label, status)}", unsafe_allow_html=True)

    else:
        st.markdown("")
        st.info("Connect to Odoo to use the Account Explorer. "
                "This tool lets you discover account codes and verify your ACCOUNT_MAP configuration.")

    # ── NMBRS INTEGRATION ──────────────────────────
    st.markdown("")
    section_header("Nmbrs (Visma) Integration", "Employee, salary, and schedule data from Nmbrs HR/Payroll")

    nmbrs_configured = is_nmbrs_configured()

    if nmbrs_configured:
        st.success("Nmbrs credentials detected.")

        # ── Company Discovery & Connection Test ──
        st.markdown("**Company Discovery**")
        st.caption("Lists all Nmbrs companies accessible with your credentials. "
                   "Copy the IDs into NMBRS_CONFIG['companies'] in config.py.")
        if st.button("List All Companies & Test Connection", key="test_nmbrs"):
            with st.spinner("Connecting to Nmbrs..."):
                status = check_nmbrs_connection()
                st.session_state['nmbrs_status'] = status

        if 'nmbrs_status' in st.session_state:
            ns = st.session_state['nmbrs_status']
            if ns['connected']:
                all_co = ns.get('all_companies', [])
                configured_co = ns.get('companies', [])
                st.success(f"Connected — {len(all_co)} companies accessible, "
                           f"{len(configured_co)} configured, "
                           f"{ns['total_employees']} employees total")

                # Show ALL accessible companies with config status
                co_rows = []
                for co in all_co:
                    co_rows.append({
                        "ID": co["id"],
                        "Company": co["name"],
                        "Number": co.get("number", ""),
                        "Employees": co["employee_count"],
                        "Status": "Configured" if co["configured"] else "Not configured",
                    })
                if co_rows:
                    st.dataframe(
                        pd.DataFrame(co_rows), use_container_width=True, hide_index=True,
                        column_config={
                            'ID': st.column_config.NumberColumn('Nmbrs ID', format='%d'),
                            'Company': 'Company Name',
                            'Number': 'Company #',
                            'Employees': st.column_config.NumberColumn('Employees', format='%d'),
                            'Status': 'Config Status',
                        },
                    )

                    unconfigured = [co for co in all_co if not co["configured"]]
                    if unconfigured:
                        st.info(
                            "To add a company, copy its ID into config.py:\n\n"
                            "```python\n"
                            "NMBRS_CONFIG = {\n"
                            '    "companies": {\n'
                            + "".join(f'        {co["id"]}: "{co["name"]}",\n' for co in all_co)
                            + "    },\n"
                            "    ...\n"
                            "}\n"
                            "```"
                        )
            else:
                st.error(f"Connection failed: {ns['error']}")

        # ── Configured companies summary ──
        configured_companies = NMBRS_CONFIG.get("companies", {})
        if configured_companies:
            st.markdown("")
            st.markdown(f"**Configured companies** ({len(configured_companies)}):")
            for cid, label in configured_companies.items():
                st.markdown(f"- {badge(str(cid), 'good')} {label}", unsafe_allow_html=True)
        else:
            st.warning("No companies configured yet. Click 'List All Companies' above to "
                       "discover your Nmbrs company IDs.")

        # ── Department Explorer ──
        st.markdown("")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Department Explorer**")
            st.caption("Discover Nmbrs departments and cost centers across all "
                       "configured companies for the NMBRS_DEPARTMENT_TO_STORE mapping.")
            if st.button("Fetch Departments", key="fetch_nmbrs_depts"):
                with st.spinner("Fetching departments from all companies..."):
                    dept_df = fetch_nmbrs_departments()
                    if not dept_df.empty:
                        st.session_state['nmbrs_depts'] = dept_df
                        st.success(f"Found {len(dept_df)} departments/cost centers")
                    else:
                        st.warning("No departments found. Check company IDs.")

            if 'nmbrs_depts' in st.session_state and not st.session_state['nmbrs_depts'].empty:
                dept_data = st.session_state['nmbrs_depts']
                # Group by company
                for company_label in dept_data['nmbrs_company'].unique():
                    st.markdown(f"*{company_label}:*")
                    company_depts = dept_data[dept_data['nmbrs_company'] == company_label]
                    for _, row in company_depts.iterrows():
                        mapped = NMBRS_DEPARTMENT_TO_STORE.get(row['description'])
                        status_badge = (badge(mapped, "good") if mapped
                                        else badge("not mapped", "warning"))
                        st.markdown(
                            f"&nbsp;&nbsp;**{row['type'].title()}**: {row['description']} "
                            f"(ID: {row['id']}) {status_badge}",
                            unsafe_allow_html=True,
                        )

        with col2:
            st.markdown("**Current Department → Store Mapping**")
            mapping_rows = [{"Department/Cost Center": k, "Store Code": v}
                            for k, v in NMBRS_DEPARTMENT_TO_STORE.items()]
            if mapping_rows:
                st.dataframe(pd.DataFrame(mapping_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No mappings configured. Edit NMBRS_DEPARTMENT_TO_STORE in config.py.")

        # ── Employee overview ──
        st.markdown("")
        st.markdown("**Employee Overview** (all configured companies merged)")
        if st.button("Load Employee Data", key="load_nmbrs_employees"):
            with st.spinner("Fetching employees from all companies..."):
                emp_df = fetch_nmbrs_employees()
                if not emp_df.empty:
                    st.session_state['nmbrs_employees'] = emp_df
                    st.success(f"Loaded {len(emp_df)} employees")
                else:
                    st.warning("No employees found.")

        if 'nmbrs_employees' in st.session_state and not st.session_state['nmbrs_employees'].empty:
            emp = st.session_state['nmbrs_employees']

            # Summary by company
            company_summary = emp.groupby('nmbrs_company').agg(
                headcount=('employee_id', 'count'),
                total_fte=('fte_factor', 'sum'),
            ).reset_index()
            for _, row in company_summary.iterrows():
                st.markdown(f"**{row['nmbrs_company']}**: {int(row['headcount'])} employees, "
                            f"{row['total_fte']:.1f} FTE")

            # Summary by store (merged across companies)
            store_summary = emp.groupby(['store_code', 'store_name']).agg(
                headcount=('employee_id', 'count'),
                total_fte=('fte_factor', 'sum'),
                companies=('nmbrs_company', lambda x: ', '.join(sorted(x.unique()))),
            ).reset_index().sort_values('headcount', ascending=False)

            st.dataframe(
                store_summary, use_container_width=True, hide_index=True,
                column_config={
                    'store_code': 'Code',
                    'store_name': 'Store',
                    'headcount': st.column_config.NumberColumn('Headcount', format='%d'),
                    'total_fte': st.column_config.NumberColumn('FTE', format='%.1f'),
                    'companies': 'From Companies',
                },
            )

            with st.expander("Full employee list", expanded=False):
                st.dataframe(
                    emp[['name', 'department', 'store_name', 'job_title',
                         'fte_factor', 'start_date', 'nmbrs_company']],
                    use_container_width=True, hide_index=True,
                    column_config={
                        'name': 'Name',
                        'department': 'Department',
                        'store_name': 'Store',
                        'job_title': 'Job Title',
                        'fte_factor': st.column_config.NumberColumn('FTE', format='%.2f'),
                        'start_date': 'Start Date',
                        'nmbrs_company': 'Company',
                    },
                )

        # ── Salary overview ──
        st.markdown("")
        st.markdown("**Salary Overview** (aggregated, all companies)")
        if st.button("Load Salary Data", key="load_nmbrs_salary"):
            with st.spinner("Fetching salary data from all companies..."):
                sal_df = fetch_nmbrs_salary_data()
                if not sal_df.empty:
                    st.session_state['nmbrs_salary'] = sal_df
                    st.success(f"Loaded salary data for {len(sal_df)} employees")
                else:
                    st.warning("No salary data found.")

        if 'nmbrs_salary' in st.session_state and not st.session_state['nmbrs_salary'].empty:
            sal = st.session_state['nmbrs_salary']

            # Per-company totals
            company_sal = sal.groupby('nmbrs_company').agg(
                headcount=('employee_id', 'count'),
                total_employer_cost=('employer_cost_month', 'sum'),
            ).reset_index()
            for _, row in company_sal.iterrows():
                st.markdown(f"**{row['nmbrs_company']}**: {int(row['headcount'])} employees, "
                            f"\u20ac{row['total_employer_cost']:,.0f}/mo total employer cost")

            # Aggregated by store (no individual salaries shown for privacy)
            store_sal = sal.groupby(['store_code', 'store_name']).agg(
                headcount=('employee_id', 'count'),
                total_gross=('gross_salary_month', 'sum'),
                total_employer_cost=('employer_cost_month', 'sum'),
                avg_fte=('fte_factor', 'mean'),
            ).reset_index().sort_values('total_employer_cost', ascending=False)

            st.dataframe(
                store_sal, use_container_width=True, hide_index=True,
                column_config={
                    'store_code': 'Code',
                    'store_name': 'Store',
                    'headcount': st.column_config.NumberColumn('Headcount', format='%d'),
                    'total_gross': st.column_config.NumberColumn('Total Gross/mo', format='\u20ac%.0f'),
                    'total_employer_cost': st.column_config.NumberColumn('Total Cost/mo', format='\u20ac%.0f'),
                    'avg_fte': st.column_config.NumberColumn('Avg FTE', format='%.2f'),
                },
            )

    else:
        st.info("Nmbrs not configured. Add NMBRS_USERNAME and NMBRS_TOKEN to "
                ".streamlit/secrets.toml or Streamlit Cloud secrets to enable "
                "HR/payroll data integration.")
        st.markdown("""
        **Setup steps:**
        1. Get an API token from your Nmbrs admin (Settings → API Tokens)
        2. Add to secrets: `NMBRS_USERNAME`, `NMBRS_TOKEN`
        3. Optionally add `NMBRS_DOMAIN` and `NMBRS_ENV`
        4. Click "List All Companies" to discover your company IDs
        5. Add company IDs to `NMBRS_CONFIG["companies"]` in config.py
        6. Map departments to stores in `NMBRS_DEPARTMENT_TO_STORE`
        """)

    # Configuration Reference
    st.markdown("")
    section_header("How to Configure", "Steps to connect real data")
    st.markdown("""
    **Odoo (Financial Data):**
    1. Set Odoo credentials in `.streamlit/secrets.toml` or Streamlit Cloud secrets
    2. Open this Settings tab and click "Fetch Chart of Accounts"
    3. Identify your account codes — find revenue accounts (usually 8xxxxx),
       COGS accounts (usually 4xxxxx), and operating expense accounts
    4. Edit `config.py` — update the `ACCOUNT_MAP` dict with your real codes
    5. Restart the app — sections with valid codes will show real Odoo data

    Each ACCOUNT_MAP entry needs:
    - `codes`: List of Odoo account code patterns (e.g. `["800000"]` or `["8%"]` for wildcards)
    - `label`: Display name in the dashboard
    - `sign`: `"credit"` for revenue, `"debit"` for expenses, `"abs"` for assets/CAPEX

    **Nmbrs (HR/Payroll Data):**
    1. Get an API token from Nmbrs (admin → Settings → API Tokens)
    2. Add `NMBRS_USERNAME` and `NMBRS_TOKEN` to secrets
    3. Click "List All Companies" in Settings to discover company IDs
    4. Add both company IDs to `NMBRS_CONFIG["companies"]` in config.py
    5. Use the Department Explorer to discover department names
    6. Map departments to store codes in `NMBRS_DEPARTMENT_TO_STORE`
    7. Restart — the Labor section will merge data from both companies
    """)


# ──────────────────────────────────────────────
# MAIN APPLICATION
# ──────────────────────────────────────────────
def main():
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown("""
        <p class="hero-header">☕ Wakuli <span>Retail Analytics</span></p>
        <p class="hero-tagline">Farmer-Friendly Finance &mdash; Brewing Profit with Purpose</p>
        """, unsafe_allow_html=True)
    with col2:
        st.image("https://www.wakuli.com/cdn/shop/files/logo_green.png?v=1719823287&width=200", width=110)

    # Sidebar
    selected_years, store_filter, selected_accounts = render_sidebar()

    # Load data
    data = load_data(selected_years, selected_accounts)

    # Data source status banner
    data_sources = data.get('data_sources', {})
    odoo_sections = [k for k, v in data_sources.items() if v == 'odoo']
    demo_sections = [k for k, v in data_sources.items() if v == 'demo']

    nmbrs_sections = [k for k, v in data_sources.items() if v == 'nmbrs']

    if not data['has_odoo'] and not nmbrs_sections:
        st.info("Running in demo mode — no Odoo/Nmbrs credentials configured. "
                "All data shown is illustrative. See the Settings tab to connect.")
    else:
        live_parts = []
        if odoo_sections:
            live_parts.append(f"Odoo: **{', '.join(s.upper() for s in odoo_sections)}**")
        if nmbrs_sections:
            live_parts.append(f"Nmbrs: **{', '.join(s.upper() for s in nmbrs_sections)}**")
        if demo_sections:
            demo_text = ', '.join(s.upper() for s in demo_sections)
            if live_parts:
                st.info(f"Live data from {'; '.join(live_parts)}. "
                        f"Demo fallback: **{demo_text}**. "
                        f"Configure more in the Settings tab.")
            else:
                st.info(f"Demo fallback: **{demo_text}**. "
                        f"Configure data sources in the Settings tab.")
        else:
            st.success(f"All data sourced from live systems: {'; '.join(live_parts)}.")

    # Tabs
    tabs = st.tabs([
        "Executive Summary",
        "Financial Deep Dive",
        "Revenue Analytics",
        "Cost & Efficiency",
        "HR / Labor",
        "Customers",
        "CAPEX Tracking",
        "Impact Dashboard",
        "Store Map",
        "Benchmarks",
        "Settings",
    ])

    with tabs[0]:
        render_executive_tab(data, store_filter)

    with tabs[1]:
        render_financial_tab(data, store_filter)

    with tabs[2]:
        render_revenue_tab(data, store_filter)

    with tabs[3]:
        render_cost_tab(data, store_filter)

    with tabs[4]:
        render_hr_tab(data, store_filter)

    with tabs[5]:
        render_customers_tab(data, store_filter)

    with tabs[6]:
        render_capex_tab(data, store_filter, selected_accounts, selected_years)

    with tabs[7]:
        render_impact_tab(data)

    with tabs[8]:
        render_map_tab(data, store_filter)

    with tabs[9]:
        render_comparative_tab(data, store_filter, selected_years)

    with tabs[10]:
        render_settings_tab(data, selected_years)


if __name__ == "__main__":
    main()
