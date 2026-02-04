# ☕ Wakuli CAPEX Budget Dashboard

A Streamlit dashboard for tracking construction budgets vs actuals for Wakuli coffee bar renovations.

![Wakuli Logo](https://www.wakuli.com/cdn/shop/files/logo_green.png?v=1719823287&width=200)

## Features

- 📊 **Real-time Dashboard** - View CAPEX spending across all stores
- 💰 **Budget Management** - Set and track budgets per store
- 🗺️ **Store Map** - Interactive map of all 20+ Wakuli locations
- 📈 **Variance Analysis** - Track budget vs actual with visual indicators
- 📋 **Detailed Data** - Export transactions to CSV

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/bdesmedt/WK.git
cd WK/capex-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Odoo credentials:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Odoo credentials
```

4. Run the app:
```bash
streamlit run app.py
```

### Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set secrets in the Streamlit Cloud dashboard:
   - `ODOO_URL`
   - `ODOO_DB`
   - `ODOO_USER`
   - `ODOO_PASSWORD`

## Configuration

### Odoo Connection

The dashboard connects to Odoo via XML-RPC API. You need:
- Odoo URL (e.g., `https://wakuli.odoo.com`)
- Database name
- User email
- API key (generate in Odoo: User → Preferences → API Keys)

### Tracked Accounts

By default, the dashboard tracks these CAPEX accounts:
- **037000** - CAPEX Winkels (Store Renovations)
- **032000** - WIA (Assets Under Construction)
- **031000** - Bedrijfsinventaris (Business Inventory)
- **021000** - Koffiemachines (Coffee Machines)
- **013000** - Verbouwingen (Renovations)

### Store Mapping

All 21 Wakuli store locations are pre-configured with:
- Address and city
- GPS coordinates for map
- Odoo analytic account IDs

## Screenshots

### Dashboard
Track spending and variances at a glance.

### Budget Management
Set annual budgets per store with quick templates.

### Store Map
Visualize CAPEX distribution across the Netherlands.

## Security Notes

- Never commit `secrets.toml` to git
- Use Streamlit Cloud secrets for production
- Consider using a dedicated service account with limited Odoo permissions

## Support

For questions or issues, contact: accounting@fidfinance.nl

---

Built with ❤️ for Wakuli by FidFinance
