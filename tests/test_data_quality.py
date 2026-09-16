from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / f"{name}.csv")


def test_primary_keys_are_unique():
    creators = read_csv("creators")
    support_cases = read_csv("support_cases")
    performance = read_csv("monthly_performance")

    assert creators["creator_id"].is_unique
    assert support_cases["case_id"].is_unique
    assert not performance.duplicated(["creator_id", "performance_month"]).any()


def test_foreign_keys_match_creators():
    creators = read_csv("creators")
    performance = read_csv("monthly_performance")
    support_cases = read_csv("support_cases")
    creator_ids = set(creators["creator_id"])

    assert set(performance["creator_id"]) <= creator_ids
    assert set(support_cases["creator_id"]) <= creator_ids


def test_performance_values_are_valid():
    performance = read_csv("monthly_performance")
    metric_columns = ["uploads", "views", "watch_hours", "new_subscribers"]

    assert (performance[metric_columns] >= 0).all().all()
    assert performance["performance_month"].nunique() == 12


def test_support_case_rules():
    support_cases = read_csv("support_cases")
    closed = support_cases["case_status"] == "Closed"
    open_cases = support_cases["case_status"] == "Open"

    assert support_cases["case_status"].isin(["Open", "Closed"]).all()
    assert support_cases.loc[closed, "resolution_hours"].notna().all()
    assert support_cases.loc[open_cases, "resolution_hours"].isna().all()
    assert support_cases.loc[closed, "satisfaction_score"].between(1, 5).all()
