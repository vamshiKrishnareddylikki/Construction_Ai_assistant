"""
Tool 1: Data migration pipeline (step 1 of 2)
Loads raw project data, cleans it, and saves a clean version.
"""
import pandas as pd

RAW_PATH = "data/construction_projects.csv"
CLEAN_PATH = "data/clean_projects.csv"


def load_data(path):
    """Read the raw CSV into a DataFrame."""
    return pd.read_csv(path)


def report(df, title):
    """Print a quick health check of the data."""
    print(f"\n=== {title} ===")
    print("Rows, columns:", df.shape)
    print("Duplicate rows:", df.duplicated().sum())
    print("Missing values per column:")
    print(df.isna().sum()[df.isna().sum() > 0])
    print("Counties:", sorted(df["county"].unique()))
    invalid = (df["budget_usd"].isna() | (df["budget_usd"] <= 0)).sum()
    print("Invalid budgets ($0, negative, or missing):", invalid)


def remove_duplicates(df):
    return df.drop_duplicates().reset_index(drop=True)


def standardize_counties(df):
    """Fix inconsistent spelling like 'broward' or 'PALM BEACH'."""
    df["county"] = df["county"].str.strip().str.title()
    return df


def fill_missing(df):
    """Missing incidents -> 0. Missing cost -> flag it and leave blank for review."""
    df["safety_incidents"] = df["safety_incidents"].fillna(0).astype(int)
    df["cost_missing"] = df["actual_cost_usd"].isna()
    return df


def flag_invalid_budgets(df):
    """SITE-6: $0, negative, or missing budgets can't be used to calculate overrun %.
    Keep the project (it's still real), but flag it for review instead of guessing."""
    df["budget_invalid"] = df["budget_usd"].isna() | (df["budget_usd"] <= 0)
    return df


def add_metrics(df):
    """Add the numbers project managers actually care about."""
    df["delay_days"] = df["actual_days"] - df["planned_days"]
    valid = ~df["budget_invalid"]
    # Only calculate overruns where the budget is valid; leave them blank (NaN) otherwise
    df["overrun_usd"] = (df["actual_cost_usd"] - df["budget_usd"]).where(valid)
    df["overrun_pct"] = (df["overrun_usd"] / df["budget_usd"] * 100).round(1).where(valid)
    df["start_date"] = pd.to_datetime(df["start_date"])
    return df


def clean(df):
    df = remove_duplicates(df)
    df = standardize_counties(df)
    df = fill_missing(df)
    df = flag_invalid_budgets(df)
    df = add_metrics(df)
    return df


if __name__ == "__main__":
    raw = load_data(RAW_PATH)
    report(raw, "BEFORE cleaning")
    cleaned = clean(raw)
    report(cleaned, "AFTER cleaning")
    cleaned.to_csv(CLEAN_PATH, index=False)
    print(f"\nSaved clean data to {CLEAN_PATH}")