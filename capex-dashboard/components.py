"""
Wakuli Retail Analytics - UI Components
=========================================
Reusable, branded UI components for the dashboard.
All components follow the Wakuli design system.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import streamlit.components.v1 as html_components
from config import COLORS, CHART_COLORS, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING


# ──────────────────────────────────────────────
# METRIC CARDS
# ──────────────────────────────────────────────

def metric_card(label, value, delta=None, delta_suffix="", color="orange", prefix="", tooltip=None):
    """Render a branded metric card with optional delta indicator.

    Args:
        label: Metric name (e.g. "Total Revenue")
        value: Formatted value string (e.g. "EUR 1.2M")
        delta: Delta value (positive = good by default)
        delta_suffix: Text after delta (e.g. "%" or "vs target")
        color: Card accent color (orange, teal, green, yellow, red)
        prefix: Currency/unit prefix for value
        tooltip: Optional explanatory text
    """
    delta_html = ""
    if delta is not None:
        delta_class = "positive" if delta >= 0 else "negative"
        arrow = "&#9650;" if delta >= 0 else "&#9660;"
        delta_html = f'<div class="metric-delta {delta_class}">{arrow} {delta:+.1f}{delta_suffix}</div>'

    tooltip_html = ""
    if tooltip:
        tooltip_html = f'<div class="tooltip-box">{tooltip}</div>'

    color_class = color if color in ('teal', 'green', 'yellow', 'red') else ''
    value_class = f'metric-value {color_class}' if color_class else 'metric-value'
    card_class = f'metric-card {color_class}' if color_class else 'metric-card'

    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-label">{label}</div>
        <div class="{value_class}">{prefix}{value}</div>
        {delta_html}
        {tooltip_html}
    </div>
    """, unsafe_allow_html=True)


