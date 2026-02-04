"""
Wakuli Retail Analytics - Configuration
========================================
Central configuration for store data, account mappings, brand constants,
and all dashboard settings.
"""

# ──────────────────────────────────────────────
# WAKULI BRAND PALETTE
# ──────────────────────────────────────────────
COLORS = {
    "orange": "#FF6B35",
    "orange_light": "#FF8066",
    "teal": "#004E64",
    "teal_light": "#006D8F",
    "yellow": "#F7B801",
    "green": "#25A18E",
    "green_dark": "#1B7A6B",
    "cream": "#FCF6F5",
    "charcoal": "#2D3142",
    "grey_light": "#E8E8E8",
    "grey_medium": "#B0B0B0",
    "white": "#FFFFFF",
    "red": "#E63946",
    "red_light": "#FF6B6B",
}

# Chart color sequences for Plotly
CHART_COLORS = [
    "#FF6B35", "#004E64", "#25A18E", "#F7B801",
    "#FF8066", "#006D8F", "#1B7A6B", "#2D3142",
    "#E63946", "#B0B0B0",
]

CHART_COLORS_WARM = ["#FF6B35", "#FF8066", "#F7B801", "#25A18E", "#004E64"]
CHART_COLORS_COOL = ["#004E64", "#006D8F", "#25A18E", "#1B7A6B", "#2D3142"]

# Positive / negative indicators
COLOR_POSITIVE = "#25A18E"
COLOR_NEGATIVE = "#E63946"
COLOR_NEUTRAL = "#B0B0B0"
COLOR_WARNING = "#F7B801"

# ──────────────────────────────────────────────
# STORE LOCATIONS
# ──────────────────────────────────────────────
STORE_LOCATIONS = {
    "LIN": {"name": "Linnaeusstraat", "address": "Linnaeusstraat 237a", "city": "Amsterdam", "lat": 52.3579, "lon": 4.9274, "sqm": 65, "opened": "2021-03"},
    "JPH": {"name": "Jan Pieter Heijestraat", "address": "Jan Pieter Heijestraat 76", "city": "Amsterdam", "lat": 52.3627, "lon": 4.8583, "sqm": 55, "opened": "2021-06"},
    "HAP": {"name": "Haarlemmerplein", "address": "Haarlemmerplein 43", "city": "Amsterdam", "lat": 52.3847, "lon": 4.8819, "sqm": 70, "opened": "2021-09"},
    "WAG": {"name": "Wagenaarstraat", "address": "Wagenaarstraat 70H", "city": "Amsterdam", "lat": 52.3615, "lon": 4.9285, "sqm": 48, "opened": "2022-01"},
    "AMS": {"name": "Amstelveenseweg", "address": "Amstelveenseweg 210", "city": "Amsterdam", "lat": 52.3489, "lon": 4.8658, "sqm": 60, "opened": "2022-03"},
    "VIJZ": {"name": "Vijzelgracht", "address": "Vijzelgracht 37H", "city": "Amsterdam", "lat": 52.3630, "lon": 4.8908, "sqm": 75, "opened": "2022-06"},
    "TWIJN": {"name": "Twijnstraat", "address": "Twijnstraat 1", "city": "Utrecht", "lat": 52.0894, "lon": 5.1180, "sqm": 50, "opened": "2022-09"},
    "ZIEK": {"name": "Ziekerstraat", "address": "Ziekerstraat 169", "city": "Nijmegen", "lat": 51.8463, "lon": 5.8642, "sqm": 55, "opened": "2023-01"},
    "WOU": {"name": "Van Woustraat", "address": "Van Woustraat 54", "city": "Amsterdam", "lat": 52.3530, "lon": 4.9040, "sqm": 58, "opened": "2023-03"},
    "NOB": {"name": "Nobelstraat", "address": "Nobelstraat 143", "city": "Utrecht", "lat": 52.0907, "lon": 5.1230, "sqm": 62, "opened": "2023-05"},
    "JAC": {"name": "Jacob van Campenstraat", "address": "Tweede Jacob van Campenstraat 1", "city": "Amsterdam", "lat": 52.3505, "lon": 4.8925, "sqm": 45, "opened": "2023-07"},
    "BAJES": {"name": "Bajes", "address": "H.J.E. Wenckebachweg 48", "city": "Amsterdam", "lat": 52.3456, "lon": 4.9356, "sqm": 80, "opened": "2023-09"},
    "FAH": {"name": "Fahrenheitstraat", "address": "Fahrenheitstraat 496", "city": "Den Haag", "lat": 52.0705, "lon": 4.2805, "sqm": 52, "opened": "2023-11"},
    "MEENT": {"name": "Meent", "address": "Meent 3A", "city": "Rotterdam", "lat": 51.9225, "lon": 4.4792, "sqm": 68, "opened": "2024-01"},
    "LUST": {"name": "Lusthofstraat", "address": "Lusthofstraat 54B", "city": "Rotterdam", "lat": 51.9178, "lon": 4.4935, "sqm": 50, "opened": "2024-03"},
    "VIS": {"name": "Visstraat", "address": "Visstraat 4", "city": "Den Bosch", "lat": 51.6878, "lon": 5.3069, "sqm": 55, "opened": "2024-06"},
    "THER": {"name": "Theresiastraat", "address": "Theresiastraat 108", "city": "Den Haag", "lat": 52.0763, "lon": 4.3015, "sqm": 60, "opened": "2024-08"},
    "PIET": {"name": "Piet Heinstraat", "address": "Piet Heinstraat 84", "city": "Den Haag", "lat": 52.0716, "lon": 4.3132, "sqm": 50, "opened": "2024-10"},
    "HAS": {"name": "Haarlemmerstraat", "address": "Haarlemmerstraat 127", "city": "Leiden", "lat": 52.1601, "lon": 4.4894, "sqm": 55, "opened": "2025-01"},
    "STOEL": {"name": "Stoeldraaierstraat", "address": "Stoeldraaierstraat 70", "city": "Groningen", "lat": 53.2171, "lon": 6.5613, "sqm": 58, "opened": "2025-03"},
    "OOH": {"name": "Overhead (All Stores)", "address": "Central Office", "city": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "sqm": 0, "opened": "2021-01"},
}

