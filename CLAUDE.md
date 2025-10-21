# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a survey data analysis project using Python, Jupyter notebooks, and common data science libraries. The project is designed to analyze survey data stored in spreadsheets (Excel/CSV format).

## Project Structure

```
├── data/           # Place survey data files (Excel, CSV) here
├── notebooks/      # Jupyter notebooks for analysis
├── src/            # Python modules and utilities
├── outputs/        # Generated reports, charts, and results
└── requirements.txt # Python dependencies
```

## Development Commands

### Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter notebook

# Start Jupyter Lab (alternative)
jupyter lab
```

### Running Analysis
- Open `notebooks/survey_analysis_template.ipynb` as a starting point
- Place your survey data files in the `data/` directory
- Modify the data loading section to point to your specific files

## Key Dependencies

- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib/seaborn**: Static visualizations
- **plotly**: Interactive visualizations
- **jupyter/ipython**: Notebook environment
- **openpyxl**: Excel file support
- **scipy/scikit-learn/statsmodels**: Statistical analysis

## Common Workflow

1. Place survey data in `data/` directory
2. Copy and customize the template notebook
3. Load data using `pd.read_excel()` or `pd.read_csv()`
4. Perform exploratory data analysis
5. Create visualizations and cross-tabulations
6. Export results to `outputs/` directory

## Notes

- The template notebook includes sample code for common survey analysis tasks
- Use the `outputs/` directory for generated charts, summary tables, and reports
- Consider creating separate notebooks for different analysis themes or survey periods