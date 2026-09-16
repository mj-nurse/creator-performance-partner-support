"""Validate the synthetic data and create analysis summaries."""

from pathlib import Path
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    creators = pd.read_csv(RAW_DIR / "creators.csv", parse_dates=["join_date"])
    performance = pd.read_csv(RAW_DIR / "monthly_performance.csv")
    support_cases = pd.read_csv(RAW_DIR / "support_cases.csv", parse_dates=["opened_date"])
    return creators, performance, support_cases


def validate_data(
    creators: pd.DataFrame,
    performance: pd.DataFrame,
    support_cases: pd.DataFrame,
) -> None:
    assert creators["creator_id"].is_unique
    assert not performance.duplicated(["creator_id", "performance_month"]).any()
    assert support_cases["case_id"].is_unique
    assert performance["creator_id"].isin(creators["creator_id"]).all()
    assert support_cases["creator_id"].isin(creators["creator_id"]).all()
    assert (performance[["uploads", "views", "watch_hours", "new_subscribers"]] >= 0).all().all()
    assert support_cases["case_status"].isin(["Open", "Closed"]).all()


def create_monthly_summary(performance: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        performance.groupby("performance_month")
        .agg(
            active_creators=("uploads", lambda values: (values > 0).sum()),
            total_uploads=("uploads", "sum"),
            total_views=("views", "sum"),
            total_watch_hours=("watch_hours", "sum"),
            new_subscribers=("new_subscribers", "sum"),
        )
        .reset_index()
    )
    return monthly


def create_segment_summary(
    creators: pd.DataFrame, performance: pd.DataFrame
) -> pd.DataFrame:
    combined = performance.merge(creators, on="creator_id", validate="many_to_one")
    summary = (
        combined.groupby(["region", "partner_tier"])
        .agg(
            creators=("creator_id", "nunique"),
            active_creator_months=("uploads", lambda values: (values > 0).sum()),
            total_uploads=("uploads", "sum"),
            total_views=("views", "sum"),
            total_watch_hours=("watch_hours", "sum"),
            new_subscribers=("new_subscribers", "sum"),
        )
        .reset_index()
    )
    return summary


def create_support_summary(
    creators: pd.DataFrame, support_cases: pd.DataFrame
) -> pd.DataFrame:
    closed_cases = support_cases[support_cases["case_status"] == "Closed"].copy()
    combined = closed_cases.merge(creators, on="creator_id", validate="many_to_one")
    summary = (
        combined.groupby("case_type")
        .agg(
            cases=("case_id", "size"),
            avg_resolution_hours=("resolution_hours", "mean"),
            first_contact_resolution_rate=("first_contact_resolved", "mean"),
            avg_satisfaction=("satisfaction_score", "mean"),
        )
        .reset_index()
        .sort_values("cases", ascending=False)
    )
    return summary


def create_creator_summary(
    creators: pd.DataFrame,
    performance: pd.DataFrame,
    support_cases: pd.DataFrame,
) -> pd.DataFrame:
    first_half = performance[performance["performance_month"] <= "2025-06"]
    second_half = performance[performance["performance_month"] >= "2025-07"]

    first_half_views = first_half.groupby("creator_id")["views"].mean().rename("first_half_views")
    second_half_views = second_half.groupby("creator_id")["views"].mean().rename("second_half_views")
    active_months = (
        performance.assign(is_active=performance["uploads"] > 0)
        .groupby("creator_id")["is_active"]
        .sum()
        .rename("active_months")
    )
    support = (
        support_cases.groupby("creator_id")
        .agg(
            support_cases=("case_id", "size"),
            avg_resolution_hours=("resolution_hours", "mean"),
        )
    )

    summary = creators.set_index("creator_id").join(
        [first_half_views, second_half_views, active_months, support]
    )
    summary["support_cases"] = summary["support_cases"].fillna(0).astype(int)
    summary["view_growth_pct"] = (
        (summary["second_half_views"] - summary["first_half_views"])
        / summary["first_half_views"].replace(0, pd.NA)
        * 100
    )
    return summary.reset_index()


def create_charts(monthly: pd.DataFrame, support_summary: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.plot(monthly["performance_month"], monthly["active_creators"], marker="o")
    axis.set_title("Monthly active creators - synthetic 2025 data")
    axis.set_xlabel("Month")
    axis.set_ylabel("Active creators")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "monthly_active_creators.png", dpi=160)
    plt.close(figure)

    ordered = support_summary.sort_values("avg_resolution_hours", ascending=True)
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.barh(ordered["case_type"], ordered["avg_resolution_hours"], color="#3b6ea8")
    axis.set_title("Average support resolution time by case type - synthetic data")
    axis.set_xlabel("Average resolution hours")
    axis.set_ylabel("")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "support_resolution_by_type.png", dpi=160)
    plt.close(figure)


def validate_sql() -> int:
    database_path = RAW_DIR / "creator_support.db"
    sql_text = (ROOT / "sql" / "02_analysis_queries.sql").read_text()
    statement = ""
    statement_count = 0

    with sqlite3.connect(database_path) as connection:
        for line in sql_text.splitlines(keepends=True):
            statement += line
            if sqlite3.complete_statement(statement):
                connection.execute(statement).fetchall()
                statement_count += 1
                statement = ""

    return statement_count


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    creators, performance, support_cases = load_data()
    validate_data(creators, performance, support_cases)

    monthly = create_monthly_summary(performance)
    segments = create_segment_summary(creators, performance)
    support_summary = create_support_summary(creators, support_cases)
    creator_summary = create_creator_summary(creators, performance, support_cases)

    monthly.to_csv(OUTPUT_DIR / "monthly_summary.csv", index=False)
    segments.to_csv(OUTPUT_DIR / "segment_summary.csv", index=False)
    support_summary.to_csv(OUTPUT_DIR / "support_summary.csv", index=False)
    creator_summary.to_csv(OUTPUT_DIR / "creator_summary.csv", index=False)
    create_charts(monthly, support_summary)

    statement_count = validate_sql()
    print(f"Validated {statement_count} SQL analyses.")
    print(f"Average monthly active creators: {monthly['active_creators'].mean():.1f}")
    print(f"Total support cases: {len(support_cases):,}")


if __name__ == "__main__":
    main()
