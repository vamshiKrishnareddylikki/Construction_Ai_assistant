"""
Tool 4: Automation 1 - Daily site report summarizer.
Superintendents write quick, messy field notes. This turns each one into a clean,
structured summary and flags what the project manager needs to act on.
"""
import os
import json
import glob
from llm_client import ask_llm_json

REPORTS_DIR = "data/site_reports"
OUTPUT_DIR = "outputs"

PROMPT = """You are an assistant for a construction project manager.
Read this superintendent's daily field log and extract the key facts.
Only use information that is in the log. Use an empty list if there is nothing for a field.

Return JSON with exactly these keys:
- "project_id": string
- "project_type": string
- "date": string
- "superintendent": string
- "crew_size": number or null
- "work_completed": list of short strings
- "delays": list of short strings (what was lost and why)
- "safety": list of short strings (incidents, near misses, violations, actions taken)
- "rfis_needed": list of short strings (unclear drawings/specs or hidden conditions needing an answer)
- "change_orders_needed": list of short strings (owner changes or extra work needing pricing)
- "procurement_risks": list of short strings (late materials, unapproved submittals, long-lead items)
- "priority": "HIGH", "MEDIUM", or "LOW" (HIGH if any safety event, schedule-critical item, or hidden condition)
- "one_line_summary": string

FIELD LOG:
{log}
"""


def summarize(log_text):
    return ask_llm_json(PROMPT.format(log=log_text))


def to_markdown(s):
    def section(title, items):
        if not items:
            return ""
        return f"**{title}**\n" + "\n".join(f"- {i}" for i in items) + "\n\n"

    return (
        f"### {s['project_id']} ({s['project_type']}): {s['date']}  [{s['priority']}]\n"
        f"*{s['one_line_summary']}*  \n"
        f"Superintendent: {s['superintendent']} | Crew: {s['crew_size']}\n\n"
        + section("Work completed", s["work_completed"])
        + section("Delays", s["delays"])
        + section("⚠️ Safety", s["safety"])
        + section("RFIs needed", s["rfis_needed"])
        + section("Change orders needed", s["change_orders_needed"])
        + section("Procurement risks", s["procurement_risks"])
    )


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summaries = []
    for path in sorted(glob.glob(os.path.join(REPORTS_DIR, "*.txt"))):
        print(f"Summarizing {os.path.basename(path)}...")
        with open(path, encoding="utf-8") as f:
            summaries.append(summarize(f.read()))

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    summaries.sort(key=lambda s: order.get(s["priority"], 3))

    with open(os.path.join(OUTPUT_DIR, "daily_summaries.json"), "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    digest = "# Daily Site Report Digest\n\n" + "\n---\n\n".join(to_markdown(s) for s in summaries)
    with open(os.path.join(OUTPUT_DIR, "daily_digest.md"), "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"\nDone. {len(summaries)} reports summarized.")
    print(f"Open {OUTPUT_DIR}/daily_digest.md to read the digest.")
    for s in summaries:
        print(f"  [{s['priority']}] {s['project_id']}: {s['one_line_summary']}")