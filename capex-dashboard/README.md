# Wakuli Retail Analytics - CFO Dashboard

A comprehensive financial analytics platform for Wakuli coffee stores.
Calculates ROI, profitability, revenue metrics, cost analysis,
operational efficiency, and mission-aligned impact KPIs.

**Brewing Profit with Purpose.**

![Wakuli Logo](https://www.wakuli.com/cdn/shop/files/logo_green.png?v=1719823287&width=200)

## Features

### 9 Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Executive Summary** | Hero KPIs, revenue trend, profitability waterfall, impact spotlight |
| **Financial Deep Dive** | Store ROI, break-even analysis, P&L gauges, cash flow trend |
| **Revenue Analytics** | Revenue by category/channel/store, daypart analysis, growth metrics |
| **Cost & Efficiency** | Cost structure, labor productivity, inventory management |
| **Customers** | CLV, CAC, retention rate, new vs returning, per-store metrics |
| **CAPEX Tracking** | Budget vs actual, account breakdown, invoice viewer (Odoo) |
| **Impact Dashboard** | Farmer premium, sourcing origins map, sustainability progress |
| **Store Map** | Interactive Netherlands map with revenue overlay |
| **Benchmarks** | Store ranking, margin comparison, YoY growth, same-store sales |

### Key KPIs Calculated

- **ROI**: Per-store return on investment (cumulative and annualized)
- **Break-Even**: Months to payback, contribution margin
- **Profitability**: Gross margin, net margin, EBITDA, OpEx ratio
- **Revenue**: Per sqm, per labor hour, by category/channel/daypart, growth rates
- **Costs**: Full cost structure with % of revenue, benchmark targets
- **Labor**: Revenue per labor hour, labor cost %, FTE efficiency
- **Inventory**: Turnover ratio, waste rate, days inventory outstanding
- **Customers**: CLV, CAC, CLV:CAC ratio, retention rate, visit frequency
- **Cash Flow**: Operating CF, cumulative CF trend
- **Impact**: Farmers supported, premium paid, direct trade %, CO2 per cup

## Architecture

```
capex-dashboard/
├── app.py               # Main Streamlit application (routing + tab rendering)
├── config.py            # Store data, account mappings, brand constants, targets
├── styles.py            # Wakuli brand CSS (Poppins, orange/teal palette)
├── odoo_connector.py    # Odoo XML-RPC API communication
├── demo_data.py         # Comprehensive demo data generator
├── kpi_engine.py        # All KPI calculations (documented formulas)
├── components.py        # Reusable branded UI components
├── requirements.txt     # Python dependencies
└── .streamlit/
    └── secrets.toml.example  # Odoo credentials template
```

## Quick Start

### Local Development

```bash
git clone https://github.com/bdesmedt/WK.git
cd WK/capex-dashboard
pip install -r requirements.txt
streamlit run app.py
```

The dashboard runs in **demo mode** by default with realistic sample data.

### Connect to Odoo (Live Data)

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Odoo credentials
```

### Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set secrets in the Streamlit Cloud dashboard

## Brand Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Vibrant Orange | `#FF6B35` | Primary brand, CTAs, highlights |
| Deep Teal | `#004E64` | Secondary, headers, depth |
| Bright Yellow | `#F7B801` | Accents, alerts, positive metrics |
| Forest Green | `#25A18E` | Sustainability, positive deltas |
| Cream | `#FCF6F5` | Backgrounds |
| Charcoal | `#2D3142` | Text, data labels |

### Typography

- **Font**: Poppins (Google Fonts)
- **Headers**: Bold 700-800, large sizing
- **Body**: Regular 400, 16px base

## Tracked Accounts (CAPEX)

| Code | Description |
|------|-------------|
| 037000 | CAPEX Winkels (Store Renovations) |
| 032000 | WIA - Assets Under Construction |
| 031000 | Bedrijfsinventaris (Business Inventory) |
| 021000 | Koffiemachines (Coffee Machines) |
| 013000 | Verbouwingen (Renovations) |

## Store Locations

21 Wakuli store locations across the Netherlands:
Amsterdam (8), Utrecht (2), Rotterdam (2), Den Haag (3), Nijmegen, Den Bosch, Leiden, Groningen + Central Office.

## KPI Formula Reference

### ROI
```
ROI = (Cumulative Net Profit / Total Investment) x 100
Net Profit = Revenue - Total Costs
Annualized ROI = (ROI / Months Operating) x 12
```

### Break-Even
```
Break-Even Revenue = Fixed Costs / (1 - Variable Cost Ratio)
Months to Payback = Total Investment / Avg Monthly Net Profit
Contribution Margin = 1 - Variable Cost Ratio
```

### Profitability
```
Gross Margin = (Revenue - COGS) / Revenue x 100
Net Margin = (Revenue - All Costs) / Revenue x 100
EBITDA = Net Profit + Depreciation
OpEx Ratio = (Total Costs - COGS) / Revenue x 100
```

### Customer
```
CAC = Marketing Spend / New Customers
CLV = Avg Revenue per Customer x Estimated Lifespan
CLV:CAC Ratio = CLV / CAC (target: >3x)
```

### Labor
```
Revenue per Labor Hour = Revenue / Total Labor Hours
Labor Cost % = Labor Costs / Revenue x 100
```

### Inventory
```
Turnover Ratio = COGS / Average Inventory Value
Days Inventory Outstanding = Avg Stock Value / Daily COGS
Waste Rate = Waste / (Sold + Waste) x 100
```

## Security Notes

- Never commit `secrets.toml` to git
- Use Streamlit Cloud secrets for production
- Consider a dedicated service account with limited Odoo permissions

## Support

For questions or issues, contact: accounting@fidfinance.nl

---

Built with purpose for Wakuli by FidFinance
