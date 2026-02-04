"""
Wakuli Retail Analytics - Configuration
========================================
Central configuration for store data, account mappings, brand constants,
and all dashboard settings.

UPDATED: Feb 2026 - Corrected account codes for Wakuli Retail Holding (Odoo)
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
# ACCOUNT MAP — WAKULI RETAIL HOLDING (ACTUAL CODES)
# ──────────────────────────────────────────────
# Updated Feb 2026 with real Odoo account codes
#
# Structure:
#   section -> category_key -> {
#       "codes": list of Odoo account code patterns (uses =like, so "8%" matches all 8xxxxx)
#       "label": Display name in the dashboard
#       "sign":  "credit" = revenue, "debit" = expense, "abs" = absolute
#       "group": Optional grouping
#   }

ACCOUNT_MAP = {
    # ── REVENUE ──────────────────────────────────
    "revenue": {
        "coffee_beverages": {
            "codes": ["800601", "800611", "800621"],
            "label": "Omzet Dranken (Beverages)",
            "sign": "credit",
            "group": "revenue",
        },
        "coffee_retail": {
            "codes": ["800610"],
            "label": "Omzet Retail (Koffie/Bundel)",
            "sign": "credit",
            "group": "revenue",
        },
        "food_sales": {
            "codes": ["800620"],
            "label": "Omzet Eten (Food)",
            "sign": "credit",
            "group": "revenue",
        },
        "consumables": {
            "codes": ["800630"],
            "label": "Omzet Verbruiksartikelen",
            "sign": "credit",
            "group": "revenue",
        },
        "retail_noncoffee": {
            "codes": ["800640"],
            "label": "Omzet Retail (Non-Coffee)",
            "sign": "credit",
            "group": "revenue",
        },
        "merchandise": {
            "codes": ["800690"],
            "label": "Omzet Merchandise",
            "sign": "credit",
            "group": "revenue",
        },
        "workshops": {
            "codes": ["800660"],
            "label": "Omzet Workshops",
            "sign": "credit",
            "group": "revenue",
        },
        "equipment_sales": {
            "codes": ["800670"],
            "label": "Omzet Uitrusting",
            "sign": "credit",
            "group": "revenue",
        },
        "ingredients": {
            "codes": ["800600"],
            "label": "Omzet Ingredienten",
            "sign": "credit",
            "group": "revenue",
        },
        "discounts": {
            "codes": ["800650"],
            "label": "Omzet Discounts",
            "sign": "credit",
            "group": "revenue",
        },
        "deposit": {
            "codes": ["800680"],
            "label": "Omzet Statiegeld",
            "sign": "credit",
            "group": "revenue",
        },
        "other_revenue": {
            "codes": ["806500", "809000"],
            "label": "Overige Opbrengsten",
            "sign": "credit",
            "group": "revenue",
        },
    },

    # ── COST OF GOODS SOLD ───────────────────────
    "cogs": {
        "cogs_coffee": {
            "codes": ["700100"],
            "label": "COGS Coffee",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_roasting": {
            "codes": ["700101"],
            "label": "COGS Roasting",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_fb_ingredients": {
            "codes": ["700106"],
            "label": "COGS F&B Ingredients",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_cleaning": {
            "codes": ["700109"],
            "label": "COGS Cleaning & Inputs",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_transaction": {
            "codes": ["700134"],
            "label": "COGS Transaction Costs (Lightspeed)",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_discount": {
            "codes": ["706500"],
            "label": "Betalingskorting",
            "sign": "debit",
            "group": "cogs",
        },
        "cogs_waste": {
            "codes": ["709111"],
            "label": "Afgekeurde Voorraad (Waste)",
            "sign": "debit",
            "group": "cogs",
        },
    },

    # ── OPERATING EXPENSES ───────────────────────
    "opex": {
        # LABOR COSTS (400xxx - 409xxx)
        "labor_gross": {
            "codes": ["400100", "400200", "400300", "400400", "400500", "400600"],
            "label": "Bruto Loonkosten",
            "sign": "debit",
            "group": "labor",
            "is_fixed": False,
        },
        "labor_employer": {
            "codes": ["401000", "401100", "401200", "401500", "401600", "401700", "401800", "401900"],
            "label": "Werkgeverslasten",
            "sign": "debit",
            "group": "labor",
            "is_fixed": False,
        },
        "labor_external": {
            "codes": ["402000", "402100", "402200", "402400", "402900"],
            "label": "Ingeleend Personeel",
            "sign": "debit",
            "group": "labor",
            "is_fixed": False,
        },
        "labor_other": {
            "codes": ["403000", "403500", "404001", "404100", "404200", "404300", "404400", "404500", "409000"],
            "label": "Overige Personeelskosten",
            "sign": "debit",
            "group": "labor",
            "is_fixed": False,
        },
        "labor_bar": {
            "codes": ["408000", "408010", "408040", "408050"],
            "label": "Loonkosten Bar Personnel",
            "sign": "debit",
            "group": "labor",
            "is_fixed": False,
        },

        # OCCUPANCY / RENT (411xxx - 419xxx)
        "rent": {
            "codes": ["411001"],
            "label": "Huur Onroerend Goed",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "maintenance_property": {
            "codes": ["411101", "411201", "411301"],
            "label": "Onderhoud Onroerend Goed",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "property_tax": {
            "codes": ["412001"],
            "label": "Belastingen Onroerend Goed",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "utilities": {
            "codes": ["413001"],
            "label": "Energiekosten",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "cleaning": {
            "codes": ["414001"],
            "label": "Schoonmaakkosten",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "insurance_property": {
            "codes": ["415001"],
            "label": "Assurantie Onroerend Goed",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },
        "other_occupancy": {
            "codes": ["419001", "419002"],
            "label": "Overige Huisvestingskosten",
            "sign": "debit",
            "group": "occupancy",
            "is_fixed": True,
        },

        # EQUIPMENT (420xxx - 429xxx)
        "equipment_lease": {
            "codes": ["420100", "420200", "421000", "421100"],
            "label": "Huur/Lease Machines & Inventaris",
            "sign": "debit",
            "group": "equipment",
            "is_fixed": True,
        },
        "equipment_maintenance": {
            "codes": ["422000", "423000", "424000"],
            "label": "Onderhoud Machines & Inventaris",
            "sign": "debit",
            "group": "equipment",
            "is_fixed": False,
        },
        "equipment_other": {
            "codes": ["425001", "426001", "427001", "428001", "429001"],
            "label": "Overige Bedrijfskosten",
            "sign": "debit",
            "group": "equipment",
            "is_fixed": False,
        },

        # OFFICE / ADMIN (430xxx - 439xxx)
        "office_supplies": {
            "codes": ["430501", "431001"],
            "label": "Kantoorbenodigdheden",
            "sign": "debit",
            "group": "admin",
            "is_fixed": False,
        },
        "office_equipment": {
            "codes": ["432001", "432101", "432201"],
            "label": "Kantoorinventaris",
            "sign": "debit",
            "group": "admin",
            "is_fixed": False,
        },
        "telecom": {
            "codes": ["433001", "434001", "435001"],
            "label": "Telefoon/Internet/Porti",
            "sign": "debit",
            "group": "admin",
            "is_fixed": True,
        },
        "software": {
            "codes": ["436001"],
            "label": "Softwarekosten",
            "sign": "debit",
            "group": "admin",
            "is_fixed": True,
        },
        "other_office": {
            "codes": ["439001"],
            "label": "Overige Kantoorkosten",
            "sign": "debit",
            "group": "admin",
            "is_fixed": False,
        },

        # VEHICLES (440xxx - 442xxx)
        "vehicles": {
            "codes": ["440400", "441200", "441400", "442400"],
            "label": "Lease/Onderhoud Vervoer",
            "sign": "debit",
            "group": "vehicles",
            "is_fixed": True,
        },

        # TRAVEL & MARKETING (451xxx - 452xxx)
        "travel": {
            "codes": ["451000", "451500"],
            "label": "Reis- en Representatiekosten",
            "sign": "debit",
            "group": "marketing",
            "is_fixed": False,
        },
        "marketing": {
            "codes": ["452010"],
            "label": "Brand Marketing",
            "sign": "debit",
            "group": "marketing",
            "is_fixed": False,
        },

        # PROFESSIONAL SERVICES (460xxx - 469xxx)
        "accounting": {
            "codes": ["460100"],
            "label": "Accountantskosten",
            "sign": "debit",
            "group": "professional",
            "is_fixed": True,
        },
        "advisory": {
            "codes": ["460500"],
            "label": "Advieskosten",
            "sign": "debit",
            "group": "professional",
            "is_fixed": False,
        },
        "admin_services": {
            "codes": ["462100"],
            "label": "Administratiekosten",
            "sign": "debit",
            "group": "professional",
            "is_fixed": True,
        },
        "bank_fees": {
            "codes": ["463000"],
            "label": "Bankkosten",
            "sign": "debit",
            "group": "professional",
            "is_fixed": True,
        },
        "tax_assessments": {
            "codes": ["464000"],
            "label": "Naheffingen Belastingdienst",
            "sign": "debit",
            "group": "professional",
            "is_fixed": False,
        },
        "other_general": {
            "codes": ["469000"],
            "label": "Overige Algemene Kosten",
            "sign": "debit",
            "group": "professional",
            "is_fixed": False,
        },

        # DEPRECIATION (480xxx - 483xxx)
        "depreciation_capex": {
            "codes": ["481000"],
            "label": "Afschrijving CAPEX",
            "sign": "debit",
            "group": "depreciation",
            "is_fixed": True,
        },
        "depreciation_machines": {
            "codes": ["482000"],
            "label": "Afschrijving Koffiemachines",
            "sign": "debit",
            "group": "depreciation",
            "is_fixed": True,
        },
        "depreciation_inventory": {
            "codes": ["483000"],
            "label": "Afschrijving Inventaris",
            "sign": "debit",
            "group": "depreciation",
            "is_fixed": True,
        },

        # OTHER
        "payment_differences": {
            "codes": ["493000"],
            "label": "Betalingsverschillen",
            "sign": "debit",
            "group": "other",
            "is_fixed": False,
        },
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
        "depreciation_capex": {
            "codes": ["037900"],
            "label": "Afschrijving CAPEX Winkels",
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
    """Return +1 or -1 based on entry's sign convention."""
    sign = entry.get("sign", "abs")
    if sign == "credit":
        return -1
    elif sign == "debit":
        return 1
    return 0

