"""
Tool 4: Automation 2 - RFI drafter.
Takes the "rfis_needed" items found by the daily report summarizer and drafts
formal RFIs that follow the company's RFI process (docs/rfi_and_submittal_process.md).
A human (the project manager) reviews every draft before it is sent.
"""
import os
import json
from datetime import date
from llm_client import ask_llm_json

SUMMARIES_PATH = "outputs/daily_summaries.json"
RFI_DIR = "outputs/rfis"

PROMPT = """You are a construction project engineer drafting a Request for Information (RFI)
to the architect. Company rules for every RFI:
- Include the drawing or spec section referenced, if known
- Ask ONE clear question
- Offer a suggested solution if possible
- Mark it "Critical" only if the issue is holding up work right now (answered in 2 business days);
  otherwise "Standard" (5 business days)
- An RFI does not authorize extra cost

Use only the facts below. Do not invent drawing numbers, dimensions, or names.
If a reference is unknown, write "To be confirmed by PM".

Project: {project_id} ({project_type})
Date observed: {date}
Superintendent: {superintendent}
Issue from field log: {issue}

Return JSON with these keys:
"subject" (short title), "references" (drawing/spec sections or "To be confirmed by PM"),
"background" (2-3 sentences), "question" (one clear question),
"suggested_solution" (string, or "None proposed"),
"priority" ("Critical" or "Standard"), "schedule_impact" (one sentence)
"""


def draft_rfi(summary, issue):
    return ask_llm_json(PROMPT.format(issue=issue, **summary))


def to_markdown(rfi_number, summary, rfi):
    return f"""# {rfi_number}: {rfi['subject']}

**DRAFT - requires project manager review before sending**

| | |
|---|---|
| Project | {summary['project_id']} ({summary['project_type']}) |
| Date | {date.today().isoformat()} |
| From | Coastline Builders LLC |
| To | Architect of Record |
| Priority | **{rfi['priority']}** ({'2' if rfi['priority'] == 'Critical' else '5'} business day response) |
| References | {rfi['references']} |

## Background
{rfi['background']}

## Question
{rfi['question']}

## Suggested solution
{rfi['suggested_solution']}

## Schedule impact
{rfi['schedule_impact']}

*This RFI does not authorize additional cost or time. Any cost or schedule change requires a Change Order.*
"""


if __name__ == "__main__":
    os.makedirs(RFI_DIR, exist_ok=True)
    with open(SUMMARIES_PATH, encoding="utf-8") as f:
        summaries = json.load(f)

    count = 0
    for summary in summaries:
        for n, issue in enumerate(summary["rfis_needed"], start=1):
            rfi_number = f"RFI-{summary['project_id']}-{n:03d}"
            print(f"Drafting {rfi_number}: {issue}")
            rfi = draft_rfi(summary, issue)
            path = os.path.join(RFI_DIR, f"{rfi_number}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(to_markdown(rfi_number, summary, rfi))
            print(f"  [{rfi['priority']}] saved to {path}")
            count += 1

    print(f"\nDone. {count} RFI drafts ready for review in {RFI_DIR}/")