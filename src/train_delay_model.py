"""
Tool 2: Project insights (step 2 of 2)
Trains a model that predicts schedule delay (in days) for a construction project.
"""
import os
import sqlite3
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor
from sklearn.metrics import mean_absolute_error, r2_score

DB_PATH = "data/projects.db"
MODEL_PATH = "models/delay_model.joblib"

# Features = what we know BEFORE the project finishes
CATEGORICAL = ["project_type", "county"]
NUMERIC = ["planned_days", "budget_usd", "change_orders", "hurricane_season_start"]
TARGET = "delay_days"


def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM projects", conn)
    df["hurricane_season_start"] = df["hurricane_season_start"].astype(int)
    return df[CATEGORICAL + NUMERIC], df[TARGET]


def build_pipeline(model):
    prep = ColumnTransformer([
        ("categories", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL),
        ("numbers", StandardScaler(), NUMERIC),  # put numbers on the same scale
    ])
    return Pipeline([("prep", prep), ("model", model)])


def evaluate(name, pipe, X_test, y_test):
    preds = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"{name:<20} MAE: {mae:5.1f} days   R2: {r2:5.2f}")
    return mae


if __name__ == "__main__":
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    candidates = {
        "Baseline (average)": DummyRegressor(strategy="mean"),
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, random_state=42),
    }

    print("=== Model comparison (lower MAE is better) ===")
    results = {}
    for name, model in candidates.items():
        pipe = build_pipeline(model).fit(X_train, y_train)
        results[name] = (evaluate(name, pipe, X_test, y_test), pipe)

    best_name = min(results, key=lambda k: results[k][0])
    best_pipe = results[best_name][1]
    print(f"\nBest model: {best_name}")

    os.makedirs("models", exist_ok=True)
    joblib.dump(best_pipe, MODEL_PATH)
    print(f"Saved to {MODEL_PATH}")

    example = pd.DataFrame([{
        "project_type": "Marina", "county": "Miami-Dade", "planned_days": 330,
        "budget_usd": 7_000_000, "change_orders": 12, "hurricane_season_start": 1,
    }])
    print(f"\nExample: Marina in Miami-Dade, 12 change orders, hurricane-season start")
    print(f"Predicted delay: {best_pipe.predict(example)[0]:.0f} days")