"""
E-Commerce Analytics Dashboard
================================
A professional Streamlit dashboard built on top of the data_loader and
business_metrics modules extracted from the EDA notebook.

Run with:  streamlit run app.py
"""

import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import data_loader as dl
import business_metrics as bm

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="stMetric"] label {
    color: #64748b;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.65rem;
    font-weight: 700;
    color: #1e293b;
}

/* Bottom cards wrapper */
.bottom-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 24px 28px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    height: 170px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.bottom-card .card-label {
    color: #64748b;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
}
.bottom-card .card-value {
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 2px;
}
.bottom-card .card-delta-positive {
    color: #16a34a;
    font-size: 0.9rem;
    font-weight: 600;
}
.bottom-card .card-delta-negative {
    color: #dc2626;
    font-size: 0.9rem;
    font-weight: 600;
}
.bottom-card .card-subtitle {
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 2px;
}
.stars {
    color: #f59e0b;
    font-size: 1.3rem;
    letter-spacing: 2px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def fmt_currency_short(value):
    """Format a number as $1.2M or $300K."""
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:,.0f}K"
    return f"${value:,.0f}"


def fmt_delta(value):
    """Format a fractional delta as +12.34% / -2.10%."""
    if math.isnan(value):
        return "N/A"
    pct = value * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def delta_color(value):
    """Return 'normal' (green ↑ / red ↓) or 'off' for NaN."""
    if math.isnan(value):
        return "off"
    return "normal"


def render_stars(score, max_stars=5):
    """Return filled/empty star HTML string."""
    filled = round(score)
    return "".join(
        "\u2605" if i < filled else "\u2606" for i in range(max_stars)
    )


# ── Load & cache data ───────────────────────────────────────────────────────

@st.cache_data
def load_all_data():
    datasets = dl.load_datasets("ecommerce_data")
    orders = dl.parse_order_dates(datasets["orders"])
    order_items = datasets["order_items"]
    products = datasets["products"]
    customers = datasets["customers"]
    reviews = datasets["reviews"]

    sales_data = dl.build_sales_data(order_items, orders)
    delivered_all = dl.filter_delivered(sales_data)
    delivered_all = dl.add_delivery_speed(delivered_all)

    return orders, order_items, products, customers, reviews, delivered_all


orders, order_items, products, customers, reviews, delivered_all = load_all_data()

# ── Header row ───────────────────────────────────────────────────────────────

min_date = delivered_all["order_purchase_timestamp"].min().date()
max_date = delivered_all["order_purchase_timestamp"].max().date()

header_left, header_right = st.columns([3, 2])

with header_left:
    st.markdown("## E-Commerce Analytics Dashboard")

with header_right:
    date_cols = st.columns(2)
    with date_cols[0]:
        start_date = st.date_input("Start date", value=pd.Timestamp("2023-01-01").date(),
                                   min_value=min_date, max_value=max_date)
    with date_cols[1]:
        end_date = st.date_input("End date", value=max_date,
                                 min_value=min_date, max_value=max_date)

st.markdown("---")

# ── Filter data by selected range ───────────────────────────────────────────

delivered_current = dl.filter_by_date_range(delivered_all, str(start_date), str(end_date))

# Build a comparison period of equal length directly before start_date
period_days = (end_date - start_date).days
comparison_end = start_date - pd.Timedelta(days=1)
comparison_start = comparison_end - pd.Timedelta(days=period_days)
delivered_previous = dl.filter_by_date_range(
    delivered_all,
    str(comparison_start),
    str(comparison_end),
)

has_comparison = len(delivered_previous) > 0

# ── KPI Row ──────────────────────────────────────────────────────────────────

rev_current = bm.total_revenue(delivered_current)
rev_change = bm.revenue_growth(delivered_current, delivered_previous) if has_comparison else float("nan")

avg_mom = bm.average_mom_growth(delivered_current) if len(delivered_current) > 0 else float("nan")

aov_current = bm.average_order_value(delivered_current) if len(delivered_current) > 0 else 0.0
aov_change = bm.aov_growth(delivered_current, delivered_previous) if has_comparison else float("nan")

