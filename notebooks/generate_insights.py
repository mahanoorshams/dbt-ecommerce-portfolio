"""
Generate the portfolio charts and headline figures from the dbt marts.

Run this AFTER `dbt run` has built the analytics marts. It reads the three
mart tables straight from BigQuery, saves three charts into ../images/, and
prints a HEADLINE FIGURES block that the README quotes.

Usage:
    pip install -r requirements.txt
    python generate_insights.py --project YOUR_GCP_PROJECT --dataset dbt_analytics
"""

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from google.cloud import bigquery

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

# A clean, consistent look across the three charts.
plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.bbox": "tight",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})
ACCENT = "#2563eb"
MUTED = "#94a3b8"


def load(client: bigquery.Client, dataset: str, table: str) -> pd.DataFrame:
    return client.query(f"select * from `{dataset}`.`{table}`").to_dataframe()


def chart_category_margin(df: pd.DataFrame) -> None:
    top = df.sort_values("gross_margin", ascending=False).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top["category"], top["gross_margin"], color=ACCENT)
    ax.set_title("Top 10 categories by gross margin (£)")
    ax.set_xlabel("Gross margin (£)")
    for y, (m, pct) in enumerate(zip(top["gross_margin"], top["gross_margin_pct"])):
        ax.text(m, y, f"  {pct:.0%}", va="center", fontsize=9, color=MUTED)
    fig.savefig(IMAGES_DIR / "category_margin.png")
    plt.close(fig)


def chart_retention(df: pd.DataFrame) -> None:
    df = df.sort_values("cohort_month")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["cohort_month"], df["repeat_purchase_rate"], color=ACCENT, marker="o", ms=3)
    ax.set_title("Repeat-purchase rate by acquisition cohort")
    ax.set_ylabel("Share of customers who ordered again")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    fig.autofmt_xdate()
    fig.savefig(IMAGES_DIR / "retention_cohorts.png")
    plt.close(fig)


def chart_channel(df: pd.DataFrame) -> None:
    df = df.sort_values("revenue_per_customer", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df["traffic_source"], df["revenue_per_customer"], color=ACCENT)
    ax.set_title("Revenue per customer by acquisition channel (£)")
    ax.set_xlabel("Revenue per customer (£)")
    for y, (rev, rep) in enumerate(zip(df["revenue_per_customer"], df["repeat_purchase_rate"])):
        ax.text(rev, y, f"  {rep:.0%} repeat", va="center", fontsize=9, color=MUTED)
    fig.savefig(IMAGES_DIR / "channel_value.png")
    plt.close(fig)


def headline_figures(cat: pd.DataFrame, ret: pd.DataFrame, chan: pd.DataFrame) -> None:
    overall_repeat = (ret["repeat_customers"].sum() / ret["new_customers"].sum())
    best_margin = cat.sort_values("gross_margin_pct", ascending=False).iloc[0]
    worst_margin = cat.sort_values("gross_margin_pct").iloc[0]
    worst_returns = cat.sort_values("return_rate", ascending=False).iloc[0]
    best_channel = chan.sort_values("revenue_per_customer", ascending=False).iloc[0]

    print("\n" + "=" * 60)
    print("HEADLINE FIGURES  (paste these into the README)")
    print("=" * 60)
    print(f"Overall repeat-purchase rate : {overall_repeat:.1%}")
    print(f"Highest-margin category      : {best_margin['category']} "
          f"({best_margin['gross_margin_pct']:.0%})")
    print(f"Lowest-margin category       : {worst_margin['category']} "
          f"({worst_margin['gross_margin_pct']:.0%})")
    print(f"Highest return rate          : {worst_returns['category']} "
          f"({worst_returns['return_rate']:.0%})")
    print(f"Best channel by rev/customer : {best_channel['traffic_source']} "
          f"(£{best_channel['revenue_per_customer']:.0f}, "
          f"{best_channel['repeat_purchase_rate']:.0%} repeat)")
    print("=" * 60 + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="GCP project id")
    p.add_argument("--dataset", default="dbt_analytics", help="dbt target dataset")
    args = p.parse_args()

    client = bigquery.Client(project=args.project)
    cat = load(client, args.dataset, "mart_category_performance")
    ret = load(client, args.dataset, "mart_customer_retention")
    chan = load(client, args.dataset, "mart_channel_performance")

    chart_category_margin(cat)
    chart_retention(ret)
    chart_channel(chan)
    headline_figures(cat, ret, chan)
    print(f"Charts written to {IMAGES_DIR}")


if __name__ == "__main__":
    main()