def impact_card(number, label, suffix=""):
    """Render a mission-aligned impact card (dark background, gold numbers)."""
    st.markdown(f"""
    <div class="impact-card">
        <div class="impact-number">{number}{suffix}</div>
        <div class="impact-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


def progress_bar(value, max_value, label="", color="orange"):
    """Render a branded progress bar."""
    pct = min(100, (value / max_value * 100)) if max_value > 0 else 0
    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #2D3142;">
            <span>{label}</span>
            <span style="font-weight: 700;">{pct:.0f}%</span>
        </div>
        <div class="progress-container">
            <div class="progress-fill {color}" style="width: {pct}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_header(title, subtitle=None):
    """Render a branded section header."""
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def badge(text, status="good"):
    """Render a status badge. status: good, warning, danger."""
    return f'<span class="badge {status}">{text}</span>'


# ──────────────────────────────────────────────
# CHART HELPERS
# ──────────────────────────────────────────────

def apply_brand_layout(fig, height=400, title=None, show_legend=True):
    """Apply Wakuli brand styling to any Plotly figure."""
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(family="Poppins", size=16, color=COLORS['charcoal'])) if title else None,
        font=dict(family="Poppins", color=COLORS['charcoal']),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=show_legend,
        legend=dict(font=dict(size=11)),
        margin=dict(l=40, r=20, t=50 if title else 20, b=40),
        xaxis=dict(gridcolor=COLORS['grey_light'], showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=COLORS['grey_light'], showgrid=True, zeroline=False),
    )
    return fig


def waterfall_chart(categories, values, title=None, height=400):
    """Create a waterfall chart for P&L / cost breakdown."""
    colors = [COLOR_POSITIVE if v >= 0 else COLOR_NEGATIVE for v in values]

    fig = go.Figure(go.Waterfall(
        x=categories,
        y=values,
        connector=dict(line=dict(color=COLORS['grey_medium'])),
        increasing=dict(marker=dict(color=COLOR_POSITIVE)),
        decreasing=dict(marker=dict(color=COLOR_NEGATIVE)),
        totals=dict(marker=dict(color=COLORS['orange'])),
        textposition="outside",
        text=[f"\u20ac{abs(v):,.0f}" for v in values],
    ))

    return apply_brand_layout(fig, height=height, title=title, show_legend=False)


def gauge_chart(value, target, title, suffix="%", min_val=0, max_val=100):
    """Create a gauge chart for KPI vs target."""
    color = COLOR_POSITIVE if value >= target else (COLOR_WARNING if value >= target * 0.9 else COLOR_NEGATIVE)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number=dict(suffix=suffix, font=dict(size=28, family="Poppins", color=COLORS['charcoal'])),
        delta=dict(reference=target, suffix=suffix, font=dict(size=14)),
        gauge=dict(
            axis=dict(range=[min_val, max_val], tickfont=dict(size=10)),
            bar=dict(color=color, thickness=0.75),
            bgcolor=COLORS['grey_light'],
            borderwidth=0,
            threshold=dict(
                line=dict(color=COLORS['charcoal'], width=2),
                thickness=0.8,
                value=target,
            ),
        ),
        title=dict(text=title, font=dict(size=13, family="Poppins")),
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Poppins"),
    )
    return fig


def donut_chart(labels, values, title=None, height=350):
    """Create a branded donut chart."""
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=CHART_COLORS[:len(labels)]),
        textinfo='percent+label',
        textfont=dict(size=11, family="Poppins"),
        hovertemplate='%{label}<br>\u20ac%{value:,.0f}<br>%{percent}<extra></extra>',
    ))

    return apply_brand_layout(fig, height=height, title=title, show_legend=False)


def bar_chart(df, x, y, color=None, title=None, height=400, orientation='v',
              color_sequence=None, barmode='group', text_auto=False):
    """Create a branded bar chart."""
    colors = color_sequence or CHART_COLORS

    fig = px.bar(
        df, x=x, y=y, color=color, orientation=orientation,
        color_discrete_sequence=colors, barmode=barmode, text_auto=text_auto,
    )

    return apply_brand_layout(fig, height=height, title=title)


def line_chart(df, x, y, color=None, title=None, height=400, color_sequence=None):
    """Create a branded line/area chart."""
    colors = color_sequence or CHART_COLORS

    fig = px.line(
        df, x=x, y=y, color=color,
        color_discrete_sequence=colors, markers=True,
    )
    fig.update_traces(line=dict(width=3))

    return apply_brand_layout(fig, height=height, title=title)


def area_chart(df, x, y, color=None, title=None, height=400, color_sequence=None):
    """Create a branded area chart."""
    colors = color_sequence or CHART_COLORS

    fig = px.area(
        df, x=x, y=y, color=color,
        color_discrete_sequence=colors,
    )

    return apply_brand_layout(fig, height=height, title=title)


# ──────────────────────────────────────────────
# INVOICE / DETAIL VIEWS
# ──────────────────────────────────────────────

def render_invoice_popup(db, uid, password, move_id, move_name):
    """Render invoice detail view inside an expander."""
    from odoo_connector import fetch_invoice_details, fetch_invoice_pdf

    move, lines = fetch_invoice_details(db, uid, password, move_id)

    if not move:
        st.warning("Could not load invoice details.")
        return

    cols = st.columns([2, 1, 1, 1])
    with cols[0]:
        st.markdown(f"**Invoice/Entry:** {move.get('name', 'N/A')}")
        partner = move.get('partner_id')
        if partner:
            st.markdown(f"**Partner:** {partner[1] if isinstance(partner, list) else partner}")
    with cols[1]:
        st.markdown(f"**Date:** {move.get('date', 'N/A')}")
        st.markdown(f"**Due:** {move.get('invoice_date_due', 'N/A')}")
    with cols[2]:
        st.markdown(f"**State:** {move.get('state', 'N/A')}")
        type_labels = {
            'out_invoice': 'Customer Invoice', 'in_invoice': 'Vendor Bill',
            'out_refund': 'Credit Note', 'in_refund': 'Vendor Credit', 'entry': 'Journal Entry',
        }
        st.markdown(f"**Type:** {type_labels.get(move.get('move_type', ''), move.get('move_type', ''))}")
    with cols[3]:
        total = move.get('amount_total', 0)
        st.metric("Total", f"\u20ac{total:,.2f}")

    ref = move.get('ref', '')
    if ref:
        st.markdown(f"**Reference:** {ref}")

    if lines:
        line_data = []
        for l in lines:
            acc = l.get('account_id', [None, ''])
            acc_name = acc[1] if isinstance(acc, list) and len(acc) > 1 else str(acc)
            prod = l.get('product_id', [None, ''])
            prod_name = prod[1] if isinstance(prod, list) and len(prod) > 1 else ''
            line_data.append({
                'Account': acc_name, 'Description': l.get('name', ''),
                'Product': prod_name, 'Qty': l.get('quantity', 0),
                'Unit Price': l.get('price_unit', 0),
                'Debit': l.get('debit', 0), 'Credit': l.get('credit', 0),
            })
        st.dataframe(
            pd.DataFrame(line_data), use_container_width=True, hide_index=True,
            column_config={
                'Debit': st.column_config.NumberColumn(format='\u20ac%.2f'),
                'Credit': st.column_config.NumberColumn(format='\u20ac%.2f'),
                'Unit Price': st.column_config.NumberColumn(format='\u20ac%.2f'),
            },
        )

    pdf_data = fetch_invoice_pdf(db, uid, password, move_id)
    if pdf_data and pdf_data.get('datas'):
        st.divider()
        st.markdown(f"**Attachment:** {pdf_data.get('name', 'document.pdf')}")
        pdf_bytes = base64.b64decode(pdf_data['datas'])
        st.download_button(
            label="Download PDF", data=pdf_bytes,
            file_name=pdf_data.get('name', 'invoice.pdf'),
            mime='application/pdf', key=f"pdf_dl_{move_id}",
        )
        b64 = pdf_data['datas']
        pdf_html = f"""
        <iframe id="pdfViewer_{move_id}" width="100%" height="580" style="border:none;"></iframe>
        <script>
            const b64 = "{b64}";
            const byteChars = atob(b64);
            const byteNums = new Uint8Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) {{ byteNums[i] = byteChars.charCodeAt(i); }}
            const blob = new Blob([byteNums], {{type: 'application/pdf'}});
            document.getElementById('pdfViewer_{move_id}').src = URL.createObjectURL(blob);
        </script>
        """
        html_components.html(pdf_html, height=600)


# ──────────────────────────────────────────────
# FORMAT HELPERS
# ──────────────────────────────────────────────

def fmt_eur(value, decimals=0):
    """Format a number as EUR currency."""
    if abs(value) >= 1_000_000:
        return f"\u20ac{value/1_000_000:,.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"\u20ac{value/1_000:,.{decimals}f}K"
    return f"\u20ac{value:,.{decimals}f}"


def fmt_pct(value, decimals=1):
    """Format a number as percentage."""
    return f"{value:,.{decimals}f}%"


def fmt_number(value, decimals=0):
    """Format a plain number with thousand separators."""
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:,.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:,.{decimals}f}K"
    return f"{value:,.{decimals}f}"
