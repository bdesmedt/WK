"""
Wakuli Retail Analytics - KPI Calculation Engine
==================================================
All financial KPI calculations: ROI, profitability, break-even,
revenue metrics, cost analysis, efficiency ratios, and impact metrics.

Each function is documented with its formula for audit traceability.
"""

import pandas as pd
import numpy as np
from config import TARGETS, STORE_LOCATIONS


# ──────────────────────────────────────────────
# STORE-LEVEL ROI ANALYSIS
# ──────────────────────────────────────────────

def calculate_store_roi(revenue_df, cost_df, investment_df, store_code=None):
    """Calculate Return on Investment per store.

    Formula: ROI = (Cumulative Net Profit / Total Investment) x 100
    Net Profit = Revenue - Total Costs
    """
    if revenue_df.empty or cost_df.empty or investment_df.empty:
        return pd.DataFrame()

    stores = [store_code] if store_code else investment_df['store_code'].unique()
    rows = []

    for sc in stores:
        inv_row = investment_df[investment_df['store_code'] == sc]
        if inv_row.empty:
            continue
        total_investment = inv_row.iloc[0]['total_investment']
        opened = inv_row.iloc[0].get('opened', '2022-01')

        store_rev = revenue_df[revenue_df['store_code'] == sc]['revenue'].sum()
        store_costs = cost_df[cost_df['store_code'] == sc]['amount'].sum()
        net_profit = store_rev - store_costs

        roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

        # Monthly ROI progression
        monthly_rev = revenue_df[revenue_df['store_code'] == sc].groupby('month')['revenue'].sum()
        monthly_costs = cost_df[cost_df['store_code'] == sc].groupby('month')['amount'].sum()
        months_operating = len(monthly_rev)

        annualized_roi = (roi_pct / max(1, months_operating)) * 12 if months_operating > 0 else 0

        rows.append({
            'store_code': sc,
            'store_name': STORE_LOCATIONS.get(sc, {}).get('name', sc),
            'city': STORE_LOCATIONS.get(sc, {}).get('city', ''),
            'opened': opened,
            'total_investment': total_investment,
            'total_revenue': store_rev,
            'total_costs': store_costs,
            'net_profit': net_profit,
            'roi_pct': round(roi_pct, 1),
            'annualized_roi_pct': round(annualized_roi, 1),
            'months_operating': months_operating,
        })

    return pd.DataFrame(rows)


