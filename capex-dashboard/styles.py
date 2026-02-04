"""
Wakuli Retail Analytics - Brand Styling
========================================
Complete Wakuli brand CSS with orange/teal palette, Poppins typography,
and all component styles for the CFO dashboard.
"""


def get_brand_css():
    """Return the complete Wakuli brand CSS stylesheet."""
    return """
<style>
    /* ── Google Fonts Import ── */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

    /* ── Global Overrides ── */
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
    }

    .stApp {
        background-color: #FCF6F5;
    }

    /* ── Main Header ── */
    .hero-header {
        font-family: 'Poppins', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #2D3142;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .hero-header span {
        color: #FF6B35;
    }
    .hero-tagline {
        font-family: 'Poppins', sans-serif;
        font-size: 1.1rem;
        font-weight: 400;
        color: #004E64;
        margin-top: 4px;
        opacity: 0.85;
    }

    /* ── Section Headers ── */
    .section-header {
        font-family: 'Poppins', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #2D3142;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.4rem;
        border-bottom: 3px solid #FF6B35;
        display: inline-block;
    }
    .section-subtitle {
        font-family: 'Poppins', sans-serif;
        font-size: 0.95rem;
        color: #004E64;
        margin-top: 0;
        margin-bottom: 1rem;
        font-weight: 400;
    }

    /* ── Metric Cards ── */
    .metric-card {
        background: #FFFFFF;
        padding: 1.2rem 1.4rem;
        border-radius: 12px;
        border-left: 5px solid #FF6B35;
        box-shadow: 0 2px 8px rgba(45, 49, 66, 0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 0.8rem;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(45, 49, 66, 0.14);
    }
    .metric-card.teal {
        border-left-color: #004E64;
    }
    .metric-card.green {
        border-left-color: #25A18E;
    }
    .metric-card.yellow {
        border-left-color: #F7B801;
    }
    .metric-card.red {
        border-left-color: #E63946;
    }

    .metric-label {
        font-family: 'Poppins', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: #004E64;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .metric-value {
        font-family: 'Poppins', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #FF6B35;
        line-height: 1.1;
    }
    .metric-value.teal {
        color: #004E64;
    }
    .metric-value.green {
        color: #25A18E;
    }
    .metric-delta {
        font-family: 'Poppins', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-delta.positive {
        color: #25A18E;
    }
    .metric-delta.negative {
        color: #E63946;
    }
    .metric-delta.neutral {
        color: #B0B0B0;
    }

    /* ── KPI Row ── */
    .kpi-row {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .kpi-item {
        flex: 1;
        min-width: 160px;
    }

    /* ── Impact Cards (Mission Metrics) ── */
    .impact-card {
        background: linear-gradient(135deg, #004E64 0%, #006D8F 100%);
        color: white;
        padding: 1.4rem;
        border-radius: 12px;
        box-shadow: 0 3px 12px rgba(0, 78, 100, 0.25);
        text-align: center;
    }
    .impact-card .impact-number {
        font-family: 'Poppins', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #F7B801;
        line-height: 1.1;
    }
    .impact-card .impact-label {
        font-family: 'Poppins', sans-serif;
        font-size: 0.85rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 4px;
    }

    /* ── Store Cards ── */
    .store-card {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
        margin-bottom: 0.6rem;
        border-left: 4px solid #25A18E;
        transition: transform 0.15s ease;
    }
    .store-card:hover {
        transform: translateX(4px);
    }
    .store-card strong {
        color: #2D3142;
        font-weight: 700;
    }
    .store-card .store-amount {
        color: #FF6B35;
        font-weight: 700;
        font-size: 1.05rem;
    }

    /* ── Tabs Styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 4px;
        box-shadow: 0 1px 4px rgba(45, 49, 66, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        color: #004E64;
        border-radius: 8px;
        padding: 8px 16px;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF6B35 !important;
        color: white !important;
        border-radius: 8px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #004E64 0%, #2D3142 100%);
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #FCF6F5 !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
        color: white;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.15);
    }
    [data-testid="stSidebar"] .stCheckbox label span {
        color: #FCF6F5 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        border-radius: 8px;
        border: none;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(255, 107, 53, 0.3);
    }
    .stButton > button[kind="primary"] {
        background-color: #FF6B35;
        color: white;
    }

    /* ── Data Tables ── */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 1px 6px rgba(45, 49, 66, 0.08);
    }

    /* ── Dividers ── */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #FF6B35, #004E64, #25A18E);
        opacity: 0.3;
        margin: 1.5rem 0;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #004E64;
        background-color: #FFFFFF;
        border-radius: 8px;
    }

    /* ── Tooltips / Info Boxes ── */
    .tooltip-box {
        background: #FCF6F5;
        border: 1px solid #E8E8E8;
        border-left: 4px solid #F7B801;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.85rem;
        color: #2D3142;
        margin: 0.5rem 0;
    }

    /* ── Progress Bars ── */
    .progress-container {
        background: #E8E8E8;
        border-radius: 6px;
        height: 10px;
        overflow: hidden;
        margin-top: 6px;
    }
    .progress-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.6s ease;
    }
    .progress-fill.orange { background: #FF6B35; }
    .progress-fill.green { background: #25A18E; }
    .progress-fill.red { background: #E63946; }
    .progress-fill.teal { background: #004E64; }

    /* ── Invoice Modal ── */
    .invoice-modal {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #E8E8E8;
        box-shadow: 0 4px 12px rgba(45, 49, 66, 0.1);
        margin: 1rem 0;
    }

    /* ── Alert / Status Badges ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .badge.good { background: #E8F5E9; color: #25A18E; }
    .badge.warning { background: #FFF8E1; color: #F7B801; }
    .badge.danger { background: #FFEBEE; color: #E63946; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #FCF6F5; }
    ::-webkit-scrollbar-thumb { background: #004E64; border-radius: 3px; }

    /* ── Responsive Tweaks ── */
    @media (max-width: 768px) {
        .hero-header { font-size: 1.8rem; }
        .metric-value { font-size: 1.4rem; }
        .section-header { font-size: 1.3rem; }
    }
</style>
"""
