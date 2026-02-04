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
)
from styles import get_brand_css
from odoo_connector import authenticate_odoo, fetch_capex_actuals, get_secret
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
        st.markdown("**Data Source**")
        odoo_user = get_secret("ODOO_USER", "")
        if odoo_user:
            st.success(f"Odoo: {odoo_user[:20]}...")
        else:
            st.info("Demo mode (no Odoo)")

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
# DATA LOADING
# ──────────────────────────────────────────────
def load_data(selected_years, selected_accounts):
    """Load data from Odoo or generate demo data."""
    auth = authenticate_odoo()
    db, uid, password, odoo_url = auth
    has_odoo = db is not None and uid is not None

    if has_odoo:
        capex_df = fetch_capex_actuals(db, uid, password, tuple(selected_accounts), tuple(selected_years))
        # For full dashboard, we generate supplementary demo data for categories
        # not yet available from Odoo (revenue, costs, etc.)
        demo = generate_all_demo_data(selected_years)
        data = demo
        data['capex'] = capex_df if not capex_df.empty else demo['capex']
        data['has_odoo'] = True
        data['db'] = db
        data['uid'] = uid
        data['password'] = password
    else:
        data = generate_all_demo_data(selected_years)
        data['has_odoo'] = False
        data['db'] = None
        data['uid'] = None
        data['password'] = None

    return data


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

    if not data['has_odoo']:
        st.info("Running in demo mode. Connect Odoo for live data. Demo data shown for illustration.")

    # Tabs
    tab_exec, tab_fin, tab_rev, tab_cost, tab_cust, tab_capex, tab_impact, tab_map, tab_compare = st.tabs([
        "Executive Summary",
        "Financial Deep Dive",
        "Revenue Analytics",
        "Cost & Efficiency",
        "Customers",
        "CAPEX Tracking",
        "Impact Dashboard",
        "Store Map",
        "Benchmarks",
    ])

    with tab_exec:
        render_executive_tab(data, store_filter)

    with tab_fin:
        render_financial_tab(data, store_filter)

    with tab_rev:
        render_revenue_tab(data, store_filter)

    with tab_cost:
        render_cost_tab(data, store_filter)

    with tab_cust:
        render_customers_tab(data, store_filter)

    with tab_capex:
        render_capex_tab(data, store_filter, selected_accounts, selected_years)

    with tab_impact:
        render_impact_tab(data)

    with tab_map:
        render_map_tab(data, store_filter)

    with tab_compare:
        render_comparative_tab(data, store_filter, selected_years)


if __name__ == "__main__":
    main()
