# E-Commerce Analytics Dashboard

A professional Streamlit dashboard for exploring e-commerce sales data. Built on
reusable `data_loader` and `business_metrics` Python modules extracted from the
original EDA notebook.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

## Project Structure

```
.
├── app.py                  # Streamlit dashboard
├── data_loader.py          # Data loading, cleaning, and filtering
├── business_metrics.py     # Reusable KPI / metric calculations
├── EDA_Refactored.ipynb    # Jupyter notebook version of the analysis
├── requirements.txt        # Python dependencies
├── ecommerce_data/         # CSV datasets
│   ├── orders_dataset.csv
│   ├── order_items_dataset.csv
│   ├── products_dataset.csv
│   ├── customers_dataset.csv
│   ├── order_reviews_dataset.csv
│   └── order_payments_dataset.csv
└── README.md
```

## Dashboard Layout

| Section | Description |
|---------|-------------|
| **Header** | Title and global date-range filter |
| **KPI Row** | Total Revenue, Avg MoM Growth, AOV, Total Orders (with trend indicators) |
| **Charts (2x2)** | Revenue trend (current vs previous), Top 10 categories, US choropleth, Satisfaction vs Delivery Time |
| **Bottom Row** | Average Delivery Time (with trend) and Average Review Score (with stars) |

### Filters

The date-range picker at the top controls the **current period**. A comparison
period of equal length directly preceding the start date is computed
automatically to power trend indicators and the dashed comparison line on the
revenue chart.

## Modules

### `data_loader.py`

- `load_datasets(data_dir)` -- load all six CSV files
- `parse_order_dates(orders)` -- convert date strings to datetime
- `build_sales_data(order_items, orders)` -- merge items with order metadata
- `filter_delivered(sales_data)` -- keep delivered orders, add year/month
- `filter_by_year(delivered, year)` / `filter_by_date_range(delivered, start, end)`
- `add_delivery_speed(delivered)` -- compute `delivery_days` column

### `business_metrics.py`

- Revenue: `total_revenue`, `revenue_growth`, `monthly_revenue`, `month_over_month_growth`, `average_mom_growth`
- Orders: `total_orders`, `order_count_growth`, `average_order_value`, `aov_growth`
- Categories: `revenue_by_category`
- Geography: `revenue_by_state`
- Customer experience: `review_delivery_summary`, `avg_review_by_delivery_bucket`, `avg_review_by_delivery_day`, `review_score_distribution`, `average_delivery_days`, `average_review_score`

## Requirements

- Python 3.9+
- See `requirements.txt` for package versions
