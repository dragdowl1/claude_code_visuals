"""
Business metric calculations for e-commerce EDA.

All functions accept filtered pandas DataFrames and return plain
Python values or DataFrames -- they do not produce plots.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Revenue metrics
# ---------------------------------------------------------------------------

def total_revenue(delivered):
    """Sum of item prices for delivered orders.

    Parameters
    ----------
    delivered : pd.DataFrame
        Delivered-sales rows (must contain a ``price`` column).

    Returns
    -------
    float
    """
    return float(delivered["price"].sum())


def revenue_growth(current_period, previous_period):
    """Percentage revenue change between two periods.

    Parameters
    ----------
    current_period : pd.DataFrame
    previous_period : pd.DataFrame

    Returns
    -------
    float
        Fractional change (e.g. -0.025 means -2.5 %).
    """
    current = total_revenue(current_period)
    previous = total_revenue(previous_period)
    if previous == 0:
        return float("nan")
    return (current - previous) / previous


def monthly_revenue(delivered):
    """Monthly total revenue for a set of delivered-sales rows.

    Parameters
    ----------
    delivered : pd.DataFrame
        Must contain ``year``, ``month``, and ``price`` columns.

    Returns
    -------
    pd.DataFrame
        Columns: year, month, revenue.
    """
    result = (
        delivered
        .groupby(["year", "month"])["price"]
        .sum()
        .reset_index()
        .rename(columns={"price": "revenue"})
    )
    return result


def month_over_month_growth(delivered):
    """Month-over-month revenue growth rates.

    Parameters
    ----------
    delivered : pd.DataFrame

    Returns
    -------
    pd.Series
        Indexed by month, values are fractional changes.
    """
    monthly = delivered.groupby("month")["price"].sum()
    return monthly.pct_change()


def average_mom_growth(delivered):
    """Average month-over-month growth rate (excludes NaN for first month).

    Parameters
    ----------
    delivered : pd.DataFrame

    Returns
    -------
    float
    """
    return float(month_over_month_growth(delivered).mean())


# ---------------------------------------------------------------------------
# Order metrics
# ---------------------------------------------------------------------------

def total_orders(delivered):
    """Count of unique orders.

    Parameters
    ----------
    delivered : pd.DataFrame

    Returns
    -------
    int
    """
    return int(delivered["order_id"].nunique())


def order_count_growth(current_period, previous_period):
    """Percentage change in order count between two periods.

    Parameters
    ----------
    current_period : pd.DataFrame
    previous_period : pd.DataFrame

    Returns
    -------
    float
    """
    current = total_orders(current_period)
    previous = total_orders(previous_period)
    if previous == 0:
        return float("nan")
    return (current - previous) / previous


def average_order_value(delivered):
    """Average revenue per order (sum of item prices grouped by order_id).

    Parameters
    ----------
    delivered : pd.DataFrame

    Returns
    -------
    float
    """
    return float(delivered.groupby("order_id")["price"].sum().mean())


def aov_growth(current_period, previous_period):
    """Percentage change in average order value between two periods.

    Parameters
    ----------
    current_period : pd.DataFrame
    previous_period : pd.DataFrame

    Returns
    -------
    float
    """
    current = average_order_value(current_period)
    previous = average_order_value(previous_period)
    if previous == 0:
        return float("nan")
    return (current - previous) / previous


# ---------------------------------------------------------------------------
# Order-status distribution
# ---------------------------------------------------------------------------

def order_status_distribution(orders, year):
    """Normalized value counts of order_status for a given year.

    Parameters
    ----------
    orders : pd.DataFrame
        Full orders table with datetime ``order_purchase_timestamp``.
    year : int

    Returns
    -------
    pd.Series
        Index: order_status, values: proportions.
    """
    orders = orders.copy()
    if not pd.api.types.is_datetime64_any_dtype(orders["order_purchase_timestamp"]):
        orders["order_purchase_timestamp"] = pd.to_datetime(
            orders["order_purchase_timestamp"], errors="coerce"
        )
    mask = orders["order_purchase_timestamp"].dt.year == year
    return orders.loc[mask, "order_status"].value_counts(normalize=True)


# ---------------------------------------------------------------------------
# Product / category metrics
# ---------------------------------------------------------------------------

def revenue_by_category(delivered, products):
    """Total revenue per product category.

    Parameters
    ----------
    delivered : pd.DataFrame
        Must contain ``product_id`` and ``price``.
    products : pd.DataFrame
        Must contain ``product_id`` and ``product_category_name``.

    Returns
    -------
    pd.Series
        Indexed by product_category_name, sorted descending.
    """
    merged = pd.merge(
        products[["product_id", "product_category_name"]],
        delivered[["product_id", "price"]],
        on="product_id",
    )
    return (
        merged
        .groupby("product_category_name")["price"]
        .sum()
        .sort_values(ascending=False)
    )


# ---------------------------------------------------------------------------
# Geographic metrics
# ---------------------------------------------------------------------------

def revenue_by_state(delivered, orders, customers):
    """Total revenue per customer state.

    Parameters
    ----------
    delivered : pd.DataFrame
        Must contain ``order_id`` and ``price``.
    orders : pd.DataFrame
        Must contain ``order_id`` and ``customer_id``.
    customers : pd.DataFrame
        Must contain ``customer_id`` and ``customer_state``.

    Returns
    -------
    pd.DataFrame
        Columns: customer_state, revenue. Sorted descending by revenue.
    """
    sales_customers = pd.merge(
        delivered[["order_id", "price"]],
        orders[["order_id", "customer_id"]],
        on="order_id",
    )
    sales_states = pd.merge(
        sales_customers,
        customers[["customer_id", "customer_state"]],
        on="customer_id",
    )
    result = (
        sales_states
        .groupby("customer_state")["price"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"price": "revenue"})
    )
    return result


# ---------------------------------------------------------------------------
# Customer-experience metrics
# ---------------------------------------------------------------------------

def categorize_delivery_speed(days):
    """Bin delivery days into human-readable buckets.

    Parameters
    ----------
    days : int or float

    Returns
    -------
    str
        One of '1-3 days', '4-7 days', '8+ days'.
    """
    if days <= 3:
        return "1-3 days"
    if days <= 7:
        return "4-7 days"
    return "8+ days"


def review_delivery_summary(delivered, reviews):
    """Build a per-order summary with delivery days, review score, and bucket.

    Parameters
    ----------
    delivered : pd.DataFrame
        Must contain ``order_id``, ``delivery_days``.
    reviews : pd.DataFrame
        Must contain ``order_id``, ``review_score``.

    Returns
    -------
    pd.DataFrame
        Unique order-level rows with columns: order_id, delivery_days,
        review_score, delivery_bucket.
    """
    merged = delivered.merge(reviews[["order_id", "review_score"]], on="order_id")
    summary = (
        merged[["order_id", "delivery_days", "review_score"]]
        .drop_duplicates()
    )
    summary = summary.copy()
    summary["delivery_bucket"] = summary["delivery_days"].apply(
        categorize_delivery_speed
    )
    return summary


def avg_review_by_delivery_bucket(review_summary):
    """Average review score per delivery-speed bucket.

    Parameters
    ----------
    review_summary : pd.DataFrame
        Output of ``review_delivery_summary``.

    Returns
    -------
    pd.DataFrame
        Columns: delivery_bucket, avg_review_score.
    """
    return (
        review_summary
        .groupby("delivery_bucket")["review_score"]
        .mean()
        .reset_index()
        .rename(columns={"review_score": "avg_review_score"})
    )


def avg_review_by_delivery_day(review_summary):
    """Average review score per delivery day.

    Parameters
    ----------
    review_summary : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        Columns: delivery_days, avg_review_score.
    """
    return (
        review_summary
        .groupby("delivery_days")["review_score"]
        .mean()
        .reset_index()
        .rename(columns={"review_score": "avg_review_score"})
    )


def review_score_distribution(review_summary):
    """Normalized distribution of review scores.

    Parameters
    ----------
    review_summary : pd.DataFrame

    Returns
    -------
    pd.Series
        Index: review_score (1-5), values: proportions.
    """
    return review_summary["review_score"].value_counts(normalize=True).sort_index()


def average_delivery_days(review_summary):
    """Mean delivery time in days.

    Parameters
    ----------
    review_summary : pd.DataFrame

    Returns
    -------
    float
    """
    return float(review_summary["delivery_days"].mean())


def average_review_score(review_summary):
    """Mean review score.

    Parameters
    ----------
    review_summary : pd.DataFrame

    Returns
    -------
    float
    """
    return float(review_summary["review_score"].mean())
