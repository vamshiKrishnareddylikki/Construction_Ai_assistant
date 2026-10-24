"""
Tool 3: Document Q&A bot (step 2 of 2) - answer questions from company documents.
RAG = Retrieval-Augmented Generation:
  1. Retrieve: find the document chunks most similar to the question
  2. Augment:  put those chunks into the prompt
  3. Generate: have the LLM answer using only those chunks
"""
import json
import sys
import numpy as np
from build_index import embed, INDEX_PATH
from llm_client import ask_llm

TOP_K = 3  # how many chunks to give the model


def load_index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        return json.load(f)


def cosine_similarity(a, b):
    """1.0 = same meaning, 0 = unrelated."""
    a, b = np.array(a), np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve(question, index, k=TOP_K):
    q_vec = embed(question, is_query=True)
    scored = [(cosine_similarity(q_vec, c["embedding"]), c) for c in index]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def build_prompt(question, matches):
    context = "\n\n".join(
        f"[Source {i + 1}: {c['source']} > {c['section']}]\n{c['text']}"
        for i, (_, c) in enumerate(matches)
    )
    return f"""You are an assistant for construction project managers.
Answer the question using ONLY the company documents below.
If the answer is not in the documents, say "I couldn't find that in the company documents."
Be concise and cite sources like [Source 1].

COMPANY DOCUMENTS:
{context}

QUESTION: {question}
ANSWER:"""


def answer(question, index):
    matches = retrieve(question, index)
    reply = ask_llm(build_prompt(question, matches))
    return reply, matches


if __name__ == "__main__":
    index = load_index()
    question = " ".join(sys.argv[1:]) or "How many days do subcontractors have to submit a weather delay notice?"
    reply, matches = answer(question, index)
    print(f"Q: {question}\n")
    print(f"A: {reply}\n")
    print("Retrieved sections:")
    for score, c in matches:
        print(f"  {score:.2f}  {c['source']} > {c['section']}")