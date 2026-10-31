"""Unit tests for the data cleaning pipeline (src/clean_data.py)."""
import numpy as np
import pandas as pd
from clean_data import clean


def make_projects(budgets):
    """Build a tiny fake dataset: one project per budget value."""
    n = len(budgets)
    return pd.DataFrame({
        "project_id": [f"T{i}" for i in range(n)],
        "project_type": ["Marina"] * n,
        "county": ["Broward"] * n,
        "start_date": ["2024-01-01"] * n,
        "planned_days": [100] * n,
        "actual_days": [110] * n,
        "budget_usd": budgets,
        "actual_cost_usd": [1_100_000.0] * n,
        "change_orders": [3] * n,
        "safety_incidents": [0.0] * n,
        "hurricane_season_start": [False] * n,
    })


def test_invalid_budgets_never_produce_infinite_overrun():
    """SITE-6 AC1: $0 and negative budgets must not create inf / -inf."""
    cleaned = clean(make_projects([0.0, -500_000.0, 1_000_000.0]))
    assert not np.isinf(cleaned["overrun_pct"]).any()


def test_invalid_budgets_are_flagged_and_kept():
    """SITE-6 AC2: invalid-budget projects stay in the data, flagged for review."""
    cleaned = clean(make_projects([0.0, -500_000.0, 1_000_000.0]))
    assert len(cleaned) == 3                                  # nothing deleted
    assert cleaned["budget_invalid"].tolist() == [True, True, False]
    assert cleaned["overrun_pct"].iloc[:2].isna().all()       # blank, not a fake number


def test_valid_budget_overrun_is_still_correct():
    """Regression check: the fix must not break normal projects ($1.0M budget, $1.1M cost = 10%)."""
    cleaned = clean(make_projects([1_000_000.0]))
    assert cleaned["overrun_pct"].iloc[0] == 10.0
