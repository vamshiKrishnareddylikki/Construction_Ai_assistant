"""
Tool 2: Project insights (step 1 of 2)
Creates charts from the project database for project managers and leadership.
"""
import os
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # save charts to files without opening windows
import matplotlib.pyplot as plt

DB_PATH = "data/projects.db"
CHART_DIR = "charts"


def load_projects():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM projects", conn)


def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print("Saved", path)


def overrun_by_type(df):
    data = df.groupby("project_type")["overrun_pct"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    data.plot.barh(ax=ax, color="#2a6f97")
    ax.set_title("Average cost overrun by project type")
    ax.set_xlabel("Overrun (%)")
    ax.set_ylabel("")
    save(fig, "overrun_by_type.png")


def delay_by_county(df):
    data = df.groupby("county")["delay_days"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    data.plot.barh(ax=ax, color="#c8553d")
    ax.set_title("Average schedule delay by county")
    ax.set_xlabel("Delay (days)")
    ax.set_ylabel("")
    save(fig, "delay_by_county.png")


def budget_vs_actual(df):
    d = df.dropna(subset=["actual_cost_usd"])
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(d["budget_usd"] / 1e6, d["actual_cost_usd"] / 1e6, alpha=0.7)
    top = max(d["budget_usd"].max(), d["actual_cost_usd"].max()) / 1e6
    ax.plot([0, top], [0, top], "--", color="gray", label="On budget")
    ax.set_title("Budget vs. actual cost (points above the line = over budget)")
    ax.set_xlabel("Budget ($M)")
    ax.set_ylabel("Actual cost ($M)")
    ax.legend()
    save(fig, "budget_vs_actual.png")


def change_orders_vs_delay(df):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(df["change_orders"], df["delay_days"], alpha=0.7, color="#6a4c93")
    ax.set_title("Change orders vs. schedule delay")
    ax.set_xlabel("Number of change orders")
    ax.set_ylabel("Delay (days)")
    save(fig, "change_orders_vs_delay.png")


def print_stats(df):
    print("\n=== Key statistics ===")
    print(df[["delay_days", "overrun_pct", "change_orders"]].describe().round(1))
    print("\nCorrelation with delay_days:")
    print(df[["delay_days", "change_orders", "planned_days", "budget_usd"]]
          .corr()["delay_days"].round(2))


if __name__ == "__main__":
    os.makedirs(CHART_DIR, exist_ok=True)
    projects = load_projects()
    overrun_by_type(projects)
    delay_by_county(projects)
    budget_vs_actual(projects)
    change_orders_vs_delay(projects)
    print_stats(projects)