def calculate_break_even(revenue_df, cost_df, investment_df, store_code=None):
    """Calculate break-even analysis per store.

    Break-even point = Fixed Costs / (1 - Variable Cost Ratio)
    Months to break-even = Total Investment / Monthly Net Profit
    """
    if revenue_df.empty or cost_df.empty or investment_df.empty:
        return pd.DataFrame()

    stores = [store_code] if store_code else investment_df['store_code'].unique()
    fixed_cost_categories = {'rent', 'insurance', 'depreciation'}
    rows = []

    for sc in stores:
        inv_row = investment_df[investment_df['store_code'] == sc]
        if inv_row.empty:
            continue
        total_investment = inv_row.iloc[0]['total_investment']

        store_rev = revenue_df[revenue_df['store_code'] == sc]
        store_costs = cost_df[cost_df['store_code'] == sc]

        if store_rev.empty:
            continue

        monthly_rev = store_rev.groupby('month')['revenue'].sum()
        months = len(monthly_rev)
        if months == 0:
            continue

        avg_monthly_revenue = monthly_rev.mean()

        # Separate fixed and variable costs
        fixed_costs_total = store_costs[
            store_costs['cost_category'].isin(fixed_cost_categories)
        ]['amount'].sum()
        variable_costs_total = store_costs[
            ~store_costs['cost_category'].isin(fixed_cost_categories)
        ]['amount'].sum()

        total_rev = store_rev['revenue'].sum()
        variable_cost_ratio = variable_costs_total / total_rev if total_rev > 0 else 0.7
        avg_monthly_fixed = fixed_costs_total / months

        # Break-even revenue per month
        be_revenue_monthly = avg_monthly_fixed / (1 - variable_cost_ratio) if variable_cost_ratio < 1 else float('inf')

        # Monthly net profit
        total_costs = store_costs['amount'].sum()
        avg_monthly_profit = (total_rev - total_costs) / months

        # Months to payback initial investment
        months_to_break_even = (total_investment / avg_monthly_profit) if avg_monthly_profit > 0 else float('inf')

        # Current performance vs break-even
        be_performance = (avg_monthly_revenue / be_revenue_monthly * 100) if be_revenue_monthly > 0 else 0

        rows.append({
            'store_code': sc,
            'store_name': STORE_LOCATIONS.get(sc, {}).get('name', sc),
            'total_investment': total_investment,
            'avg_monthly_revenue': round(avg_monthly_revenue, 0),
            'break_even_revenue_monthly': round(be_revenue_monthly, 0),
            'avg_monthly_profit': round(avg_monthly_profit, 0),
            'months_to_payback': round(months_to_break_even, 1) if months_to_break_even != float('inf') else None,
            'be_performance_pct': round(be_performance, 1),
            'variable_cost_ratio': round(variable_cost_ratio, 3),
            'contribution_margin': round(1 - variable_cost_ratio, 3),
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# PROFITABILITY METRICS
# ──────────────────────────────────────────────

def calculate_profitability(revenue_df, cost_df, store_filter=None):
    """Calculate profit margins and EBITDA.

    Gross Margin = (Revenue - COGS) / Revenue x 100
    Net Margin = (Revenue - All Costs) / Revenue x 100
    EBITDA = Revenue - OpEx (excl. depreciation)
    """
    if revenue_df.empty or cost_df.empty:
        return {}

    if store_filter:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]

    total_revenue = revenue_df['revenue'].sum()
    if total_revenue == 0:
        return {}

    cogs_categories = {'cogs_coffee', 'cogs_food', 'cogs_merch'}
    depreciation_categories = {'depreciation'}

    cogs = cost_df[cost_df['cost_category'].isin(cogs_categories)]['amount'].sum()
    total_costs = cost_df['amount'].sum()
    depreciation = cost_df[cost_df['cost_category'].isin(depreciation_categories)]['amount'].sum()

    gross_profit = total_revenue - cogs
    net_profit = total_revenue - total_costs
    ebitda = net_profit + depreciation

    return {
        'total_revenue': total_revenue,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'gross_margin_pct': round(gross_profit / total_revenue * 100, 1),
        'net_profit': net_profit,
        'net_margin_pct': round(net_profit / total_revenue * 100, 1),
        'ebitda': ebitda,
        'ebitda_margin_pct': round(ebitda / total_revenue * 100, 1),
        'total_costs': total_costs,
        'opex_ratio': round((total_costs - cogs) / total_revenue * 100, 1),
    }


def calculate_profitability_by_store(revenue_df, cost_df):
    """Calculate profitability metrics per store."""
    if revenue_df.empty or cost_df.empty:
        return pd.DataFrame()

    stores = revenue_df['store_code'].unique()
    rows = []
    for sc in stores:
        metrics = calculate_profitability(revenue_df, cost_df, store_filter=[sc])
        if metrics:
            metrics['store_code'] = sc
            metrics['store_name'] = STORE_LOCATIONS.get(sc, {}).get('name', sc)
            rows.append(metrics)

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# REVENUE METRICS
# ──────────────────────────────────────────────

def calculate_revenue_metrics(revenue_df, customer_df, store_filter=None):
    """Calculate revenue KPIs: ATV, revenue/sqm, growth rates."""
    if revenue_df.empty:
        return {}

    if store_filter:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
        if not customer_df.empty:
            customer_df = customer_df[customer_df['store_code'].isin(store_filter)]

    total_revenue = revenue_df['revenue'].sum()
    months_data = revenue_df['month'].nunique()

    # Revenue by period
    monthly_rev = revenue_df.groupby('month')['revenue'].sum()
    avg_monthly = monthly_rev.mean() if len(monthly_rev) > 0 else 0

    # Revenue by category
    cat_rev = revenue_df.groupby('category')['revenue'].sum().to_dict()
    total_for_pct = max(total_revenue, 1)

    # Revenue per sqm
    stores_in_data = revenue_df['store_code'].unique()
    total_sqm = sum(STORE_LOCATIONS.get(sc, {}).get('sqm', 0) for sc in stores_in_data if sc != "OOH")
    rev_per_sqm = (total_revenue / months_data / total_sqm) if total_sqm > 0 and months_data > 0 else 0

    # Growth: compare last 3 months to prior 3 months
    sorted_months = sorted(monthly_rev.index)
    if len(sorted_months) >= 6:
        recent = monthly_rev[sorted_months[-3:]].sum()
        prior = monthly_rev[sorted_months[-6:-3]].sum()
        growth_pct = ((recent - prior) / prior * 100) if prior > 0 else 0
    else:
        growth_pct = 0

    # Customer metrics
    avg_tv = 0
    total_customers = 0
    if not customer_df.empty:
        avg_tv = customer_df['avg_transaction_value'].mean()
        total_customers = customer_df['unique_customers'].sum()

    return {
        'total_revenue': total_revenue,
        'avg_monthly_revenue': round(avg_monthly, 0),
        'months_of_data': months_data,
        'revenue_per_sqm_month': round(rev_per_sqm, 0),
        'growth_pct_3m': round(growth_pct, 1),
        'avg_transaction_value': round(avg_tv, 2),
        'total_customers': total_customers,
        'revenue_coffee_pct': round(cat_rev.get('coffee', 0) / total_for_pct * 100, 1),
        'revenue_food_pct': round(cat_rev.get('food', 0) / total_for_pct * 100, 1),
        'revenue_merch_pct': round(cat_rev.get('merchandise', 0) / total_for_pct * 100, 1),
        'revenue_sub_pct': round(cat_rev.get('subscription', 0) / total_for_pct * 100, 1),
    }


def calculate_revenue_by_period(revenue_df, period='month'):
    """Aggregate revenue by time period (month, quarter, year)."""
    if revenue_df.empty:
        return pd.DataFrame()

    if period == 'quarter':
        revenue_df = revenue_df.copy()
        revenue_df['period'] = revenue_df['month'].apply(
            lambda m: f"{m[:4]}-Q{(int(m[5:7]) - 1) // 3 + 1}"
        )
    elif period == 'year':
        revenue_df = revenue_df.copy()
        revenue_df['period'] = revenue_df['year'].astype(str)
    else:
        revenue_df = revenue_df.copy()
        revenue_df['period'] = revenue_df['month']

    return revenue_df.groupby('period')['revenue'].sum().reset_index().sort_values('period')


# ──────────────────────────────────────────────
# COST STRUCTURE ANALYSIS
# ──────────────────────────────────────────────

def calculate_cost_structure(cost_df, revenue_df, store_filter=None):
    """Analyze cost structure with ratios and benchmarks.

    Returns cost breakdown with % of revenue for each category.
    """
    if cost_df.empty or revenue_df.empty:
        return pd.DataFrame()

    if store_filter:
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]

    total_revenue = revenue_df['revenue'].sum()
    cost_summary = cost_df.groupby(['cost_category', 'cost_label'])['amount'].sum().reset_index()
    cost_summary = cost_summary.sort_values('amount', ascending=False)
    cost_summary['pct_of_revenue'] = (cost_summary['amount'] / total_revenue * 100).round(1)

    # Add benchmark targets
    target_map = {
        'labor': TARGETS['labor_cost_pct'] * 100,
        'rent': TARGETS['rent_cost_pct'] * 100,
        'cogs_coffee': TARGETS['beverage_cost_pct'] * 100,
        'cogs_food': TARGETS['food_cost_pct'] * 100,
    }
    cost_summary['target_pct'] = cost_summary['cost_category'].map(target_map)
    cost_summary['vs_target'] = cost_summary.apply(
        lambda r: r['pct_of_revenue'] - r['target_pct'] if pd.notna(r['target_pct']) else None, axis=1
    )

    return cost_summary


