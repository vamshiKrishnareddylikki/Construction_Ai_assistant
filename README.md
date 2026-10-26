# Construction AI Assistant

An AI toolkit for construction project teams: data migration, project insights,
document Q&A, workflow automation, a fine-tuned model, and an AI agent.

Built around the needs of a South Florida general contractor: multifamily,
hospitality, marina, country club, commercial, and renovation projects.

## Tools
| # | Tool | Status |
|---|------|--------|
| 1 | Data migration pipeline | ✅ Done |
| 2 | Project insights + delay predictor | ✅ Done |
| 3 | Document Q&A bot (RAG) + web app | ✅ Done |
| 4 | Workflow automations | ✅ Done |
| 5 | Fine-tuned model (post-training) | ✅ Done |
| 6 | AI agent | ✅ Done |

## Tool 1: Data Migration Pipeline
Takes a messy project export, cleans it, and migrates it into a SQL database.
- Removes duplicate records
- Standardizes inconsistent county names (`broward`, `BROWARD` → `Broward`)
- Flags missing costs for human review instead of guessing
- Adds delay and cost overrun metrics
- Verifies the migration with SQL queries

## Tool 2: Project Insights + Delay Predictor
**Key finding:** change orders are the strongest driver of schedule delay (correlation 0.65).
Marina projects have the highest average overrun (9.1%) and delay (66 days).

![Average cost overrun by project type](charts/overrun_by_type.png)
![Change orders vs delay](charts/change_orders_vs_delay.png)

**Delay prediction model** (tested on projects it never saw during training):

| Model | Avg. error (MAE) | R² |
|---|---|---|
| Baseline (always guess the average) | 17.7 days | -0.06 |
| **Linear Regression (selected)** | **8.9 days** | **0.70** |
| Random Forest | 11.3 days | 0.57 |

The model cuts prediction error in half compared to the baseline.




## Tool 3: Document Q&A Bot (RAG)
Answers questions from company documents (contracts, safety manual, closeout, RFI process),
with source citations. Built for non-technical staff with a Streamlit web page.
- Splits documents into sections and embeds them (Gemini embeddings)
- Finds the most relevant sections by meaning, not keywords (cosine similarity)
- The LLM answers **only** from retrieved sections and cites them
- Says "I couldn't find that" when the answer isn't in the documents (no hallucinations)

| Question | Answer | Top match |
|---|---|---|
| Weather delay notice deadline? | 7 calendar days | 0.83 |
| Documents needed for final payment? | Lien waivers, as-builts, O&M manuals, warranties... | 0.77 |
| Remote work policy? | "I couldn't find that in the company documents" | 0.58 (no good match) |

## Tool 4: Workflow Automations
A daily pipeline that runs every morning on a schedule:
1. **Site report summarizer:** turns messy superintendent field logs into structured summaries,
   sorted by priority, flagging safety issues, RFIs, change orders, and procurement risks
2. **RFI drafter:** turns field issues into formal RFI drafts that follow company rules.
   Never invents drawing references; every draft is marked for PM review
3. **Delay risk alerts:** runs the Tool 2 model on active projects and emails AI-written alerts
   to project managers (dry-run mode by default)
4. **Daily runner:** runs all steps on a schedule with failure isolation and timestamped logs

## Reliability
- **Provider-agnostic LLM layer:** switch between Groq and Gemini with one `.env` setting
- **Retries with exponential backoff** for rate limits and server overload (429/5xx)
- **Timeouts**, so requests never hang
- **Secrets** stored in `.env`, never committed


## Tool 5: Post-Training Experiment (Fine-tuning vs. RAG)
**Question:** for company policy knowledge, is it better to fine-tune a model or use RAG?

1. **Dataset:** generated 102 Q&A pairs from company documents with an LLM (87 train / 15 test)
2. **Fine-tuning:** SFT with LoRA on Qwen3-0.6B in Google Colab (T4 GPU). Trained 0.76% of
   parameters; loss dropped from 2.24 to ~0.45 in 61 seconds
3. **Evaluation:** an LLM judge graded every answer against the reference on the 15 unseen questions

| System | Score | Correct | Hallucinations |
|---|---|---|---|
| Base model (Qwen3-0.6B) | 50.0% | 6 / 15 | 8 |
| Fine-tuned (Qwen3-0.6B + LoRA) | 26.7% | 3 / 15 | 12 |
| **RAG bot** | **96.7%** | **14 / 15** | **0** |

**Finding:** the fine-tuned model learned the company's *tone* but not its *facts*, and became more
confidently wrong (for example, saying fall protection starts at 5 feet instead of 6).
RAG is the right choice for factual company knowledge; fine-tuning is better suited to style,
format, and behavior.

**Debugging along the way:** removed an incompatible `torchao` version and switched from bfloat16
to 32-bit precision because the T4 GPU doesn't support bfloat16.


## Tool 6: AI Agent (Project Operations Assistant)
A tool-calling agent that decides on its own which tools to use, chains them, and answers
in one response. Available as a chat in the web app, with a "Tools used" panel for transparency.

**Tools the agent can call:**
| Tool | Built on |
|---|---|
| `search_company_docs` | Tool 3 (RAG) |
| `query_project_history` | Tool 1 (SQL database, read-only) |
| `rank_active_projects_by_risk`, `predict_delay` | Tool 2 (delay model) |
| `get_daily_digest` | Tool 4 (field report summarizer) |

**Guardrails:** read-only SQL (keyword check + read-only database connection), max 8 steps per
question, a system prompt that forbids invented numbers, names, and explanations, and strict
safety-manual compliance. **Memory:** last 3 exchanges. **Tracing:** every question, tool call,
and answer is logged to `logs/agent_trace.jsonl`.

**Evaluation:** an automated suite of 10 tests checks tool choice, key facts, forbidden claims,
the delete guardrail, out-of-scope questions, and safety pressure ("can we skip harnesses?").
Score history is kept in `outputs/agent_eval_history.jsonl`.

**What evaluation caught and fixed:**
- Agent checked only 5 of 8 projects and got the right answer by luck → added a ranking tool (6 steps → 1)
- Agent invented explanations ("due to permitting") → tightened the system prompt
- First eval run scored 7/9, but both failures were false negatives (rounding and a non-breaking
  space) → normalized formatting in the checker
- Agent blended project names from two systems with different IDs → aligned IDs across
  systems and added a regression test


## How to run
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/build_index.py         # build the document search index
streamlit run src/app.py          # open the Q&A web app
python src/daily_run.py           # run all daily automations
python src/generate_data.py      # create realistic sample data
python src/clean_data.py         # clean it
python src/migrate_to_db.py      # migrate into SQLite
python src/make_charts.py        # charts + statistics
python src/train_delay_model.py  # train the delay predictor
python src/agent.py               # chat with the agent in the terminal
python src/eval_agent.py          # run the agent evaluation suite
```

## Note on data
Real company data is private, so this project uses a synthetic dataset of 500
projects that models realistic causes of delay: change orders, hurricane-season
starts, project complexity, and county permit times.

## Tech
Python · pandas · NumPy · SQL (SQLite) · Matplotlib · scikit-learn · Gemini & Groq LLM APIs ·
Embeddings · RAG · Streamlit · JSON structured outputs · Task scheduling · Hugging Face · Transformers · PyTorch · PEFT/LoRA · TRL (SFT) · Google Colab · LLM-as-a-judge evals · Tool calling · AI agents · Guardrails · Tracing · Agent evals