"""
Tool 4: Automation 3 - Delay risk alerts.
Connects three systems:
  1. Active project data (from the project database / CSV export)
  2. The delay prediction model from Tool 2
  3. Email (or saved alert files when email isn't set up)
Projects predicted to run late get a short, AI-written alert to their project manager.
"""
import os
import smtplib
from email.message import EmailMessage
import joblib
import pandas as pd
from dotenv import load_dotenv
from llm_client import ask_llm

load_dotenv(override=True)

ACTIVE_PATH = "data/active_projects.csv"
MODEL_PATH = "models/delay_model.joblib"
ALERT_DIR = "outputs/alerts"
DELAY_THRESHOLD_DAYS = 45  # alert if predicted delay is at least this many days
FEATURES = ["project_type", "county", "planned_days", "budget_usd",
            "change_orders", "hurricane_season_start"]

# Email is optional. Without these in .env, alerts are saved as files instead (safe "dry run").
SMTP_USER = os.getenv("ALERT_EMAIL_USER")
SMTP_PASSWORD = os.getenv("ALERT_EMAIL_APP_PASSWORD")
SEND_TO_OVERRIDE = os.getenv("ALERT_SEND_TO")  # send every alert to yourself while testing


def predict_delays(projects):
    model = joblib.load(MODEL_PATH)
    projects = projects.copy()
    projects["predicted_delay_days"] = model.predict(projects[FEATURES]).round().astype(int)
    return projects


def write_alert(p):
    prompt = f"""Write a short, professional email alert to a construction project manager.
Facts (use only these, do not invent anything):
- Project: {p.project_name} ({p.project_id}), {p.project_type} in {p.county} County
- Project manager: {p.project_manager}
- Planned duration: {p.planned_days} days, {p.days_elapsed} days elapsed
- Change orders so far: {p.change_orders}
- Started in hurricane season: {"yes" if p.hurricane_season_start else "no"}
- Predicted delay from our model: {p.predicted_delay_days} days (typical model error is about 9 days)

Explain the risk in 2-3 sentences, mention the main likely drivers from the facts above,
and suggest 2-3 practical next steps (for example: review open change orders, update the
schedule, check long-lead items). Keep it under 150 words. Sign off as "Project Controls Bot".
Return only the email body, no subject line."""
    return ask_llm(prompt)


def send_or_save(p, body):
    subject = f"Delay risk: {p.project_name} predicted ~{p.predicted_delay_days} days late"
    recipient = SEND_TO_OVERRIDE or p.pm_email

    if SMTP_USER and SMTP_PASSWORD:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = SMTP_USER, recipient, subject
        msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return f"emailed to {recipient}"

    os.makedirs(ALERT_DIR, exist_ok=True)
    path = os.path.join(ALERT_DIR, f"{p.project_id}_alert.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"**To:** {recipient}  \n**Subject:** {subject}\n\n{body}\n")
    return f"saved to {path}"


if __name__ == "__main__":
    projects = predict_delays(pd.read_csv(ACTIVE_PATH))
    projects = projects.sort_values("predicted_delay_days", ascending=False)

    print("=== Predicted delays for active projects ===")
    for p in projects.itertuples():
        flag = "⚠️ ALERT" if p.predicted_delay_days >= DELAY_THRESHOLD_DAYS else "ok"
        print(f"  {p.project_id}  {p.project_name:<32} {p.predicted_delay_days:>4} days   {flag}")

    at_risk = projects[projects["predicted_delay_days"] >= DELAY_THRESHOLD_DAYS]
    print(f"\n{len(at_risk)} project(s) at risk. Writing alerts...")
    for p in at_risk.itertuples():
        result = send_or_save(p, write_alert(p))
        print(f"  {p.project_id}: {result}")