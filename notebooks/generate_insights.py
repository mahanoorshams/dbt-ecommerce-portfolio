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

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from google.cloud import bigquery

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

BACKGROUND = "#DDDDDC"   # warm natural grey applied to all charts
PURPLE     = "#6B21A8"   # gross margin bars
GREEN      = "#0D5349"   # channel chart bars
TEAL       = "#0D9488"   # cost of goods bars and retention line
LABEL      = "#FFFFFF"   # text on coloured bars

plt.rcParams.update({
    "figure.dpi": 130,
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "figure.facecolor": BACKGROUND,
    "axes.facecolor": BACKGROUND,
})


def load(client: bigquery.Client, dataset: str, table: str) -> pd.DataFrame:
    return client.query(f"select * from `{dataset}`.`{table}`").to_dataframe()


def chart_category_margin(df: pd.DataFrame) -> None:
    """
    Stacked horizontal bar chart showing cost of goods (teal) and gross margin
    (purple) for the top 10 categories by gross margin value. The full bar
    length equals gross revenue. Margin percentage sits inside the purple section.
    Categories are aggregated across Men and Women departments before ranking.
    """
    df_agg = (
        df.groupby("category", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            cost_of_goods=("cost_of_goods", "sum"),
        )
    )
    df_agg["gross_margin_pct"] = df_agg["gross_margin"] / df_agg["gross_revenue"]

    top = (
        df_agg.sort_values("gross_margin", ascending=False)
        .head(10)
        .iloc[::-1]
        .reset_index(drop=True)
    )

    bar_h = 0.55
    y = np.arange(len(top))

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    ax.barh(y, top["cost_of_goods"], height=bar_h, color=TEAL, label="Cost of goods")

    gm_bars = ax.barh(
        y, top["gross_margin"],
        left=top["cost_of_goods"],
        height=bar_h,
        color=PURPLE,
        label="Gross margin",
    )

    for bar, pct in zip(gm_bars, top["gross_margin_pct"]):
        x  = bar.get_x() + bar.get_width() * 0.5
        cy = bar.get_y() + bar.get_height() / 2
        ax.text(x, cy, f"{pct:.0%}", ha="center", va="center",
                fontsize=8, color=LABEL, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels(top["category"], fontsize=10)
    ax.set_xlabel("Value (£)")
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda v, _: f"{v/1_000_000:.1f}M" if v >= 1_000_000
            else f"{v/1000:.0f}K" if v >= 1000
            else "0"
        )
    )
    ax.legend(loc="lower right", framealpha=0.9, facecolor=BACKGROUND)
    fig.suptitle("Top 10 Categories by Gross Margin (£)", fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "category_margin.png", facecolor=BACKGROUND, bbox_inches="tight")
    plt.close(fig)


def chart_retention(df: pd.DataFrame) -> None:
    df = df.sort_values("cohort_month")
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.plot(df["cohort_month"], df["repeat_purchase_rate"],
            color=TEAL, marker="o", ms=4, linewidth=2)
    ax.fill_between(df["cohort_month"], df["repeat_purchase_rate"],
                    alpha=0.15, color=TEAL)
    ax.set_ylabel("Share of customers who ordered again")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    fig.autofmt_xdate()
    fig.suptitle("Repeat Purchase Rate by Acquisition Cohort", fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "retention_cohorts.png", facecolor=BACKGROUND, bbox_inches="tight")
    plt.close(fig)


def chart_channel(df: pd.DataFrame) -> None:
    df = df.sort_values("revenue_per_customer", ascending=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    bars = ax.barh(df["traffic_source"], df["revenue_per_customer"], color=GREEN)
    ax.set_xlabel("Value (£)")
    for bar, rep in zip(bars, df["repeat_purchase_rate"]):
        cx = bar.get_x() + bar.get_width() * 0.5
        cy = bar.get_y() + bar.get_height() / 2
        ax.text(cx, cy, f"{rep:.0%} repeat", ha="center", va="center",
                fontsize=8, color=LABEL, fontweight="bold")
    fig.suptitle("Revenue per Customer by Acquisition Channel (£)", fontsize=12, y=1.01)
    fig.tight_layout()
    fig.savefig(IMAGES_DIR / "channel_value.png", facecolor=BACKGROUND, bbox_inches="tight")
    plt.close(fig)


def headline_figures(
    cat: pd.DataFrame, ret: pd.DataFrame, chan: pd.DataFrame
) -> None:
    overall_repeat = ret["repeat_customers"].sum() / ret["new_customers"].sum()
    best_channel   = chan.sort_values("revenue_per_customer", ascending=False).iloc[0]

    # Aggregate across departments and filter to the same top 10 shown in the chart
    # so the headline figures reference categories that are actually visible.
    cat_agg = (
        cat.groupby("category", as_index=False)
        .agg(
            gross_revenue=("gross_revenue", "sum"),
            gross_margin=("gross_margin", "sum"),
            return_rate=("return_rate", "mean"),
        )
    )
    cat_agg["gross_margin_pct"] = cat_agg["gross_margin"] / cat_agg["gross_revenue"]
    top10 = cat_agg.sort_values("gross_margin", ascending=False).head(10)

    best_margin   = top10.sort_values("gross_margin_pct", ascending=False).iloc[0]
    worst_margin  = top10.sort_values("gross_margin_pct").iloc[0]
    worst_returns = top10.sort_values("return_rate", ascending=False).iloc[0]

    print("\n" + "=" * 60)
    print("HEADLINE FIGURES  (paste these into the README)")
    print("=" * 60)
    print(f"Overall repeat purchase rate : {overall_repeat:.1%}")
    print(f"Highest margin category (top 10) : {best_margin['category']} "
          f"({best_margin['gross_margin_pct']:.0%} margin)")
    print(f"Lowest margin category (top 10)  : {worst_margin['category']} "
          f"({worst_margin['gross_margin_pct']:.0%} margin)")
    print(f"Highest return rate (top 10)     : {worst_returns['category']} "
          f"({worst_returns['return_rate']:.0%} of items returned)")
    print(f"Best channel by rev/customer     : {best_channel['traffic_source']} "
          f"(£{best_channel['revenue_per_customer']:.0f}, "
          f"{best_channel['repeat_purchase_rate']:.0%} repeat)")
    print("=" * 60 + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True, help="GCP project id")
    p.add_argument("--dataset", default="dbt_analytics", help="dbt target dataset")
    args = p.parse_args()

    client = bigquery.Client(project=args.project)
    cat  = load(client, args.dataset, "mart_category_performance")
    ret  = load(client, args.dataset, "mart_customer_retention")
    chan = load(client, args.dataset, "mart_channel_performance")

    chart_category_margin(cat)
    chart_retention(ret)
    chart_channel(chan)
    headline_figures(cat, ret, chan)
    print(f"Charts saved to {IMAGES_DIR}")


if __name__ == "__main__":
    main()
