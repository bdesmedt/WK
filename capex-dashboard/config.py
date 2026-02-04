"""
Wakuli Retail Analytics - Configuration
========================================
Central configuration for store data, account mappings, brand constants,
and all dashboard settings.

HOW TO CONFIGURE FOR YOUR ODOO INSTANCE
-----------------------------------------
1. Run the "Account Explorer" diagnostic (Settings tab in dashboard sidebar)
   to discover your actual Odoo chart of accounts.
2. Update ACCOUNT_MAP below with real account code patterns.
3. Each entry uses Odoo's =like operator: '8%' matches 800000, 801000, etc.
   Use exact codes like '800000' for precision, or prefixes like '8%' for ranges.
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

CHART_COLORS = [
    "#FF6B35", "#004E64", "#25A18E", "#F7B801",
    "#FF8066", "#006D8F", "#1B7A6B", "#2D3142",
    "#E63946", "#B0B0B0",
]

CHART_COLORS_WARM = ["#FF6B35", "#FF8066", "#F7B801", "#25A18E", "#004E64"]
CHART_COLORS_COOL = ["#004E64", "#006D8F", "#25A18E", "#1B7A6B", "#2D3142"]

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

# Odoo analytics IDs (analytic_distribution keys in account.move.line)
STORE_ODOO_IDS = {
    "LIN": 17046, "JPH": 17047, "HAP": 17048, "WAG": 17049, "AMS": 17050,
    "VIJZ": 17051, "TWIJN": 17052, "ZIEK": 17053, "WOU": 17054, "NOB": 17055,
    "JAC": 22869, "BAJES": 28826, "FAH": 18393, "MEENT": 53942, "LUST": 51003,
    "VIS": 58577, "THER": 58498, "PIET": 58578, "HAS": 58596, "STOEL": 58603,
    "OOH": 19878,
}

ODOO_ID_TO_STORE = {v: k for k, v in STORE_ODOO_IDS.items()}

# Wakuli Retail Holding company ID in Odoo
RETAIL_HOLDING_ID = 2


# ──────────────────────────────────────────────
# ACCOUNT MAP — THE CORE CONFIGURATION
# ──────────────────────────────────────────────
# This is the single source of truth that maps Odoo account codes to
# dashboard categories. Edit this to match your actual chart of accounts.
#
# Structure:
#   section -> category_key -> {
#       "codes": list of Odoo account code patterns (uses =like, so "8%" matches 800000)
#       "label": Display name in the dashboard
#       "sign":  How to interpret the balance field:
#                "credit"  = revenue (positive amount = credit balance)
#                "debit"   = expense (positive amount = debit balance)
#                "abs"     = use absolute value (for CAPEX/asset entries)
#       "group": Optional grouping for roll-ups (e.g. "cogs", "opex", "fixed")
#   }
#
# To discover your actual account codes, use the Account Explorer in the
# dashboard sidebar, or query Odoo:
#   Accounting > Configuration > Chart of Accounts

ACCOUNT_MAP = {
    # ── REVENUE ──────────────────────────────────
    # All revenue accounts. The dashboard sums these for total revenue,
    # and breaks down by category for the Revenue Analytics tab.
    "revenue": {
        "coffee_sales": {
            "codes": ["800000"],
            "label": "Coffee Sales",
            "sign": "credit",
            "group": "revenue",
        },
        "food_sales": {
            "codes": ["800100"],
            "label": "Food Sales",
            "sign": "credit",
            "group": "revenue",
        },
        "merchandise_sales": {
            "codes": ["800200"],
            "label": "Merchandise Sales",
            "sign": "credit",
            "group": "revenue",
        },
        "subscription_revenue": {
            "codes": ["800300"],
            "label": "Subscription Revenue",
            "sign": "credit",
            "group": "revenue",
        },
        "delivery_revenue": {
            "codes": ["800400"],
            "label": "Delivery Revenue",
            "sign": "credit",
            "group": "revenue",
        },
        # CATCH-ALL: Uncomment to pick up any revenue account by prefix:
        # "other_revenue": {
        #     "codes": ["8%"],
        #     "label": "Other Revenue",
        #     "sign": "credit",
        #     "group": "revenue",
        # },
    },

    # ── COST OF GOODS SOLD ───────────────────────
    # Direct costs tied to products sold.
    "cogs": {
        "cogs_coffee": {
            "codes": ["400000"],
            "label": "COGS - Coffee Beans",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_food": {
            "codes": ["400100"],
            "label": "COGS - Food & Bakery",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_merchandise": {
            "codes": ["400200"],
            "label": "COGS - Merchandise",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_packaging": {
            "codes": ["400300"],
            "label": "COGS - Packaging",
            "sign": "debit",
            "group": "cogs",
        },
        # CATCH-ALL: Uncomment to pick up any COGS account by prefix:
        # "cogs_other": {
        #     "codes": ["40%"],
        #     "label": "COGS - Other",
        #     "sign": "debit",
        #     "group": "cogs",
        # },
    },

    # ── OPERATING EXPENSES ───────────────────────
    # Non-COGS operating costs. Each maps to a cost_category used by the
    # KPI engine to calculate labor%, rent%, etc.
    "opex": {
        "labor": {
            "codes": ["410000"],
            "label": "Labor Costs",
            "sign": "debit",
            "group": "opex",
            "is_fixed": False,
        },
        "rent": {
            "codes": ["420000"],
            "label": "Rent & Occupancy",
            "sign": "debit",
            "group": "opex",
            "is_fixed": True,
        },
        "utilities": {
            "codes": ["430000"],
            "label": "Utilities",
            "sign": "debit",
            "group": "opex",
            "is_fixed": True,
        },
        "marketing": {
            "codes": ["440000"],
            "label": "Marketing & Advertising",
            "sign": "debit",
            "group": "opex",
            "is_fixed": False,
        },
        "maintenance": {
            "codes": ["450000"],
            "label": "Equipment Maintenance",
            "sign": "debit",
            "group": "opex",
            "is_fixed": False,
        },
        "supplies": {
            "codes": ["460000"],
            "label": "Supplies & Consumables",
            "sign": "debit",
            "group": "opex",
            "is_fixed": False,
        },
        "insurance": {
            "codes": ["470000"],
            "label": "Insurance & Licenses",
            "sign": "debit",
            "group": "opex",
            "is_fixed": True,
        },
        "depreciation": {
            "codes": ["480000"],
            "label": "Depreciation & Amortization",
            "sign": "debit",
            "group": "opex",
            "is_fixed": True,
        },
        # CATCH-ALL: Uncomment to pick up any OpEx account by prefix:
        # "opex_other": {
        #     "codes": ["4%"],
        #     "label": "Other OpEx",
        #     "sign": "debit",
        #     "group": "opex",
        #     "is_fixed": False,
        # },
    },

    # ── CAPEX (already working) ──────────────────
    "capex": {
        "capex_stores": {
            "codes": ["037000"],
            "label": "CAPEX Winkels (Store Renovations)",
            "sign": "abs",
            "group": "capex",
        },
        "wia": {
            "codes": ["032000"],
            "label": "WIA - Assets Under Construction",
            "sign": "abs",
            "group": "capex",
        },
        "business_inventory": {
            "codes": ["031000"],
            "label": "Bedrijfsinventaris (Business Inventory)",
            "sign": "abs",
            "group": "capex",
        },
        "coffee_machines": {
            "codes": ["021000"],
            "label": "Koffiemachines (Coffee Machines)",
            "sign": "abs",
            "group": "capex",
        },
        "renovations": {
            "codes": ["013000"],
            "label": "Verbouwingen (Renovations)",
            "sign": "abs",
            "group": "capex",
        },
    },
}

# Convenience: flat dict of CAPEX account code -> label (used by sidebar checkboxes)
CAPEX_ACCOUNTS = {
    code: entry["label"]
    for entry in ACCOUNT_MAP["capex"].values()
    for code in entry["codes"]
}


def get_all_account_codes(section):
    """Get all account code patterns for a given section of the ACCOUNT_MAP."""
    codes = []
    for entry in ACCOUNT_MAP.get(section, {}).values():
        codes.extend(entry["codes"])
    return codes


def get_category_for_account_code(raw_code, section=None):
    """Given an Odoo account code string, find the matching category key.

    Tries exact match first, then prefix matching (longest prefix wins).
    Returns (section, category_key, entry_dict) or (None, None, None).
    """
    sections_to_search = [section] if section else list(ACCOUNT_MAP.keys())
    best_match = (None, None, None)
    best_match_len = 0

    for sec in sections_to_search:
        for cat_key, entry in ACCOUNT_MAP.get(sec, {}).items():
            for pattern in entry["codes"]:
                # Convert Odoo =like pattern to a prefix for matching
                prefix = pattern.rstrip('%')
                if raw_code.startswith(prefix) and len(prefix) > best_match_len:
                    best_match = (sec, cat_key, entry)
                    best_match_len = len(prefix)
                # Exact match always wins
                if raw_code == pattern:
                    return (sec, cat_key, entry)

    return best_match


def get_sign_multiplier(entry):
    """Return +1 or -1 based on entry's sign convention.

    - "credit": use credit - debit (positive for revenue)
    - "debit":  use debit - credit (positive for expenses)
    - "abs":    use absolute value of balance
    """
    sign = entry.get("sign", "abs")
    if sign == "credit":
        return -1  # balance = debit - credit, so negate for revenue
    elif sign == "debit":
        return 1
    return 0  # "abs" handled separately


# ──────────────────────────────────────────────
# PRODUCT CATEGORIES (for revenue breakdown)
# ──────────────────────────────────────────────
# Maps revenue account category keys to product labels
PRODUCT_CATEGORIES = {
    "coffee": {"label": "Coffee & Espresso", "icon": "coffee", "target_cogs_pct": 0.28},
    "food": {"label": "Food & Pastries", "icon": "cake", "target_cogs_pct": 0.32},
    "merchandise": {"label": "Merchandise", "icon": "shopping_bag", "target_cogs_pct": 0.45},
    "subscription": {"label": "Subscriptions", "icon": "autorenew", "target_cogs_pct": 0.25},
}

# Maps revenue ACCOUNT_MAP keys to product category keys (for category breakdown charts)
REVENUE_TO_PRODUCT_CATEGORY = {
    "coffee_sales": "coffee",
    "food_sales": "food",
    "merchandise_sales": "merchandise",
    "subscription_revenue": "subscription",
    "delivery_revenue": "coffee",  # delivery is mostly coffee
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
    "gross_margin_pct": 0.68,
    "net_margin_pct": 0.12,
    "labor_cost_pct": 0.30,
    "rent_cost_pct": 0.12,
    "food_cost_pct": 0.30,
    "beverage_cost_pct": 0.25,
    "avg_transaction_value": 6.50,
    "revenue_per_sqm_month": 650,
    "revenue_per_labor_hour": 55,
    "customer_retention_pct": 0.45,
    "inventory_turnover": 24,
    "break_even_months": 18,
}

# ──────────────────────────────────────────────
# IMPACT METRICS (Wakuli mission)
# ──────────────────────────────────────────────
IMPACT_DEFAULTS = {
    "farmer_premium_pct": 0.35,
    "direct_trade_pct": 0.92,
    "farmers_supported": 847,
    "countries_sourced": 8,
    "compostable_packaging_pct": 0.88,
    "co2_per_cup_grams": 68,
    "kg_coffee_per_month": 2800,
}

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
# INVESTMENT DATA PER STORE (manual input)
# ──────────────────────────────────────────────
# Fill these in with actual buildout costs. Used for ROI and break-even.
# Set to 0 or omit stores where data is unknown.
STORE_INVESTMENTS = {
    # "LIN": {"buildout": 75000, "equipment": 35000, "furniture": 12000, "working_capital": 20000},
    # "JPH": {"buildout": 65000, "equipment": 32000, "furniture": 10000, "working_capital": 18000},
    # ... fill in per store
}


# ──────────────────────────────────────────────
# ODOO OPTIONAL MODULES
# ──────────────────────────────────────────────
# Set these to True if the corresponding Odoo modules are installed.
# The dashboard will attempt to query these models for richer data.
ODOO_MODULES = {
    "pos": False,        # Odoo Point of Sale (pos.order, pos.order.line)
    "hr": False,         # Odoo HR / Payroll (hr.employee)
    "stock": False,      # Odoo Inventory (stock.move, stock.valuation.layer)
    "asset": False,      # Odoo Assets (account.asset)
}


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