# ──────────────────────────────────────────────
# CUSTOMER METRICS
# ──────────────────────────────────────────────

def calculate_customer_metrics(customer_df, cost_df=None, store_filter=None):
    """Calculate customer KPIs: CAC, CLV, retention, frequency.

    CAC = Marketing Spend / New Customers
    CLV = Avg Revenue per Customer x Avg Lifespan
    """
    if customer_df.empty:
        return {}

    if store_filter:
        customer_df = customer_df[customer_df['store_code'].isin(store_filter)]

    total_transactions = customer_df['total_transactions'].sum()
    total_customers = customer_df['unique_customers'].sum()
    new_customers = customer_df['new_customers'].sum()
    returning_customers = customer_df['returning_customers'].sum()
    avg_retention = customer_df['retention_rate'].mean()
    avg_tv = customer_df['avg_transaction_value'].mean()

    # Estimate CAC from marketing costs
    cac = 0
    if cost_df is not None and not cost_df.empty:
        if store_filter:
            cost_df = cost_df[cost_df['store_code'].isin(store_filter)]
        marketing_spend = cost_df[cost_df['cost_category'] == 'marketing']['amount'].sum()
        cac = marketing_spend / new_customers if new_customers > 0 else 0

    # Estimated CLV (simplified: avg monthly revenue per customer x avg retention months)
    months = customer_df['month'].nunique()
    if months > 0 and total_customers > 0:
        avg_monthly_rev_per_customer = customer_df['revenue'].sum() / total_customers
        avg_lifespan_months = 1 / (1 - avg_retention) if avg_retention < 1 else 24
        clv = avg_monthly_rev_per_customer * min(avg_lifespan_months, 36)
    else:
        clv = 0

    # Visit frequency
    visits_per_customer = total_transactions / total_customers if total_customers > 0 else 0

    return {
        'total_transactions': total_transactions,
        'total_customers': total_customers,
        'new_customers': new_customers,
        'returning_customers': returning_customers,
        'avg_retention_rate': round(avg_retention, 3),
        'avg_transaction_value': round(avg_tv, 2),
        'customer_acquisition_cost': round(cac, 2),
        'customer_lifetime_value': round(clv, 2),
        'clv_cac_ratio': round(clv / cac, 1) if cac > 0 else 0,
        'visits_per_customer': round(visits_per_customer, 1),
        'new_customer_pct': round(new_customers / total_customers * 100, 1) if total_customers > 0 else 0,
    }