# Odoo analytics IDs
STORE_ODOO_IDS = {
    "LIN": 17046, "JPH": 17047, "HAP": 17048, "WAG": 17049, "AMS": 17050,
    "VIJZ": 17051, "TWIJN": 17052, "ZIEK": 17053, "WOU": 17054, "NOB": 17055,
    "JAC": 22869, "BAJES": 28826, "FAH": 18393, "MEENT": 53942, "LUST": 51003,
    "VIS": 58577, "THER": 58498, "PIET": 58578, "HAS": 58596, "STOEL": 58603,
    "OOH": 19878,
}

ODOO_ID_TO_STORE = {v: k for k, v in STORE_ODOO_IDS.items()}

# ──────────────────────────────────────────────
# ACCOUNT MAPPINGS
# ──────────────────────────────────────────────

# CAPEX accounts
CAPEX_ACCOUNTS = {
    "037000": "CAPEX Winkels (Store Renovations)",
    "032000": "WIA - Assets Under Construction",
    "031000": "Bedrijfsinventaris (Business Inventory)",
    "021000": "Koffiemachines (Coffee Machines)",
    "013000": "Verbouwingen (Renovations)",
}

# Revenue accounts (for expanded dashboard)
REVENUE_ACCOUNTS = {
    "800000": "Coffee Sales",
    "800100": "Food Sales",
    "800200": "Merchandise Sales",
    "800300": "Subscription Revenue",
    "800400": "Delivery Revenue",
}

# Cost accounts
COST_ACCOUNTS = {
    "400000": "Cost of Goods - Coffee",
    "400100": "Cost of Goods - Food",
    "400200": "Cost of Goods - Merchandise",
    "410000": "Labor Costs",
    "420000": "Rent & Occupancy",
    "430000": "Utilities",
    "440000": "Marketing & Advertising",
    "450000": "Equipment Maintenance",
    "460000": "Supplies & Consumables",
    "470000": "Insurance & Licenses",
}

# Wakuli Retail Holding company ID in Odoo
RETAIL_HOLDING_ID = 2

