"""
Generates a realistic synthetic dataset of South Florida construction projects.
Real company data is private, so this simulates the patterns contractors see:
more change orders, hurricane-season starts, and complex project types cause delays.
"""
import numpy as np
import pandas as pd

N_PROJECTS = 500
SEED = 42
OUT_PATH = "data/construction_projects.csv"

PROJECT_TYPES = {
    # type: (typical budget, typical duration in days, complexity 0-1)
    "Multifamily": (18e6, 540, 0.7),
    "Hospitality": (25e6, 600, 0.8),
    "Commercial": (12e6, 420, 0.5),
    "Country Club": (9e6, 365, 0.5),
    "Marina": (7e6, 330, 0.9),
    "Luxury Residential": (5e6, 300, 0.6),
    "Renovation": (3e6, 200, 0.4),
}
COUNTIES = ["Miami-Dade", "Broward", "Palm Beach", "Martin", "St. Lucie"]
COUNTY_PERMIT_DELAY = {"Miami-Dade": 15, "Broward": 10, "Palm Beach": 8, "Martin": 4, "St. Lucie": 3}


def generate(n, seed):
    rng = np.random.default_rng(seed)
    types = rng.choice(list(PROJECT_TYPES), n)
    counties = rng.choice(COUNTIES, n, p=[0.3, 0.25, 0.25, 0.1, 0.1])
    start = pd.to_datetime("2019-01-01") + pd.to_timedelta(rng.integers(0, 2000, n), unit="D")
    hurricane = start.month.isin(range(6, 12))

    budget, planned, complexity = [], [], []
    for t in types:
        b, d, c = PROJECT_TYPES[t]
        budget.append(b * rng.uniform(0.6, 1.5))
        planned.append(int(d * rng.uniform(0.8, 1.2)))
        complexity.append(c)
    budget = np.round(np.array(budget), -3)
    planned = np.array(planned)
    complexity = np.array(complexity)

    change_orders = rng.poisson(3 + 8 * complexity)
    county_delay = np.array([COUNTY_PERMIT_DELAY[c] for c in counties])

    delay = (
        4 * change_orders
        + 20 * hurricane
        + 30 * complexity
        + county_delay
        + rng.normal(0, 12, n)
        - 25
    ).round().astype(int)

    overrun_pct = (0.8 * change_orders + 3 * hurricane + 0.05 * delay + rng.normal(0, 3, n) - 4) / 100
    actual_cost = np.round(budget * (1 + overrun_pct), -3)
    incidents = rng.poisson(0.5 + 1.5 * complexity + 0.003 * planned)

    df = pd.DataFrame({
        "project_id": [f"P{1000 + i}" for i in range(n)],
        "project_type": types,
        "county": counties,
        "start_date": start.date,
        "planned_days": planned,
        "actual_days": planned + delay,
        "budget_usd": budget,
        "actual_cost_usd": actual_cost,
        "change_orders": change_orders,
        "safety_incidents": incidents.astype(float),
        "hurricane_season_start": hurricane,
    })
    return add_real_world_mess(df, rng)


def add_real_world_mess(df, rng):
    """Real exports are messy: missing values, inconsistent names, duplicate rows."""
    df.loc[rng.choice(len(df), 12, replace=False), "actual_cost_usd"] = np.nan
    df.loc[rng.choice(len(df), 5, replace=False), "safety_incidents"] = np.nan
    messy = rng.choice(len(df), 15, replace=False)
    df.loc[messy, "county"] = df.loc[messy, "county"].apply(
        lambda c: rng.choice([c.lower(), c.upper(), f" {c} "]))
    dupes = df.sample(8, random_state=1)
    return pd.concat([df, dupes], ignore_index=True)


if __name__ == "__main__":
    data = generate(N_PROJECTS, SEED)
    data.to_csv(OUT_PATH, index=False)
    print(f"Generated {len(data)} rows -> {OUT_PATH}")