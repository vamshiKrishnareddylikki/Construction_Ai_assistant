"""
Tool 7: Pre-construction drawing reviewer.
  Step 1 (AI):     Gemini reads the drawing PDF and EXTRACTS facts into structured JSON
                   (sheets, schedules, notes). The AI only reads; it doesn't judge.
  Step 2 (Python): company rules are applied by normal code, so the checks are
                   consistent, explainable, and testable.
  Step 3:          writes a pre-construction report marked DRAFT for human review.
Deliberately NOT attempted: quantity takeoffs, measurements, clash detection.
"""
import os
import re
import sys
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from llm_client import with_retry

load_dotenv(override=True)
VISION_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
OUT_DIR = "outputs/drawing_reviews"
EXPECTED_DISCIPLINES = {"G": "General", "A": "Architectural", "S": "Structural",
                        "M": "Mechanical", "E": "Electrical", "P": "Plumbing"}
LONG_LEAD = {  # keyword -> why it matters (company rule: submit long-lead items within 30 days)
    "sliding glass door": "Impact sliding doors often have 10-14 week lead times",
    "garage": "Impact-rated overhead garage doors are often long-lead",
    "impact": "Impact windows/doors: ~12 week lead time in South Florida",
    "metal roof": "Standing seam metal roofing needs shop drawings + lead time",
    "elevator": "Elevators: 16+ week lead time",
    "switchgear": "Electrical switchgear: 20+ week lead time",
    "piling": "Marine pilings: long lead and permitting",
}
VAGUE_PHRASES = ["tbd", "by others", "see spec", "verify", "not provided", "under separate cover"]
# Standard boilerplate found on almost every drawing set. Not real questions, so not RFIs.
BOILERPLATE = ["verify all existing conditions", "verify all dimensions", "field verify",
               "dimensions to face of stud", "do not scale drawings"]

EXTRACT_PROMPT = """You are reading a construction drawing set (PDF) for a pre-construction review.
EXTRACT what is written. Do not guess, do not measure, do not fill in missing values.
If a cell is blank, return an empty string "".

Return JSON with these keys:
- "project": {"name": str, "address": str, "county": str, "code_notes": str}
- "sheet_index": list of {"sheet": str, "title": str}   (from the cover sheet index, if present)
- "sheets_in_set": list of sheet numbers that actually appear as pages, in order
- "windows": list of {"mark", "size", "type", "impact", "product_approval", "qty"} (all strings)
- "doors": list of {"mark", "size", "type", "location", "impact", "product_approval"} (all strings)
- "notes": list of {"sheet": str, "text": str}   (every general/project/schedule/structural note, word for word)
"""


def extract(pdf_path):
    client = genai.Client(http_options=types.HttpOptions(timeout=180_000))
    with open(pdf_path, "rb") as f:
        pdf_part = types.Part.from_bytes(data=f.read(), mime_type="application/pdf")
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0)
    response = with_retry(lambda: client.models.generate_content(
        model=VISION_MODEL, contents=[pdf_part, EXTRACT_PROMPT], config=config))
    return json.loads(response.text)


def norm(s):
    return str(s or "").strip().lower()