# ──────────────────────────────────────────────
# LABOR EFFICIENCY
# ──────────────────────────────────────────────

def calculate_labor_efficiency(labor_df, store_filter=None):
    """Calculate labor productivity metrics.

    Revenue per Labor Hour = Revenue / Total Labor Hours
    Labor Cost Ratio = Labor Costs / Revenue x 100
    """
    if labor_df.empty:
        return {}

    if store_filter:
        labor_df = labor_df[labor_df['store_code'].isin(store_filter)]

    total_revenue = labor_df['revenue'].sum()
    total_labor_hours = labor_df['total_labor_hours'].sum()
    total_labor_cost = labor_df['labor_cost'].sum()
    avg_fte = labor_df['fte_count'].mean()

    rev_per_hour = total_revenue / total_labor_hours if total_labor_hours > 0 else 0
    labor_pct = total_labor_cost / total_revenue * 100 if total_revenue > 0 else 0
    rev_per_employee = total_revenue / (avg_fte * labor_df['month'].nunique()) if avg_fte > 0 else 0

    return {
        'total_labor_hours': round(total_labor_hours, 0),
        'total_labor_cost': round(total_labor_cost, 0),
        'avg_fte': round(avg_fte, 1),
        'revenue_per_labor_hour': round(rev_per_hour, 2),
        'labor_cost_pct': round(labor_pct, 1),
        'revenue_per_employee_month': round(rev_per_employee, 0),
        'target_labor_pct': TARGETS['labor_cost_pct'] * 100,
        'vs_target': round(labor_pct - TARGETS['labor_cost_pct'] * 100, 1),
    }


