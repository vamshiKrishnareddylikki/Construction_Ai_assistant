"""
Tool 5: Post-training (step 3 of 3) - the scoreboard.
Compares three ways of answering company-policy questions on the same 15 unseen test questions:
  1. Base model (Qwen3-0.6B, no training)
  2. Fine-tuned model (Qwen3-0.6B + LoRA)
  3. RAG bot (looks up the company documents, then answers)
A larger LLM acts as the grader ("LLM-as-a-judge"), comparing each answer to the reference answer.
"""
import json
from ask_docs import load_index, answer as rag_answer
from llm_client import ask_llm_json

RESULTS_PATH = "outputs/finetune/finetune_results.json"
SCORES_PATH = "outputs/finetune/scoreboard.json"
REPORT_PATH = "outputs/finetune/scoreboard.md"
SYSTEMS = ["base", "finetuned", "rag"]
POINTS = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}

JUDGE_PROMPT = """You are grading answers to a construction company policy question.
Compare the CANDIDATE answer to the REFERENCE answer (which is correct).

Grading:
- "correct": gives the same key facts as the reference (numbers, deadlines, yes/no). Extra wording is fine.
- "partial": partly right, but missing or vague on a key fact.
- "incorrect": wrong, contradicts the reference, or no real answer.
Also set "hallucination" to true if the candidate states a specific fact (number, rule, deadline)
that contradicts the reference.

QUESTION: {question}
REFERENCE: {reference}
CANDIDATE: {candidate}

Return JSON: {{"grade": "correct" | "partial" | "incorrect", "hallucination": true | false, "reason": "one short sentence"}}
"""


def judge(question, reference, candidate):
    result = ask_llm_json(JUDGE_PROMPT.format(
        question=question, reference=reference, candidate=candidate[:1500]))
    result["grade"] = result.get("grade", "incorrect").lower()
    if result["grade"] not in POINTS:
        result["grade"] = "incorrect"
    return result


def summarize(scored):
    rows = []
    for system in SYSTEMS:
        grades = [item[system]["grade"] for item in scored]
        n = len(grades)
        rows.append({
            "system": system,
            "score_pct": round(100 * sum(POINTS[g] for g in grades) / n, 1),
            "correct": grades.count("correct"),
            "partial": grades.count("partial"),
            "incorrect": grades.count("incorrect"),
            "hallucinations": sum(item[system]["hallucination"] for item in scored),
            "n": n,
        })
    return rows


def write_report(summary, scored):
    names = {"base": "Base model (Qwen3-0.6B)", "finetuned": "Fine-tuned (Qwen3-0.6B + LoRA)",
             "rag": "RAG bot (document lookup + LLM)"}
    lines = ["# Scoreboard: Base vs. Fine-tuned vs. RAG", "",
             f"Graded on {summary[0]['n']} test questions the fine-tuned model never saw during training.",
             "", "| System | Score | Correct | Partial | Incorrect | Hallucinations |",
             "|---|---|---|---|---|---|"]
    for r in summary:
        lines.append(f"| {names[r['system']]} | **{r['score_pct']}%** | {r['correct']} | "
                     f"{r['partial']} | {r['incorrect']} | {r['hallucinations']} |")
    lines += ["", "## Every question", ""]
    for item in scored:
        lines.append(f"**Q:** {item['question']}  ")
        lines.append(f"**Reference:** {item['reference']}  ")
        for system in SYSTEMS:
            s = item[system]
            flag = " ⚠️ hallucination" if s["hallucination"] else ""
            lines.append(f"- *{system}* ({s['grade']}{flag}): {s['answer'][:300]}")
        lines.append("")
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    with open(RESULTS_PATH, encoding="utf-8") as f:
        results = json.load(f)["results"]
    index = load_index()

    scored = []
    for i, r in enumerate(results, start=1):
        print(f"[{i}/{len(results)}] {r['question']}")
        answers = {
            "base": r["base_answer"],
            "finetuned": r["finetuned_answer"],
            "rag": rag_answer(r["question"], index)[0],
        }
        item = {"question": r["question"], "reference": r["reference"]}
        for system, ans in answers.items():
            item[system] = {"answer": ans, **judge(r["question"], r["reference"], ans)}
        print("    " + "  ".join(f"{s}={item[s]['grade']}" for s in SYSTEMS))
        scored.append(item)

    summary = summarize(scored)
    with open(SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "items": scored}, f, indent=2, ensure_ascii=False)
    write_report(summary, scored)

    print("\n=== SCOREBOARD ===")
    print(f"{'System':<12}{'Score':>8}{'Correct':>9}{'Partial':>9}{'Wrong':>7}{'Halluc.':>9}")
    for r in summary:
        print(f"{r['system']:<12}{r['score_pct']:>7}%{r['correct']:>9}{r['partial']:>9}"
              f"{r['incorrect']:>7}{r['hallucinations']:>9}")
    print(f"\nFull report: {REPORT_PATH}")