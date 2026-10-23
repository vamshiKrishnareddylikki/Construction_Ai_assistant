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
| 3 | Document Q&A bot (RAG) | ⏳ Next |
| 4 | Workflow automations | ⏳ Planned |
| 5 | Fine-tuned model (post-training) | ⏳ Planned |
| 6 | AI agent | ⏳ Planned |

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

## How to run
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/generate_data.py      # create realistic sample data
python src/clean_data.py         # clean it
python src/migrate_to_db.py      # migrate into SQLite
python src/make_charts.py        # charts + statistics
python src/train_delay_model.py  # train the delay predictor
```

## Note on data
Real company data is private, so this project uses a synthetic dataset of 500
projects that models realistic causes of delay: change orders, hurricane-season
starts, project complexity, and county permit times.

## Tech
Python · pandas · NumPy · SQL (SQLite) · Matplotlib · scikit-learn