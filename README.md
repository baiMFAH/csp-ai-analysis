# Survey & AI Learning Resource Analysis Project

A Python workspace for analysing internal survey exports and synthesising AI learning resource recommendations using notebooks plus scripted pipelines.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Jupyter:
   ```bash
   jupyter notebook
   ```

3. Open `notebooks/survey_analysis_template.ipynb` to get started, or run the reporting scripts described below for automated outputs.

## Usage

1. Place your survey data (Excel/CSV) in the `data/` directory
2. Use the template notebook as a starting point
3. Customize the analysis for your specific survey data
4. Results will be saved to the `outputs/` directory

### AI Learning Resource Reporting

The automated enrichment pipeline lives in `src/reporting/resource_report.py`. It merges the curated CSV under `outputs/self-report/` with Wide Research captures stored in `runs/2025-02-14-ai-learning-wide/raw/`, then emits enriched datasets plus publishable reports.

Run it any time new raw research arrives:

```bash
python3 src/reporting/resource_report.py
```

Outputs are written to:

- `runs/2025-02-14-ai-learning-wide/processed/` – machine-readable JSON/CSV with categories, tags, scores, and evidence
- `runs/2025-02-14-ai-learning-wide/output/` – single-page Markdown and HTML reports ready for sharing

Refer to `AGENTS.md` for repository conventions and `prompts/ai_resource_analysis_prompts.md` for the Wide Research brief.

## Project Structure

- `data/` - Survey data files
- `notebooks/` - Jupyter analysis notebooks  
- `src/` - Python utilities
- `outputs/` - Generated results and reports
- `runs/` - Wide Research captures, processed datasets, and generated AI learning resource reports
