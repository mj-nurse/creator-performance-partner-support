"""Cross-check key outputs between SQLite and pandas-generated files."""

from pathlib import Path
import sqlite3

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "raw" / "creator_support.db"
PROCESSED = ROOT / "data" / "processed"


with sqlite3.connect(DATABASE) as connection:
    sql_monthly = pd.read_sql_query(
        """
        SELECT
            performance_month,
            COUNT(DISTINCT CASE WHEN uploads > 0 THEN creator_id END) AS active_creators,
            SUM(uploads) AS total_uploads,
            SUM(views) AS total_views,
            ROUND(SUM(watch_hours), 1) AS total_watch_hours,
            SUM(new_subscribers) AS new_subscribers
        FROM monthly_performance
        GROUP BY performance_month
        ORDER BY performance_month
        """,
        connection,
    )

    table_counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ["creators", "monthly_performance", "support_cases"]
    }

pandas_monthly = pd.read_csv(PROCESSED / "monthly_summary.csv")
pd.testing.assert_frame_equal(sql_monthly, pandas_monthly, check_dtype=False)

assert table_counts["creators"] == 750
assert table_counts["monthly_performance"] == 9_000
assert table_counts["support_cases"] > 0

print("SQL and pandas monthly summaries match.")
print(f"Validated table counts: {table_counts}")
