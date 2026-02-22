"""
Data loading, processing, and cleaning module for e-commerce EDA.

Provides functions to load CSV datasets, parse datetime columns,
merge order-level data, and filter by configurable date ranges.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_datasets(data_dir="ecommerce_data"):
    """Load all e-commerce CSV files and return them as a dictionary.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing the CSV files.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys: "orders", "order_items", "products", "customers", "reviews",
        "payments".
    """
    datasets = {
        "orders": pd.read_csv(f"{data_dir}/orders_dataset.csv"),
        "order_items": pd.read_csv(f"{data_dir}/order_items_dataset.csv"),
        "products": pd.read_csv(f"{data_dir}/products_dataset.csv"),
        "customers": pd.read_csv(f"{data_dir}/customers_dataset.csv"),
        "reviews": pd.read_csv(f"{data_dir}/order_reviews_dataset.csv"),
        "payments": pd.read_csv(f"{data_dir}/order_payments_dataset.csv"),
    }
    return datasets


# ---------------------------------------------------------------------------
# Cleaning / type conversion
# ---------------------------------------------------------------------------

_ORDER_DATE_COLS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def parse_order_dates(orders):
    """Convert date-string columns in the orders table to datetime.

    Parameters
    ----------
    orders : pd.DataFrame
        Raw orders dataframe.

    Returns
    -------
    pd.DataFrame
        Orders with datetime-typed date columns.
    """
    orders = orders.copy()
    for col in _ORDER_DATE_COLS:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")
    return orders


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def build_sales_data(order_items, orders):
    """Merge order items with order-level information.

    Only the columns needed for downstream analysis are kept:
    order_id, order_item_id, product_id, price, order_status,
    order_purchase_timestamp, order_delivered_customer_date.

    Parameters
    ----------
    order_items : pd.DataFrame
    orders : pd.DataFrame
        Should already have datetime-typed date columns.

    Returns
    -------
    pd.DataFrame
    """
    sales = pd.merge(
        order_items[["order_id", "order_item_id", "product_id", "price"]],
        orders[["order_id", "order_status", "order_purchase_timestamp",
                "order_delivered_customer_date"]],
        on="order_id",
    )
    return sales


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def filter_delivered(sales_data):
    """Return only rows with order_status == 'delivered'.

    Parameters
    ----------
    sales_data : pd.DataFrame

    Returns
    -------
    pd.DataFrame
        A copy filtered to delivered orders, with year and month columns added.
    """
    delivered = sales_data[sales_data["order_status"] == "delivered"].copy()
    delivered["year"] = delivered["order_purchase_timestamp"].dt.year
    delivered["month"] = delivered["order_purchase_timestamp"].dt.month
    return delivered


def filter_by_year(delivered, year):
    """Return delivered-sales rows for a specific year.

    Parameters
    ----------
    delivered : pd.DataFrame
        Output of ``filter_delivered``.
    year : int

    Returns
    -------
    pd.DataFrame
    """
    return delivered[delivered["year"] == year].copy()


def filter_by_date_range(delivered, start_date, end_date):
    """Return delivered-sales rows within an inclusive date range.

    Parameters
    ----------
    delivered : pd.DataFrame
        Output of ``filter_delivered``.
    start_date : str or datetime
        Inclusive lower bound (e.g. '2023-01-01').
    end_date : str or datetime
        Inclusive upper bound (e.g. '2023-12-31').

    Returns
    -------
    pd.DataFrame
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    mask = (
        (delivered["order_purchase_timestamp"] >= start)
        & (delivered["order_purchase_timestamp"] <= end)
    )
    return delivered[mask].copy()


def add_delivery_speed(delivered):
    """Add a ``delivery_days`` column (integer days from purchase to delivery).

    Parameters
    ----------
    delivered : pd.DataFrame
        Must contain order_purchase_timestamp and
        order_delivered_customer_date as datetime columns.

    Returns
    -------
    pd.DataFrame
        Same dataframe with an additional ``delivery_days`` column.
    """
    delivered = delivered.copy()
    delivered["order_delivered_customer_date"] = pd.to_datetime(
        delivered["order_delivered_customer_date"], errors="coerce"
    )
    delivered["delivery_days"] = (
        delivered["order_delivered_customer_date"]
        - delivered["order_purchase_timestamp"]
    ).dt.days
    return delivered
