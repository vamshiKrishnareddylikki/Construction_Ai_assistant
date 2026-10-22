"""
Tool 1: Data migration pipeline (step 2 of 2)
Moves clean project data into a SQL database, like migrating to a new platform.
"""
import sqlite3
import pandas as pd

CLEAN_PATH = "data/clean_projects.csv"
DB_PATH = "data/projects.db"


def migrate(csv_path, db_path):
    df = pd.read_csv(csv_path)
    with sqlite3.connect(db_path) as conn:
        df.to_sql("projects", conn, if_exists="replace", index=False)
    print(f"Migrated {len(df)} projects into {db_path}")


def verify(db_path):
    """Check the migration worked by querying the new database."""
    with sqlite3.connect(db_path) as conn:
        count = pd.read_sql("SELECT COUNT(*) AS projects FROM projects", conn)
        worst = pd.read_sql(
            """
            SELECT project_type,
                   ROUND(AVG(overrun_pct), 1) AS avg_overrun_pct,
                   ROUND(AVG(delay_days), 0)  AS avg_delay_days
            FROM projects
            GROUP BY project_type
            ORDER BY avg_overrun_pct DESC
            """,
            conn,
        )
    print(count)
    print(worst)


if __name__ == "__main__":
    migrate(CLEAN_PATH, DB_PATH)
    verify(DB_PATH)