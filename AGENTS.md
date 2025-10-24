# Repository Guidelines

## Project Structure & Module Organization
`src/` holds reusable Python modules for survey parsing, expense analysis, URL enrichment, and data loading. Long-running notebooks live in `notebooks/`, and should import helpers from `src/` rather than re-implementing logic. Raw survey exports go in `data/`; never commit PII. Generated charts, tables, and serialized artifacts belong in `outputs/` or `runs/`. Keep ad-hoc network utilities under `test/` so they stay isolated from shipping code.

## Build, Test, and Development Commands
Install dependencies with `pip install -r requirements.txt`. Run exploratory work through Jupyter: `jupyter notebook notebooks/survey_analysis_template.ipynb`. Execute module entry points locally via `python -m src.ai_survey_analysis --help` (use the module flag to ensure relative imports resolve). When validating integrations, run `pytest -q` from the repo root; disable specific network-heavy cases with `-k "not url"` when offline.

## Coding Style & Naming Conventions
Target Python 3.10+ and follow PEP 8: four-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and descriptive filenames (e.g., `update_expensed_column.py`). Use docstrings on public functions to document intent and inputs. Prefer pathlib over os.path, and centralize constants at the top of modules. Before pushing, auto-format with `black .` and sort imports using `isort .` to keep diffs clean and deterministic.

## Testing Guidelines
Unit-style checks reside under `test/` and default to pytest discovery (`test_*.py`). Mirror the module under test in the filename and name test functions descriptively (`test_handles_empty_survey`). Keep network calls behind mocks; if live calls are unavoidable, mark with `@pytest.mark.network` so CI can skip them. Aim to add regression coverage alongside feature work and capture edge cases around missing data, malformed URLs, and worksheet schema drift.

## Commit & Pull Request Guidelines
Write commits in imperative Title Case, mirroring the existing history (`Add Expense Classification Script`). Focus each commit on a single concern and include context in the body when touching notebooks or data pipelines. For PRs, supply: concise summary, linked issue or task ID, screenshots of key charts (if applicable), and a validation checklist covering notebook reruns plus `pytest`. Tag reviewers familiar with the affected module and call out any manual steps required post-merge.

## Data Handling & Credentials
Strip sensitive responses and secrets before committing. Reference environment variables for API tokens (never hard-code or echo them in notebooks). When sharing notebooks, re-run `Kernel > Restart & Clear Output` so reviewers can reproduce without cached credentials.