# ──────────────────────────────────────────────
# PRODUCT CATEGORIES (for revenue breakdown)
# ──────────────────────────────────────────────
PRODUCT_CATEGORIES = {
    "coffee": {"label": "Coffee & Espresso", "icon": "coffee", "target_cogs_pct": 0.28},
    "food": {"label": "Food & Pastries", "icon": "cake", "target_cogs_pct": 0.32},
    "merchandise": {"label": "Merchandise", "icon": "shopping_bag", "target_cogs_pct": 0.45},
    "retail": {"label": "Retail Products", "icon": "store", "target_cogs_pct": 0.40},
    "other": {"label": "Other", "icon": "more_horiz", "target_cogs_pct": 0.35},
}

# Maps revenue ACCOUNT_MAP keys to product category keys
REVENUE_TO_PRODUCT_CATEGORY = {
    "coffee_beverages": "coffee",
    "coffee_retail": "retail",
    "food_sales": "food",
    "consumables": "other",
    "retail_noncoffee": "retail",
    "merchandise": "merchandise",
    "workshops": "other",
    "equipment_sales": "other",
    "ingredients": "other",
    "discounts": "other",
    "deposit": "other",
    "other_revenue": "other",
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
STORE_INVESTMENTS = {
    # Fill in actual buildout costs per store for ROI calculations
}

# ──────────────────────────────────────────────
# ODOO OPTIONAL MODULES
# ──────────────────────────────────────────────
ODOO_MODULES = {
    "pos": False,
    "hr": False,
    "stock": False,
    "asset": False,
}

# ──────────────────────────────────────────────
# NMBRS (VISMA) HR/PAYROLL CONFIGURATION
# ──────────────────────────────────────────────
NMBRS_CONFIG = {
    "enabled": True,
    "companies": {
        # Nmbrs company ID → display label
        # Use Settings tab to discover company IDs
    },
    "full_time_hours": 40,
    "employer_burden_pct": 0.30,
}

NMBRS_DEPARTMENT_TO_STORE = {
    "Linnaeusstraat": "LIN",
    "Jan Pieter Heijestraat": "JPH",
    "Haarlemmerplein": "HAP",
    "Wagenaarstraat": "WAG",
    "Amstelveenseweg": "AMS",
    "Vijzelgracht": "VIJZ",
    "Twijnstraat": "TWIJN",
    "Ziekerstraat": "ZIEK",
    "Van Woustraat": "WOU",
    "Nobelstraat": "NOB",
    "Jacob van Campenstraat": "JAC",
    "Bajes": "BAJES",
    "Fahrenheitstraat": "FAH",
    "Meent": "MEENT",
    "Lusthofstraat": "LUST",
    "Visstraat": "VIS",
    "Theresiastraat": "THER",
    "Piet Heinstraat": "PIET",
    "Haarlemmerstraat": "HAS",
    "Stoeldraaierstraat": "STOEL",
    "Overhead": "OOH",
    "Head Office": "OOH",
    "Hoofdkantoor": "OOH",
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