orders_current = bm.total_orders(delivered_current)
orders_change = bm.order_count_growth(delivered_current, delivered_previous) if has_comparison else float("nan")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        label="Total Revenue",
        value=fmt_currency_short(rev_current),
        delta=fmt_delta(rev_change),
        delta_color=delta_color(rev_change),
    )
with kpi2:
    st.metric(
        label="Monthly Growth (Avg MoM)",
        value=fmt_delta(avg_mom),
    )
with kpi3:
    st.metric(
        label="Average Order Value",
        value=f"${aov_current:,.2f}",
        delta=fmt_delta(aov_change),
        delta_color=delta_color(aov_change),
    )
with kpi4:
    st.metric(
        label="Total Orders",
        value=f"{orders_current:,}",
        delta=fmt_delta(orders_change),
        delta_color=delta_color(orders_change),
    )

st.markdown("")

# ── Charts Grid (2x2) ───────────────────────────────────────────────────────

chart_top_left, chart_top_right = st.columns(2)

# -- Revenue trend line chart --------------------------------------------------
with chart_top_left:
    monthly_current = bm.monthly_revenue(delivered_current)
    monthly_current["period"] = "month"
    monthly_current["label"] = monthly_current["month"].apply(
        lambda m: pd.Timestamp(2000, int(m), 1).strftime("%b")
    )

    fig_rev = go.Figure()

    # Previous period (dashed)
    if has_comparison:
        monthly_prev = bm.monthly_revenue(delivered_previous)
        monthly_prev["label"] = monthly_prev["month"].apply(
            lambda m: pd.Timestamp(2000, int(m), 1).strftime("%b")
        )
        fig_rev.add_trace(go.Scatter(
            x=monthly_prev["label"],
            y=monthly_prev["revenue"],
            mode="lines+markers",
            name="Previous Period",
            line=dict(dash="dash", color="#94a3b8", width=2),
            marker=dict(size=5, color="#94a3b8"),
            hovertemplate="%{x}: %{y:$,.0f}<extra>Previous</extra>",
        ))

    # Current period (solid)
    fig_rev.add_trace(go.Scatter(
        x=monthly_current["label"],
        y=monthly_current["revenue"],
        mode="lines+markers",
        name="Current Period",
        line=dict(color="#2C6E91", width=3),
        marker=dict(size=7, color="#2C6E91"),
        hovertemplate="%{x}: %{y:$,.0f}<extra>Current</extra>",
    ))

    fig_rev.update_layout(
        title="Revenue Trend",
        xaxis_title="Month",
        yaxis_title="Revenue",
        yaxis_tickformat="$,.0s",
        yaxis=dict(
            gridcolor="#f1f5f9",
            gridwidth=1,
            tickprefix="$",
            tickformat=".2s",
        ),
        xaxis=dict(gridcolor="#f1f5f9", gridwidth=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        height=380,
    )
    st.plotly_chart(fig_rev, use_container_width=True)

# -- Top 10 categories bar chart -----------------------------------------------
with chart_top_right:
    cat_rev = bm.revenue_by_category(delivered_current, products).head(10)

    # Build blue gradient: darker for higher values
    max_val = cat_rev.max() if len(cat_rev) > 0 else 1
    bar_colors = [
        f"rgba(44, 110, 145, {0.35 + 0.65 * (v / max_val)})"
        for v in cat_rev.values
    ]

    fig_cat = go.Figure(go.Bar(
        x=cat_rev.values,
        y=cat_rev.index,
        orientation="h",
        marker_color=bar_colors,
        hovertemplate="%{y}: %{x:$,.0f}<extra></extra>",
    ))

    fig_cat.update_layout(
        title="Top 10 Product Categories",
        xaxis_title="Revenue",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(
            gridcolor="#f1f5f9",
            tickprefix="$",
            tickformat=".2s",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        height=380,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

chart_bot_left, chart_bot_right = st.columns(2)

# -- US choropleth map ---------------------------------------------------------
with chart_bot_left:
    state_revenue = bm.revenue_by_state(delivered_current, orders, customers)

    fig_map = px.choropleth(
        state_revenue,
        locations="customer_state",
        color="revenue",
        locationmode="USA-states",
        scope="usa",
        color_continuous_scale=[
            [0, "#d4e8f0"],
            [0.35, "#6dafc9"],
            [0.7, "#2C6E91"],
            [1, "#123a50"],
        ],
        labels={"revenue": "Revenue", "customer_state": "State"},
    )
    fig_map.update_layout(
        title="Revenue by State",
        geo=dict(
            lakecolor="white",
            bgcolor="white",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=50, b=0),
        height=380,
        coloraxis_colorbar=dict(
            tickprefix="$",
            tickformat=".2s",
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True)

# -- Satisfaction vs Delivery Time bar chart ------------------------------------
with chart_bot_right:
    review_summary = bm.review_delivery_summary(delivered_current, reviews)
    by_bucket = bm.avg_review_by_delivery_bucket(review_summary)

    # Ensure correct bucket ordering
    bucket_order = ["1-3 days", "4-7 days", "8+ days"]
    by_bucket["delivery_bucket"] = pd.Categorical(
        by_bucket["delivery_bucket"], categories=bucket_order, ordered=True
    )
    by_bucket = by_bucket.sort_values("delivery_bucket")

    fig_sat = go.Figure(go.Bar(
        x=by_bucket["delivery_bucket"],
        y=by_bucket["avg_review_score"],
        marker_color=["#2C6E91", "#5a9ec2", "#94c4df"],
        text=by_bucket["avg_review_score"].round(2),
        textposition="outside",
        hovertemplate="%{x}: %{y:.2f}<extra></extra>",
    ))

    fig_sat.update_layout(
        title="Satisfaction vs Delivery Time",
        xaxis_title="Delivery Time",
        yaxis_title="Avg Review Score",
        yaxis=dict(range=[0, 5.5], gridcolor="#f1f5f9", dtick=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        height=380,
    )
    st.plotly_chart(fig_sat, use_container_width=True)

# ── Bottom Row ───────────────────────────────────────────────────────────────

avg_delivery = bm.average_delivery_days(review_summary) if len(review_summary) > 0 else 0.0
avg_review = bm.average_review_score(review_summary) if len(review_summary) > 0 else 0.0

# Comparison-period delivery/review metrics
if has_comparison:
    review_summary_prev = bm.review_delivery_summary(delivered_previous, reviews)
    avg_delivery_prev = bm.average_delivery_days(review_summary_prev) if len(review_summary_prev) > 0 else 0.0
    delivery_change = (avg_delivery - avg_delivery_prev) / avg_delivery_prev if avg_delivery_prev else float("nan")
else:
    delivery_change = float("nan")

bot_left, bot_right = st.columns(2)

with bot_left:
    # For delivery time, lower is better, so invert the arrow logic
    if not math.isnan(delivery_change):
        pct = delivery_change * 100
        # Negative change = faster delivery = good (green)
        if pct <= 0:
            delta_cls = "card-delta-positive"
            arrow = "&#9660;"  # down arrow (good for delivery time)
        else:
            delta_cls = "card-delta-negative"
            arrow = "&#9650;"  # up arrow (bad for delivery time)
        delta_html = f'<div class="{delta_cls}">{arrow} {abs(pct):.2f}% vs previous period</div>'
    else:
        delta_html = '<div class="card-subtitle">No comparison data</div>'

    st.markdown(f"""
    <div class="bottom-card">
        <div class="card-label">Average Delivery Time</div>
        <div class="card-value">{avg_delivery:.1f} days</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

with bot_right:
    stars_html = render_stars(avg_review)
    st.markdown(f"""
    <div class="bottom-card">
        <div class="card-label">Average Review Score</div>
        <div class="card-value">{avg_review:.2f} / 5.00</div>
        <div class="stars">{stars_html}</div>
        <div class="card-subtitle">Based on {len(review_summary):,} reviews</div>
    </div>
    """, unsafe_allow_html=True)