# ──────────────────────────────────────────────
# INVENTORY METRICS
# ──────────────────────────────────────────────

def calculate_inventory_metrics(inventory_df, cost_df=None, store_filter=None):
    """Calculate inventory management KPIs.

    Turnover Ratio = COGS / Average Inventory Value
    Waste Rate = Total Waste / Total Sold x 100
    """
    if inventory_df.empty:
        return {}

    if store_filter:
        inventory_df = inventory_df[inventory_df['store_code'].isin(store_filter)]

    total_sold = inventory_df['sold'].sum()
    total_waste = inventory_df['waste'].sum()
    avg_stock_value = inventory_df.groupby('month')['stock_value'].sum().mean()
    total_stock_value = inventory_df.groupby('month')['stock_value'].sum().iloc[-1] if len(inventory_df) > 0 else 0

    # COGS from cost data or estimated from inventory
    months = inventory_df['month'].nunique()
    total_cost_of_sold = (inventory_df['sold'] * inventory_df['unit_cost']).sum()

    turnover_ratio = (total_cost_of_sold / avg_stock_value) if avg_stock_value > 0 else 0
    annualized_turnover = turnover_ratio * (12 / max(1, months))
    waste_rate = (total_waste / (total_sold + total_waste) * 100) if (total_sold + total_waste) > 0 else 0

    # Days inventory outstanding
    daily_cogs = total_cost_of_sold / (months * 30) if months > 0 else 0
    dio = avg_stock_value / daily_cogs if daily_cogs > 0 else 0

    return {
        'avg_stock_value': round(avg_stock_value, 0),
        'current_stock_value': round(total_stock_value, 0),
        'turnover_ratio': round(turnover_ratio, 1),
        'annualized_turnover': round(annualized_turnover, 1),
        'waste_rate_pct': round(waste_rate, 2),
        'days_inventory_outstanding': round(dio, 1),
        'total_waste_units': total_waste,
        'total_sold_units': total_sold,
    }


# ──────────────────────────────────────────────
# CASH FLOW (ESTIMATED)
# ──────────────────────────────────────────────

