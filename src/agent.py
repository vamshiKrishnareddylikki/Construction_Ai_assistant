"""
Tool 6: AI agent (step 2 of 3) - the agent loop.
The LLM looks at the question, decides which tool(s) to call, reads the results,
and repeats until it can give a final answer. Every step is written to a trace log.
"""
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from agent_tools import TOOL_SCHEMAS, run_tool
from llm_client import with_retry

load_dotenv(override=True)
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
client = Groq(timeout=120)

MAX_STEPS = 8  # guardrail: stop runaway loops
TRACE_PATH = "logs/agent_trace.jsonl"

SYSTEM_PROMPT = """You are the Project Operations Assistant for Coastline Builders, a South Florida
construction company. You help project managers using these tools:
- search_company_docs: company policy (contract, safety, closeout, RFIs/submittals)
- query_project_history: statistics from 500 completed projects (read-only SQL)
- list_active_projects / predict_delay: current projects and predicted schedule delays
- get_daily_digest: today's superintendent field report summaries

Rules:
1. Use tools for facts. Never invent numbers, policies, project IDs, or names.
2. For policy questions, always call search_company_docs and cite the source section.
3. For predictions, mention the model's typical error (about 9 days).
4. If the tools can't answer, say so clearly.
5. Safety questions: follow the safety manual exactly; never suggest skipping safety steps.
6. Be concise and practical: short paragraphs or bullets a busy PM can scan."""


def trace(event):
    os.makedirs(os.path.dirname(TRACE_PATH), exist_ok=True)
    event["time"] = datetime.now().isoformat(timespec="seconds")
    with open(TRACE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")


def run_agent(question, history=None, verbose=True):
    """Answer a question, using tools as needed. Returns (answer, steps)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + (history or [])
    messages.append({"role": "user", "content": question})
    steps = []
    trace({"event": "question", "question": question})
    start = time.time()

    for step in range(1, MAX_STEPS + 1):
        response = with_retry(lambda: client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS,
            tool_choice="auto", temperature=0.2))
        msg = response.choices[0].message

        if not msg.tool_calls:  # no more tools needed: this is the final answer
            answer = msg.content or ""
            trace({"event": "answer", "steps": len(steps),
                   "seconds": round(time.time() - start, 1), "answer": answer})
            return answer, steps

        # Record the model's decision, then run each tool it asked for
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            result = run_tool(tc.function.name, tc.function.arguments)
            steps.append({"tool": tc.function.name, "arguments": tc.function.arguments,
                          "result_preview": result[:300]})
            trace({"event": "tool_call", "step": step, "tool": tc.function.name,
                   "arguments": tc.function.arguments, "result_preview": result[:300]})
            if verbose:
                print(f"  🔧 step {step}: {tc.function.name}({tc.function.arguments})")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result[:6000]})

    trace({"event": "stopped", "reason": "max_steps"})
    return "I couldn't finish within the step limit. Please try a more specific question.", steps


if __name__ == "__main__":
    print("Project Operations Assistant (type 'quit' to exit)\n")
    history = []
    while True:
        question = input("You: ").strip()
        if question.lower() in {"quit", "exit", ""}:
            break
        answer, steps = run_agent(question, history)
        print(f"\nAssistant: {answer}\n")
        history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
        history = history[-6:]  # short-term memory: keep the last 3 exchanges