# ──────────────────────────────────────────────
# PRODUCT CATEGORIES
# ──────────────────────────────────────────────
PRODUCT_CATEGORIES = {
    "coffee": {"label": "Coffee & Espresso", "icon": "coffee", "target_cogs_pct": 0.28},
    "food": {"label": "Food & Pastries", "icon": "cake", "target_cogs_pct": 0.32},
    "merchandise": {"label": "Merchandise", "icon": "shopping_bag", "target_cogs_pct": 0.45},
    "subscription": {"label": "Subscriptions", "icon": "autorenew", "target_cogs_pct": 0.25},
}

# ──────────────────────────────────────────────
# DAYPART DEFINITIONS
# ──────────────────────────────────────────────
DAYPARTS = {
    "early_morning": {"label": "Early Morning", "hours": (6, 9), "color": "#F7B801"},
    "morning": {"label": "Morning Rush", "hours": (9, 12), "color": "#FF6B35"},
    "afternoon": {"label": "Afternoon", "hours": (12, 15), "color": "#004E64"},
    "late_afternoon": {"label": "Late Afternoon", "hours": (15, 18), "color": "#25A18E"},
    "evening": {"label": "Evening", "hours": (18, 21), "color": "#2D3142"},
}

# ──────────────────────────────────────────────
# KPI TARGETS & BENCHMARKS
# ──────────────────────────────────────────────
TARGETS = {
    "gross_margin_pct": 0.68,          # 68% target
    "net_margin_pct": 0.12,            # 12% target
    "labor_cost_pct": 0.30,            # 30% of revenue
    "rent_cost_pct": 0.12,             # 12% of revenue
    "food_cost_pct": 0.30,             # 30% COGS ratio
    "beverage_cost_pct": 0.25,         # 25% COGS ratio
    "avg_transaction_value": 6.50,     # EUR
    "revenue_per_sqm_month": 650,      # EUR/sqm/month
    "revenue_per_labor_hour": 55,      # EUR
    "customer_retention_pct": 0.45,    # 45% returning
    "inventory_turnover": 24,          # times per year
    "break_even_months": 18,           # months to break-even
}

# ──────────────────────────────────────────────
# IMPACT METRICS (Wakuli mission)
# ──────────────────────────────────────────────
IMPACT_DEFAULTS = {
    "farmer_premium_pct": 0.35,        # 35% above market price
    "direct_trade_pct": 0.92,          # 92% directly sourced
    "farmers_supported": 847,
    "countries_sourced": 8,
    "compostable_packaging_pct": 0.88,
    "co2_per_cup_grams": 68,           # grams CO2 per cup
    "kg_coffee_per_month": 2800,       # kg across all stores
}

# Coffee sourcing origins
SOURCING_ORIGINS = [
    {"country": "Ethiopia", "region": "Yirgacheffe", "lat": 6.16, "lon": 38.20, "farmers": 234, "pct": 0.28},
    {"country": "Colombia", "region": "Huila", "lat": 2.53, "lon": -75.53, "farmers": 156, "pct": 0.18},
    {"country": "Kenya", "region": "Nyeri", "lat": -0.42, "lon": 36.95, "farmers": 98, "pct": 0.12},
    {"country": "Rwanda", "region": "Nyamasheke", "lat": -2.35, "lon": 29.13, "farmers": 112, "pct": 0.13},
    {"country": "Indonesia", "region": "Sumatra", "lat": 2.52, "lon": 98.58, "farmers": 87, "pct": 0.10},
    {"country": "Guatemala", "region": "Antigua", "lat": 14.56, "lon": -90.73, "farmers": 72, "pct": 0.09},
    {"country": "Brazil", "region": "Minas Gerais", "lat": -18.51, "lon": -44.55, "farmers": 56, "pct": 0.07},
    {"country": "Uganda", "region": "Mt. Elgon", "lat": 1.13, "lon": 34.53, "farmers": 32, "pct": 0.03},
]

# ──────────────────────────────────────────────
# APP CONFIGURATION
# ──────────────────────────────────────────────
APP_CONFIG = {
    "page_title": "Wakuli Retail Analytics",
    "page_icon": "☕",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "cache_ttl_auth": 600,
    "cache_ttl_data": 300,
    "max_odoo_records": 10000,
}