def calculate_cash_flow(revenue_df, cost_df, store_filter=None):
    """Estimate operating cash flow metrics.

    Operating Cash Flow = Net Profit + Depreciation
    Free Cash Flow = Operating CF - CAPEX
    """
    if revenue_df.empty or cost_df.empty:
        return pd.DataFrame()

    if store_filter:
        revenue_df = revenue_df[revenue_df['store_code'].isin(store_filter)]
        cost_df = cost_df[cost_df['store_code'].isin(store_filter)]

    monthly_rev = revenue_df.groupby('month')['revenue'].sum()
    monthly_costs = cost_df.groupby('month')['amount'].sum()
    monthly_depr = cost_df[cost_df['cost_category'] == 'depreciation'].groupby('month')['amount'].sum()

    months = sorted(set(monthly_rev.index) | set(monthly_costs.index))

    rows = []
    cumulative_cf = 0
    for m in months:
        rev = monthly_rev.get(m, 0)
        costs = monthly_costs.get(m, 0)
        depr = monthly_depr.get(m, 0)
        net_profit = rev - costs
        operating_cf = net_profit + depr
        cumulative_cf += operating_cf

        rows.append({
            'month': m,
            'revenue': round(rev, 0),
            'total_costs': round(costs, 0),
            'net_profit': round(net_profit, 0),
            'depreciation': round(depr, 0),
            'operating_cash_flow': round(operating_cf, 0),
            'cumulative_cash_flow': round(cumulative_cf, 0),
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────
# IMPACT METRICS
# ──────────────────────────────────────────────

def calculate_impact_summary(impact_df):
    """Summarize Wakuli mission impact metrics."""
    if impact_df.empty:
        return {}

    latest_month = impact_df.sort_values('month').iloc[-1]
    total_kg = impact_df['kg_coffee_sourced'].sum()
    total_premium = impact_df['premium_paid_eur'].sum()
    total_cups = impact_df['cups_served'].sum()
    avg_direct_trade = impact_df['direct_trade_pct'].mean()
    avg_compostable = impact_df['compostable_packaging_pct'].mean()

    # Trend: compare latest quarter to prior quarter
    months_sorted = sorted(impact_df['month'].unique())
    if len(months_sorted) >= 6:
        recent_3 = impact_df[impact_df['month'].isin(months_sorted[-3:])]
        prior_3 = impact_df[impact_df['month'].isin(months_sorted[-6:-3])]
        premium_growth = ((recent_3['premium_paid_eur'].sum() - prior_3['premium_paid_eur'].sum())
                          / prior_3['premium_paid_eur'].sum() * 100) if prior_3['premium_paid_eur'].sum() > 0 else 0
    else:
        premium_growth = 0

    return {
        'total_kg_sourced': round(total_kg, 0),
        'total_premium_paid': round(total_premium, 0),
        'total_cups_served': total_cups,
        'current_farmers_supported': int(latest_month['farmers_supported']),
        'avg_farmer_premium_pct': round(impact_df['farmer_premium_pct'].mean() * 100, 1),
        'avg_direct_trade_pct': round(avg_direct_trade * 100, 1),
        'avg_compostable_pct': round(avg_compostable * 100, 1),
        'current_co2_per_cup': round(latest_month['co2_per_cup_grams'], 1),
        'premium_per_cup': round(total_premium / total_cups, 3) if total_cups > 0 else 0,
        'premium_growth_pct': round(premium_growth, 1),
        'kg_per_month_latest': round(latest_month['kg_coffee_sourced'], 0),
    }


# ──────────────────────────────────────────────
# EXECUTIVE SUMMARY (AGGREGATED)
# ──────────────────────────────────────────────

def calculate_executive_summary(revenue_df, cost_df, customer_df, investment_df,
                                 impact_df, store_filter=None):
    """Calculate top-level executive KPIs for the hero section."""
    profit = calculate_profitability(revenue_df, cost_df, store_filter)
    rev_metrics = calculate_revenue_metrics(revenue_df, customer_df, store_filter)
    roi_df = calculate_store_roi(revenue_df, cost_df, investment_df)

    if store_filter and not roi_df.empty:
        roi_df = roi_df[roi_df['store_code'].isin(store_filter)]

    avg_roi = roi_df['roi_pct'].mean() if not roi_df.empty else 0
    total_investment = roi_df['total_investment'].sum() if not roi_df.empty else 0

    impact = calculate_impact_summary(impact_df) if not impact_df.empty else {}

    active_stores = revenue_df['store_code'].nunique() if not revenue_df.empty else 0

    return {
        'total_revenue': profit.get('total_revenue', 0),
        'gross_margin_pct': profit.get('gross_margin_pct', 0),
        'net_margin_pct': profit.get('net_margin_pct', 0),
        'ebitda': profit.get('ebitda', 0),
        'avg_roi_pct': round(avg_roi, 1),
        'total_investment': total_investment,
        'growth_pct': rev_metrics.get('growth_pct_3m', 0),
        'avg_transaction_value': rev_metrics.get('avg_transaction_value', 0),
        'total_customers': rev_metrics.get('total_customers', 0),
        'active_stores': active_stores,
        'farmers_supported': impact.get('current_farmers_supported', 0),
        'premium_paid': impact.get('total_premium_paid', 0),
    }
