"""
Tool 6: AI agent (step 1 of 3) - the agent's toolbox.
Each function wraps something built in Tools 1-4, so the agent can decide when to use it.
TOOL_SCHEMAS describe each tool to the LLM: its name, what it does, and its inputs.
"""
import json
import re
import sqlite3
import joblib
import pandas as pd
import os
import glob
from ask_docs import load_index, retrieve

DB_PATH = "data/projects.db"
ACTIVE_PATH = "data/active_projects.csv"
MODEL_PATH = "models/delay_model.joblib"
DIGEST_PATH = "outputs/daily_digest.md"
MAX_ROWS = 20
FEATURES = ["project_type", "county", "planned_days", "budget_usd",
            "change_orders", "hurricane_season_start"]

_index = None


def search_company_docs(question):
    """Find the company document sections most relevant to a question (RAG retrieval)."""
    global _index
    if _index is None:
        _index = load_index()
    matches = retrieve(question, _index, k=3)
    return [{"source": f"{c['source']} > {c['section']}", "match": round(score, 2), "text": c["text"]}
            for score, c in matches]


def query_project_history(sql):
    """Run a READ-ONLY SQL query on the historical projects database (500 completed projects)."""
    cleaned = sql.strip().rstrip(";")
    # Guardrail: only allow a single SELECT statement. No changes to the data, ever.
    if not re.match(r"(?is)^\s*(select|with)\b", cleaned) or ";" in cleaned:
        return {"error": "Only a single read-only SELECT query is allowed."}
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|create|replace|attach|pragma)\b", cleaned):
        return {"error": "Query contains a forbidden keyword. Only read-only SELECT queries are allowed."}
    try:
        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:  # opened read-only
            df = pd.read_sql(f"SELECT * FROM ({cleaned}) LIMIT {MAX_ROWS}", conn)
        return {"rows": df.to_dict(orient="records"), "row_count": len(df)}
    except Exception as e:
        return {"error": f"SQL error: {e}"}


def list_active_projects():
    """List all projects currently under construction."""
    df = pd.read_csv(ACTIVE_PATH)
    return df[["project_id", "project_name", "project_type", "county", "project_manager",
               "planned_days", "days_elapsed", "change_orders"]].to_dict(orient="records")


def predict_delay(project_id):
    """Predict schedule delay (days) for an active project using the Tool 2 model."""
    df = pd.read_csv(ACTIVE_PATH)
    row = df[df["project_id"].str.upper() == str(project_id).upper()]
    if row.empty:
        return {"error": f"No active project with id {project_id}. Use list_active_projects first."}
    model = joblib.load(MODEL_PATH)
    days = int(round(model.predict(row[FEATURES])[0]))
    p = row.iloc[0]
    return {"project_id": p["project_id"], "project_name": p["project_name"],
            "predicted_delay_days": days, "model_typical_error_days": 9,
            "change_orders": int(p["change_orders"]),
            "hurricane_season_start": bool(p["hurricane_season_start"])}


def rank_active_projects_by_risk():
    """Predict delays for ALL active projects at once and rank them, highest risk first."""
    df = pd.read_csv(ACTIVE_PATH)
    model = joblib.load(MODEL_PATH)
    df["predicted_delay_days"] = model.predict(df[FEATURES]).round().astype(int)
    df = df.sort_values("predicted_delay_days", ascending=False)
    return {"model_typical_error_days": 9,
            "projects": df[["project_id", "project_name", "project_type", "county",
                            "project_manager", "change_orders", "predicted_delay_days"]]
                        .to_dict(orient="records")}


def get_daily_digest():
    """Return today's summarized superintendent field reports (from the daily automation)."""
    try:
        with open(DIGEST_PATH, encoding="utf-8") as f:
            return {"digest": f.read()}
    except FileNotFoundError:
        return {"error": "No digest yet. Run python src/summarize_reports.py first."}


DRAWINGS_DIR = "data/drawings"


def list_drawing_sets():
    """List the drawing set PDFs available for review."""
    files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(DRAWINGS_DIR, "*.pdf")))
    return {"drawing_sets": files} if files else {"error": "No drawing PDFs found in data/drawings."}