def check(data):
    """Company rules, applied by code (not AI)."""
    findings = {"missing_sheets": [], "missing_disciplines": [], "approval_issues": [],
                "long_lead": [], "rfi_candidates": []}

    listed = {s["sheet"].upper() for s in data.get("sheet_index", [])}
    present = {s.upper() for s in data.get("sheets_in_set", [])}
    findings["missing_sheets"] = sorted(listed - present)

    prefixes = {re.match(r"[A-Z]+", s).group() for s in listed | present if re.match(r"[A-Z]+", s)}
    findings["missing_disciplines"] = [f"{k} ({v})" for k, v in EXPECTED_DISCIPLINES.items() if k not in prefixes]

    hvhz = "hvhz" in norm(data.get("project", {}).get("code_notes")) or "miami-dade" in norm(
        data.get("project", {}).get("county"))
    openings = [("window", w) for w in data.get("windows", [])] + \
               [("door", d) for d in data.get("doors", []) if norm(d.get("location")) != "interior"]
    for kind, o in openings:
        approval, impact = norm(o.get("product_approval")), norm(o.get("impact"))
        label = f"{o.get('mark')} ({o.get('type')})"
        problems = []  # collect all problems for this opening, then report them in one line
        if impact in {"no", "n"} and hvhz:
            problems.append("NOT impact-rated, but project is in HVHZ")
        if not approval or "tbd" in approval:
            problems.append("missing Florida Product Approval / Miami-Dade NOA")
        if problems:
            findings["approval_issues"].append(f"{label}: {'; '.join(problems)}")

    seen = set()
    text_items = [f"{w.get('type')} window" for w in data.get("windows", [])] + \
                 [d.get("type", "") for d in data.get("doors", [])] + [n["text"] for n in data.get("notes", [])]
    for item in text_items:
        for kw, why in LONG_LEAD.items():
            if kw in norm(item) and kw not in seen:
                seen.add(kw)
                findings["long_lead"].append(f"{kw.title()}: {why}. Submit within 30 days of subcontract.")

    for n in data.get("notes", []):
        text = norm(n["text"])
        if any(b in text for b in BOILERPLATE):
            continue  # skip standard boilerplate to avoid false alarms
        refs = [r.upper() for r in re.findall(r"\b[a-z]{1,2}-\d{3}\b", text)]
        missing_refs = [r for r in refs if r not in present]
        if missing_refs:
            findings["rfi_candidates"].append(f"[{n['sheet']}] \"{n['text']}\" references {', '.join(missing_refs)}, "
                                              "which is not in the drawing set.")
        elif any(p in text for p in VAGUE_PHRASES):
            findings["rfi_candidates"].append(f"[{n['sheet']}] \"{n['text']}\" is incomplete or vague.")
    for issue in findings["approval_issues"]:
        findings["rfi_candidates"].append(f"[A-601] {issue}. Request product approval or confirm substitution.")
    return findings


def to_markdown(data, f):
    p = data.get("project", {})
    def bullets(items, empty="None found."):
        return "\n".join(f"- {i}" for i in items) if items else empty
    windows = "\n".join(f"| {w.get('mark')} | {w.get('type')} | {w.get('size')} | {w.get('impact')} | "
                        f"{w.get('product_approval') or '**MISSING**'} | {w.get('qty')} |"
                        for w in data.get("windows", []))
    return f"""# Pre-Construction Drawing Review: {p.get('name', 'Unknown project')}

**DRAFT: AI-assisted first pass. Requires review by the PM / estimator before use.**
Not included by design: quantity takeoffs, measurements, clash detection.

**Location:** {p.get('address', '')} ({p.get('county', '')})  
**Code:** {p.get('code_notes', '')}  
**Sheets in set:** {', '.join(data.get('sheets_in_set', []))}

## 1. Missing sheets (listed in index, not in set)
{bullets(f['missing_sheets'])}

## 2. Missing disciplines
{bullets(f['missing_disciplines'])}

## 3. Window schedule (extracted)
| Mark | Type | Size | Impact | Product approval | Qty |
|---|---|---|---|---|---|
{windows}

## 4. Florida product approval / impact issues
{bullets(f['approval_issues'])}

## 5. Long-lead procurement items
{bullets(f['long_lead'])}

## 6. RFI candidates
{bullets(f['rfi_candidates'])}
"""


def score_against(expected_path, findings):
    """Compare to the answer key: what share of known problems did we catch?"""
    with open(expected_path) as fh:
        exp = json.load(fh)
    blob = norm(json.dumps(findings))
    checks = ([s.lower() for s in exp["sheets_listed_but_missing"]] +
              [m.lower() for m in exp["openings_missing_approval"]] +
              [d.lower() + " (" for d in exp["missing_disciplines"]] +
              [r.lower() for r in exp["rfi_candidates_should_mention"]])
    caught = [c for c in checks if c in blob]
    missed = [c for c in checks if c not in blob]
    return len(caught), len(checks), missed


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "data/drawings/palmetto_bay_townhomes.pdf"
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(OUT_DIR, exist_ok=True)

    print(f"Reading {pdf_path} with {VISION_MODEL}...")
    data = extract(pdf_path)
    findings = check(data)
    with open(os.path.join(OUT_DIR, f"{name}_extracted.json"), "w", encoding="utf-8") as fh:
        json.dump({"extracted": data, "findings": findings}, fh, indent=2, ensure_ascii=False)
    report_path = os.path.join(OUT_DIR, f"{name}_review.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(to_markdown(data, findings))

    for section, items in findings.items():
        print(f"\n{section.replace('_', ' ').upper()} ({len(items)})")
        for i in items:
            print(f"  - {i}")

    expected_path = pdf_path.replace(".pdf", "_expected.json")
    if os.path.exists(expected_path):
        caught, total, missed = score_against(expected_path, findings)
        print(f"\nAnswer-key check: caught {caught}/{total} known problems. Missed: {missed or 'none'}")
    print(f"\nReport: {report_path}")
