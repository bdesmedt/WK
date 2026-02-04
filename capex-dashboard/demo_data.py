"""
Wakuli Retail Analytics - Demo Data Generator
===============================================
Generates comprehensive, realistic demo data for all KPI categories
when Odoo is not connected. Covers revenue, costs, labor, customers,
inventory, and impact metrics across all 20 Wakuli stores.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import STORE_LOCATIONS, CAPEX_ACCOUNTS, PRODUCT_CATEGORIES, DAYPARTS


def _seed():
    return np.random.RandomState(42)


def generate_capex_data(selected_years):
    """Generate demo CAPEX transactions."""
    rng = _seed()
    stores = [c for c in STORE_LOCATIONS if c != "OOH"]
    accounts = list(CAPEX_ACCOUNTS.keys())
    account_labels = list(CAPEX_ACCOUNTS.values())

    rows = []
    for year in selected_years:
        n_transactions = rng.randint(40, 70)
        for _ in range(n_transactions):
            month = rng.randint(1, 13)
            if month > 12:
                month = 12
            day = rng.randint(1, 29)
            store = rng.choice(stores)
            acc_idx = rng.randint(0, len(accounts))
            amount = float(rng.choice([5000, 8000, 10000, 12000, 15000, 18000, 22000, 25000, 30000, 35000, 45000]))
            amount *= rng.uniform(0.7, 1.4)

            rows.append({
                'date': f'{year}-{month:02d}-{day:02d}',
                'year': year,
                'month': f'{year}-{month:02d}',
                'amount': round(amount, 2),
                'description': f'{account_labels[acc_idx].split("(")[0].strip()} - {STORE_LOCATIONS[store]["name"]}',
                'account_code': accounts[acc_idx],
                'account_label': account_labels[acc_idx],
                'cost_category': accounts[acc_idx],
                'cost_label': account_labels[acc_idx],
                'store_code': store,
                'store_name': STORE_LOCATIONS[store]['name'],
                'move_id': None,
                'move_name': '',
                'section': 'capex',
                'group': 'capex',
            })

    return pd.DataFrame(rows)


def generate_revenue_data(selected_years):
    """Generate monthly revenue data by store, category, and channel."""
    rng = _seed()
    stores = [c for c in STORE_LOCATIONS if c != "OOH"]
    categories = list(PRODUCT_CATEGORIES.keys())
    channels = ['dine_in', 'takeaway', 'delivery', 'subscription']

    # Base monthly revenue per store (varies by store size/location)
    store_base_revenue = {}
    for code in stores:
        sqm = STORE_LOCATIONS[code].get('sqm', 55)
        store_base_revenue[code] = sqm * rng.uniform(550, 750)

    rows = []
    for year in selected_years:
        for month in range(1, 13):
            # Skip future months
            now = datetime.now()
            if year > now.year or (year == now.year and month > now.month):
                continue

            # Seasonality: higher in winter months (coffee!)
            seasonality = {1: 1.05, 2: 1.02, 3: 0.98, 4: 0.95, 5: 0.93,
                          6: 0.88, 7: 0.85, 8: 0.87, 9: 0.95, 10: 1.02,
                          11: 1.08, 12: 1.15}
            season_mult = seasonality.get(month, 1.0)

            for store in stores:
                # Growth factor: stores get more revenue over time
                opened = STORE_LOCATIONS[store].get('opened', '2022-01')
                opened_year, opened_month = int(opened[:4]), int(opened[5:7])
                months_open = (year - opened_year) * 12 + (month - opened_month)
                if months_open < 0:
                    continue
                # Ramp-up in first 6 months
                ramp = min(1.0, 0.4 + 0.1 * months_open) if months_open < 6 else 1.0
                # Organic growth ~0.5% per month
                growth = 1.0 + 0.005 * max(0, months_open - 6)

                base = store_base_revenue[store] * season_mult * ramp * growth
                noise = rng.uniform(0.88, 1.12)
                total_revenue = base * noise

                # Split by category
                cat_splits = {'coffee': 0.58, 'food': 0.25, 'merchandise': 0.07, 'subscription': 0.10}
                # Split by channel
                ch_splits = {'dine_in': 0.52, 'takeaway': 0.33, 'delivery': 0.08, 'subscription': 0.07}

                for cat, cat_pct in cat_splits.items():
                    for ch, ch_pct in ch_splits.items():
                        rev = total_revenue * cat_pct * ch_pct * rng.uniform(0.9, 1.1)
                        if rev > 0:
                            rows.append({
                                'year': year,
                                'month': f'{year}-{month:02d}',
                                'store_code': store,
                                'store_name': STORE_LOCATIONS[store]['name'],
                                'category': cat,
                                'category_label': PRODUCT_CATEGORIES[cat]['label'],
                                'channel': ch,
                                'revenue': round(rev, 2),
                            })

    return pd.DataFrame(rows)


def generate_cost_data(revenue_df):
    """Generate cost data based on revenue (realistic cost ratios)."""
    rng = _seed()
    if revenue_df.empty:
        return pd.DataFrame()

    # Aggregate revenue by store/month
    monthly_rev = revenue_df.groupby(['year', 'month', 'store_code', 'store_name'])['revenue'].sum().reset_index()

    rows = []
    cost_categories = {
        'cogs_coffee': {'label': 'COGS - Coffee', 'pct_of_revenue': 0.18, 'variance': 0.03},
        'cogs_food': {'label': 'COGS - Food', 'pct_of_revenue': 0.09, 'variance': 0.02},
        'cogs_merch': {'label': 'COGS - Merchandise', 'pct_of_revenue': 0.03, 'variance': 0.01},
        'labor': {'label': 'Labor Costs', 'pct_of_revenue': 0.28, 'variance': 0.04},
        'rent': {'label': 'Rent & Occupancy', 'pct_of_revenue': 0.11, 'variance': 0.01},
        'utilities': {'label': 'Utilities', 'pct_of_revenue': 0.035, 'variance': 0.008},
        'marketing': {'label': 'Marketing', 'pct_of_revenue': 0.025, 'variance': 0.01},
        'maintenance': {'label': 'Equipment Maintenance', 'pct_of_revenue': 0.015, 'variance': 0.005},
        'supplies': {'label': 'Supplies & Consumables', 'pct_of_revenue': 0.02, 'variance': 0.005},
        'insurance': {'label': 'Insurance & Licenses', 'pct_of_revenue': 0.012, 'variance': 0.002},
        'depreciation': {'label': 'Depreciation', 'pct_of_revenue': 0.04, 'variance': 0.005},
    }

    for _, row in monthly_rev.iterrows():
        rev = row['revenue']
        for cost_key, cost_info in cost_categories.items():
            pct = cost_info['pct_of_revenue'] + rng.uniform(-cost_info['variance'], cost_info['variance'])
            cost = rev * max(0, pct)
            rows.append({
                'year': row['year'],
                'month': row['month'],
                'store_code': row['store_code'],
                'store_name': row['store_name'],
                'cost_category': cost_key,
                'cost_label': cost_info['label'],
                'amount': round(cost, 2),
            })

    return pd.DataFrame(rows)


def generate_customer_data(revenue_df):
    """Generate customer traffic and behavior data."""
    rng = _seed()
    if revenue_df.empty:
        return pd.DataFrame()

    monthly_rev = revenue_df.groupby(['year', 'month', 'store_code', 'store_name'])['revenue'].sum().reset_index()

    rows = []
    for _, row in monthly_rev.iterrows():
        avg_ticket = rng.uniform(5.20, 7.80)
        total_transactions = int(row['revenue'] / avg_ticket)
        # Unique customers is ~60-70% of transactions (repeat visits)
        unique_customers = int(total_transactions * rng.uniform(0.55, 0.72))
        new_customer_pct = rng.uniform(0.25, 0.45)
        new_customers = int(unique_customers * new_customer_pct)
        returning_customers = unique_customers - new_customers

        # Daypart split
        daypart_splits = {
            'early_morning': rng.uniform(0.12, 0.18),
            'morning': rng.uniform(0.30, 0.38),
            'afternoon': rng.uniform(0.22, 0.28),
            'late_afternoon': rng.uniform(0.12, 0.18),
        }
        daypart_splits['evening'] = 1.0 - sum(daypart_splits.values())

        rows.append({
            'year': row['year'],
            'month': row['month'],
            'store_code': row['store_code'],
            'store_name': row['store_name'],
            'revenue': row['revenue'],
            'total_transactions': total_transactions,
            'unique_customers': unique_customers,
            'new_customers': new_customers,
            'returning_customers': returning_customers,
            'avg_transaction_value': round(avg_ticket, 2),
            'retention_rate': round(1 - new_customer_pct, 3),
            **{f'daypart_{k}_pct': round(v, 3) for k, v in daypart_splits.items()},
        })

    return pd.DataFrame(rows)


def generate_labor_data(revenue_df):
    """Generate labor productivity data."""
    rng = _seed()
    if revenue_df.empty:
        return pd.DataFrame()

    monthly_rev = revenue_df.groupby(['year', 'month', 'store_code', 'store_name'])['revenue'].sum().reset_index()

    rows = []
    for _, row in monthly_rev.iterrows():
        sqm = STORE_LOCATIONS.get(row['store_code'], {}).get('sqm', 55)
        # Staff count scales with store size
        fte_count = max(2, sqm / 18 + rng.uniform(-0.5, 0.5))
        hours_per_fte = rng.uniform(140, 168)
        total_labor_hours = fte_count * hours_per_fte
        labor_cost = total_labor_hours * rng.uniform(14.5, 18.5)  # hourly rate EUR
        revenue_per_labor_hour = row['revenue'] / total_labor_hours if total_labor_hours > 0 else 0

        avg_ticket = rng.uniform(5.5, 7.5)
        transactions = int(row['revenue'] / avg_ticket)
        transactions_per_labor_hour = transactions / total_labor_hours if total_labor_hours > 0 else 0

        rows.append({
            'year': row['year'],
            'month': row['month'],
            'store_code': row['store_code'],
            'store_name': row['store_name'],
            'revenue': row['revenue'],
            'fte_count': round(fte_count, 1),
            'total_labor_hours': round(total_labor_hours, 0),
            'labor_cost': round(labor_cost, 2),
            'labor_cost_pct': round(labor_cost / row['revenue'], 3) if row['revenue'] > 0 else 0,
            'revenue_per_labor_hour': round(revenue_per_labor_hour, 2),
            'transactions_per_labor_hour': round(transactions_per_labor_hour, 1),
            'revenue_per_employee': round(row['revenue'] / fte_count, 2) if fte_count > 0 else 0,
        })

    return pd.DataFrame(rows)


def generate_inventory_data(selected_years):
    """Generate inventory management metrics."""
    rng = _seed()
    stores = [c for c in STORE_LOCATIONS if c != "OOH"]
    inventory_items = [
        {'name': 'Single Origin Beans', 'category': 'coffee', 'unit_cost': 18.50},
        {'name': 'Blend Beans', 'category': 'coffee', 'unit_cost': 14.00},
        {'name': 'Milk & Alternatives', 'category': 'dairy', 'unit_cost': 2.80},
        {'name': 'Pastries & Cakes', 'category': 'food', 'unit_cost': 3.50},
        {'name': 'Sandwiches & Wraps', 'category': 'food', 'unit_cost': 4.20},
        {'name': 'Cups & Packaging', 'category': 'supplies', 'unit_cost': 0.35},
        {'name': 'Merchandise Items', 'category': 'merchandise', 'unit_cost': 12.00},
        {'name': 'Syrups & Toppings', 'category': 'supplies', 'unit_cost': 8.50},
    ]

    rows = []
    for year in selected_years:
        for month in range(1, 13):
            now = datetime.now()
            if year > now.year or (year == now.year and month > now.month):
                continue
            for store in stores:
                for item in inventory_items:
                    opening_stock = rng.randint(20, 150)
                    purchased = rng.randint(30, 200)
                    sold = rng.randint(25, int((opening_stock + purchased) * 0.85))
                    waste = max(0, int(rng.uniform(0.02, 0.08) * sold))
                    closing_stock = opening_stock + purchased - sold - waste

                    rows.append({
                        'year': year,
                        'month': f'{year}-{month:02d}',
                        'store_code': store,
                        'store_name': STORE_LOCATIONS[store]['name'],
                        'item_name': item['name'],
                        'item_category': item['category'],
                        'unit_cost': item['unit_cost'],
                        'opening_stock': opening_stock,
                        'purchased': purchased,
                        'sold': sold,
                        'waste': waste,
                        'closing_stock': max(0, closing_stock),
                        'stock_value': round(max(0, closing_stock) * item['unit_cost'], 2),
                    })

    return pd.DataFrame(rows)


def generate_investment_data():
    """Generate initial investment data per store for ROI calculations."""
    rng = _seed()
    stores = [c for c in STORE_LOCATIONS if c != "OOH"]

    rows = []
    for store in stores:
        sqm = STORE_LOCATIONS[store].get('sqm', 55)
        base_buildout = sqm * rng.uniform(1200, 1800)
        equipment = rng.uniform(25000, 45000)
        furniture = sqm * rng.uniform(150, 300)
        working_capital = rng.uniform(15000, 30000)
        total = base_buildout + equipment + furniture + working_capital

        rows.append({
            'store_code': store,
            'store_name': STORE_LOCATIONS[store]['name'],
            'city': STORE_LOCATIONS[store]['city'],
            'sqm': sqm,
            'opened': STORE_LOCATIONS[store].get('opened', '2022-01'),
            'buildout_cost': round(base_buildout, 0),
            'equipment_cost': round(equipment, 0),
            'furniture_cost': round(furniture, 0),
            'working_capital': round(working_capital, 0),
            'total_investment': round(total, 0),
        })

    return pd.DataFrame(rows)


def generate_impact_data(selected_years):
    """Generate Wakuli mission-aligned impact metrics."""
    rng = _seed()

    rows = []
    for year in selected_years:
        for month in range(1, 13):
            now = datetime.now()
            if year > now.year or (year == now.year and month > now.month):
                continue

            # Growth in impact over time
            months_since_start = (year - 2021) * 12 + month
            growth_factor = 1.0 + 0.02 * months_since_start

            kg_coffee = 2200 * growth_factor * rng.uniform(0.9, 1.1)
            direct_trade_pct = min(0.98, 0.80 + 0.001 * months_since_start + rng.uniform(-0.02, 0.02))
            farmers_supported = int(500 + 3 * months_since_start + rng.randint(-10, 10))
            farmer_premium = 0.30 + 0.001 * months_since_start + rng.uniform(-0.02, 0.02)
            market_price_per_kg = rng.uniform(4.50, 6.50)
            wakuli_price_per_kg = market_price_per_kg * (1 + farmer_premium)
            premium_paid = (wakuli_price_per_kg - market_price_per_kg) * kg_coffee * direct_trade_pct
            compostable_pct = min(0.98, 0.75 + 0.002 * months_since_start)
            co2_per_cup = max(55, 85 - 0.15 * months_since_start + rng.uniform(-3, 3))

            # Cups served (avg ~200g per kg for espresso drinks)
            cups_served = int(kg_coffee * 1000 / 18)  # ~18g per double shot

            rows.append({
                'year': year,
                'month': f'{year}-{month:02d}',
                'kg_coffee_sourced': round(kg_coffee, 1),
                'direct_trade_pct': round(direct_trade_pct, 3),
                'farmers_supported': farmers_supported,
                'farmer_premium_pct': round(farmer_premium, 3),
                'market_price_per_kg': round(market_price_per_kg, 2),
                'wakuli_price_per_kg': round(wakuli_price_per_kg, 2),
                'premium_paid_eur': round(premium_paid, 2),
                'compostable_packaging_pct': round(compostable_pct, 3),
                'co2_per_cup_grams': round(co2_per_cup, 1),
                'cups_served': cups_served,
            })

    return pd.DataFrame(rows)


def generate_budget_data():
    """Generate default budget data for all stores."""
    rng = _seed()
    stores = [c for c in STORE_LOCATIONS if c != "OOH"]

    budgets = {}
    for store in stores:
        sqm = STORE_LOCATIONS[store].get('sqm', 55)
        budget = round(sqm * rng.uniform(600, 1000), -3)
        budgets[store] = int(budget)

    budgets["OOH"] = 25000
    return budgets


def generate_all_demo_data(selected_years):
    """Generate all demo datasets and return as a dict."""
    revenue_df = generate_revenue_data(selected_years)
    cost_df = generate_cost_data(revenue_df)
    customer_df = generate_customer_data(revenue_df)
    labor_df = generate_labor_data(revenue_df)
    inventory_df = generate_inventory_data(selected_years)
    investment_df = generate_investment_data()
    impact_df = generate_impact_data(selected_years)
    capex_df = generate_capex_data(selected_years)
    budgets = generate_budget_data()

    return {
        'revenue': revenue_df,
        'costs': cost_df,
        'customers': customer_df,
        'labor': labor_df,
        'inventory': inventory_df,
        'investment': investment_df,
        'impact': impact_df,
        'capex': capex_df,
        'budgets': budgets,
    }