def review_drawing_set(file_name):
    """Pre-construction review of one drawing set: missing sheets, NOA issues, long-lead items, RFIs."""
    from review_drawings import review  # imported here so the agent still works without Gemini vision
    safe_name = os.path.basename(file_name)  # guardrail: only files inside data/drawings
    path = os.path.join(DRAWINGS_DIR, safe_name)
    if not safe_name.lower().endswith(".pdf") or not os.path.exists(path):
        return {"error": f"No drawing set named {file_name}. Use list_drawing_sets first."}
    data, findings, _, report_path = review(path, use_cache=True)
    return {"project": data.get("project", {}), "sheets_in_set": data.get("sheets_in_set", []),
            "findings": findings, "full_report": report_path,
            "note": "AI-assisted first pass. Requires PM/estimator review. No takeoffs or measurements."}


# What the LLM sees: name + description + input format for each tool.
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "search_company_docs",
        "description": "Search company documents (contract general conditions, safety manual, closeout "
                       "procedures, RFI and submittal process). Use for ANY question about company policy, "
                       "rules, deadlines, or procedures.",
        "parameters": {"type": "object", "properties": {
            "question": {"type": "string", "description": "What to look up"}},
            "required": ["question"]}}},
    {"type": "function", "function": {
        "name": "query_project_history",
        "description": "Run a read-only SQLite SELECT query on table `projects` (500 completed projects). "
                       "Columns: project_id, project_type, county, start_date, planned_days, actual_days, "
                       "budget_usd, actual_cost_usd, change_orders, safety_incidents, "
                       "hurricane_season_start (1/0), cost_missing (1/0), delay_days, overrun_usd, overrun_pct. "
                       "Exact text values (case-sensitive!): project_type in ('Multifamily', 'Hospitality', "
                       "'Commercial', 'Country Club', 'Marina', 'Luxury Residential', 'Renovation'); "
                       "county in ('Miami-Dade', 'Broward', 'Palm Beach', 'Martin', 'St. Lucie'). "
                       "Use for statistics and trends from past projects.",
        "parameters": {"type": "object", "properties": {
            "sql": {"type": "string", "description": "A single SQLite SELECT statement"}},
            "required": ["sql"]}}},
    {"type": "function", "function": {
        "name": "list_active_projects",
        "description": "List all projects currently under construction, with IDs, names, and project managers.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "predict_delay",
        "description": "Predict the schedule delay in days for ONE active project, by its project_id (like A2001).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "rank_active_projects_by_risk",
        "description": "Predict delays for ALL active projects at once, ranked highest risk first. "
                       "Use this for any question comparing projects or asking which is most at risk.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "list_drawing_sets",
        "description": "List architectural drawing set PDFs available for pre-construction review.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "review_drawing_set",
        "description": "Pre-construction review of a drawing set PDF: missing sheets and disciplines, "
                       "windows/doors missing impact rating or Miami-Dade NOA, long-lead procurement items, "
                       "and RFI candidates. Does NOT do quantity takeoffs or measurements.",
        "parameters": {"type": "object", "properties": {
            "file_name": {"type": "string", "description": "PDF file name from list_drawing_sets"}},
            "required": ["file_name"]}}},
    {"type": "function", "function": {
        "name": "get_daily_digest",
        "description": "Get today's summary of superintendent daily field reports: safety issues, "
                       "delays, RFIs needed, change orders, and procurement risks.",
        "parameters": {"type": "object", "properties": {}}}},
]

TOOLS = {
    "search_company_docs": search_company_docs,
    "query_project_history": query_project_history,
    "list_active_projects": list_active_projects,
    "predict_delay": predict_delay,
    "rank_active_projects_by_risk": rank_active_projects_by_risk,
    "get_daily_digest": get_daily_digest,
    "list_drawing_sets": list_drawing_sets,
    "review_drawing_set": review_drawing_set,
}


def run_tool(name, arguments_json):
    """Run a tool by name with JSON arguments from the LLM. Errors are returned, not raised,
    so the agent can read them and try something else."""
    if name not in TOOLS:
        return json.dumps({"error": f"Unknown tool {name}"})
    try:
        args = json.loads(arguments_json or "{}")
        result = TOOLS[name](**args)
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {e}"}
    return json.dumps(result, default=str)


if __name__ == "__main__":
    # Quick test of every tool, without the LLM
    print("list_active_projects ->", len(list_active_projects()), "projects")
    print("predict_delay(A2001) ->", predict_delay("A2001"))
    print("query (avg delay by county) ->", query_project_history(
        "SELECT county, ROUND(AVG(delay_days),1) AS avg_delay FROM projects GROUP BY county"))
    print("guardrail test (DELETE) ->", query_project_history("DELETE FROM projects"))
    print("search_company_docs ->", [m["source"] for m in search_company_docs("weather delay notice")])
    print("get_daily_digest ->", str(get_daily_digest())[:80], "...")
