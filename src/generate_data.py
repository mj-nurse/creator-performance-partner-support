"""Generate reproducible synthetic creator and partner-support data."""

from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RANDOM_SEED = 20260916
MONTHS = pd.period_range("2025-01", "2025-12", freq="M").astype(str)


def build_creators(rng: np.random.Generator, count: int = 750) -> pd.DataFrame:
    creator_ids = [f"CR{i:04d}" for i in range(1, count + 1)]
    join_dates = pd.to_datetime("2022-01-01") + pd.to_timedelta(
        rng.integers(0, 1095, count), unit="D"
    )

    return pd.DataFrame(
        {
            "creator_id": creator_ids,
            "join_date": join_dates.strftime("%Y-%m-%d"),
            "region": rng.choice(
                ["US & Canada", "Brazil", "Mexico", "Other LATAM"],
                count,
                p=[0.55, 0.18, 0.15, 0.12],
            ),
            "category": rng.choice(
                ["Entertainment", "Gaming", "Education", "Music", "Lifestyle"],
                count,
                p=[0.24, 0.22, 0.18, 0.17, 0.19],
            ),
            "partner_tier": rng.choice(
                ["Emerging", "Growth", "Established"],
                count,
                p=[0.58, 0.29, 0.13],
            ),
        }
    )


def build_monthly_performance(
    rng: np.random.Generator, creators: pd.DataFrame
) -> pd.DataFrame:
    tier_upload_rate = {"Emerging": 2.8, "Growth": 5.0, "Established": 7.5}
    tier_base_views = {"Emerging": 18_000, "Growth": 75_000, "Established": 260_000}
    tier_monthly_growth = {"Emerging": 0.015, "Growth": 0.022, "Established": 0.012}
    tier_inactive_probability = {"Emerging": 0.18, "Growth": 0.08, "Established": 0.04}

    records = []
    for creator in creators.itertuples(index=False):
        creator_scale = rng.lognormal(mean=0, sigma=0.45)

        for month_number, month in enumerate(MONTHS):
            inactive = rng.random() < tier_inactive_probability[creator.partner_tier]
            uploads = 0 if inactive else rng.poisson(tier_upload_rate[creator.partner_tier]) + 1

            if uploads == 0:
                views = 0
                watch_hours = 0.0
                new_subscribers = 0
            else:
                expected_views = (
                    tier_base_views[creator.partner_tier]
                    * creator_scale
                    * (1 + tier_monthly_growth[creator.partner_tier]) ** month_number
                )
                views = int(max(100, expected_views * rng.lognormal(0, 0.25)))
                average_view_minutes = rng.uniform(3.5, 9.0)
                watch_hours = round(views * average_view_minutes / 60, 1)
                subscriber_rate = rng.uniform(0.004, 0.015)
                new_subscribers = int(views * subscriber_rate)

            records.append(
                {
                    "creator_id": creator.creator_id,
                    "performance_month": month,
                    "uploads": uploads,
                    "views": views,
                    "watch_hours": watch_hours,
                    "new_subscribers": new_subscribers,
                }
            )

    return pd.DataFrame(records)


def build_support_cases(
    rng: np.random.Generator, creators: pd.DataFrame
) -> pd.DataFrame:
    tier_case_rate = {"Emerging": 3.2, "Growth": 2.4, "Established": 1.8}
    case_types = [
        "Monetization",
        "Account Access",
        "Policy Question",
        "Technical Issue",
        "Analytics Question",
    ]
    case_probabilities = [0.25, 0.14, 0.21, 0.24, 0.16]
    resolution_multiplier = {
        "Monetization": 1.5,
        "Account Access": 1.1,
        "Policy Question": 1.4,
        "Technical Issue": 1.3,
        "Analytics Question": 0.9,
    }

    records = []
    case_number = 1

    for creator in creators.itertuples(index=False):
        case_count = rng.poisson(tier_case_rate[creator.partner_tier])

        for _ in range(case_count):
            case_type = rng.choice(case_types, p=case_probabilities)
            case_status = rng.choice(["Closed", "Open"], p=[0.94, 0.06])
            opened_date = pd.Timestamp("2025-01-01") + pd.to_timedelta(
                rng.integers(0, 365), unit="D"
            )

            if case_status == "Closed":
                resolution_hours = round(
                    min(168, rng.lognormal(2.1, 0.7) * resolution_multiplier[case_type]),
                    1,
                )
                first_contact_probability = 0.74 if creator.partner_tier != "Emerging" else 0.65
                first_contact_resolved = int(rng.random() < first_contact_probability)
                satisfaction_score = int(
                    np.clip(round(5.1 - resolution_hours / 18 + rng.normal(0, 0.7)), 1, 5)
                )
            else:
                resolution_hours = None
                first_contact_resolved = 0
                satisfaction_score = None

            records.append(
                {
                    "case_id": f"SC{case_number:05d}",
                    "creator_id": creator.creator_id,
                    "opened_date": opened_date.strftime("%Y-%m-%d"),
                    "case_type": case_type,
                    "case_channel": rng.choice(["Email", "Chat", "Phone"], p=[0.40, 0.38, 0.22]),
                    "resolution_hours": resolution_hours,
                    "first_contact_resolved": first_contact_resolved,
                    "satisfaction_score": satisfaction_score,
                    "case_status": case_status,
                }
            )
            case_number += 1

    return pd.DataFrame(records)


def write_outputs(
    creators: pd.DataFrame,
    performance: pd.DataFrame,
    support_cases: pd.DataFrame,
) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tables = {
        "creators": creators,
        "monthly_performance": performance,
        "support_cases": support_cases,
    }

    for table_name, data in tables.items():
        data.to_csv(RAW_DIR / f"{table_name}.csv", index=False)

    database_path = RAW_DIR / "creator_support.db"
    with sqlite3.connect(database_path) as connection:
        connection.executescript((ROOT / "sql" / "01_schema.sql").read_text())
        for table_name, data in tables.items():
            data.to_sql(table_name, connection, if_exists="append", index=False)


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    creators = build_creators(rng)
    performance = build_monthly_performance(rng, creators)
    support_cases = build_support_cases(rng, creators)
    write_outputs(creators, performance, support_cases)

    print(f"Created {len(creators):,} synthetic creators.")
    print(f"Created {len(performance):,} monthly performance records.")
    print(f"Created {len(support_cases):,} synthetic support cases.")


if __name__ == "__main__":
    main()
