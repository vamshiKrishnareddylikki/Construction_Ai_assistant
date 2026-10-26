"""
Tool 5: Post-training (step 1 of 3) - build the fine-tuning dataset.
Uses a large LLM to write question-and-answer pairs from each company document section.
These pairs teach a small open model to answer like a company expert (Supervised Fine-Tuning).
"""
import os
import json
import random
from build_index import split_into_chunks
from llm_client import ask_llm_json
import glob

DOCS_DIR = "docs"
OUT_DIR = "data/finetune"
PAIRS_PER_SECTION = 6
TEST_FRACTION = 0.15
SYSTEM_PROMPT = ("You are a helpful assistant for Coastline Builders, a South Florida "
                 "construction company. Answer accurately and concisely using company policy.")

PROMPT = """You are creating training data for a construction company assistant.
From the document section below, write {n} realistic questions a project manager,
superintendent, or subcontractor might ask, each with a correct, concise answer (1-3 sentences).

Rules:
- Every answer must be fully supported by the section. Do not add outside facts.
- Include exact numbers, deadlines, and percentages from the section.
- Vary the wording: some short and casual, some formal.

Return JSON: {{"pairs": [{{"question": "...", "answer": "..."}}]}}

DOCUMENT SECTION:
{text}
"""


def make_pairs(chunk):
    result = ask_llm_json(PROMPT.format(n=PAIRS_PER_SECTION, text=chunk["text"]))
    return [
        {**pair, "source": f"{chunk['source']} > {chunk['section']}"}
        for pair in result.get("pairs", [])
        if pair.get("question") and pair.get("answer")
    ]


def to_chat_format(pair):
    """The 'messages' format that Hugging Face fine-tuning tools expect."""
    return {"messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pair["question"]},
        {"role": "assistant", "content": pair["answer"]},
    ], "source": pair["source"]}


def save_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    chunks = [c for p in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))) for c in split_into_chunks(p)]

    pairs = []
    for chunk in chunks:
        new = make_pairs(chunk)
        print(f"{len(new):>2} pairs from {chunk['source']} > {chunk['section']}")
        pairs.extend(new)

    random.seed(42)
    random.shuffle(pairs)
    n_test = max(1, int(len(pairs) * TEST_FRACTION))
    test, train = pairs[:n_test], pairs[n_test:]

    save_jsonl([to_chat_format(p) for p in train], os.path.join(OUT_DIR, "train.jsonl"))
    save_jsonl([to_chat_format(p) for p in test], os.path.join(OUT_DIR, "test.jsonl"))
    print(f"\nTotal: {len(pairs)} pairs -> {len(train)} train, {len(test)} test")
    print(f"Saved to {OUT_DIR}/train.jsonl and {OUT_DIR}/test.jsonl")
    print("\nExample:")
    print(json.dumps(to_chat_format(train[0]), indent=2, ensure_ascii=False))