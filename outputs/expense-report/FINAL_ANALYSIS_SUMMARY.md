# AI Expense Reporting Analysis - Final Summary

**Analysis Date:** October 17, 2025
**Data Sources:**
- CS Monthly AI Subscriptions.csv
- CSP AI Culture and Learning_ Tracking - People and AI Info_2025-10-17.csv

---

## Executive Summary

### Overall Reporting Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Team Members** | 215 | 100% |
| **Reported AI Expenses** | 61 | **28.4%** |
| **Did NOT Report** | 154 | 71.6% |

---

## Matching Results

### Name Matching Success

| Category | Count |
|----------|-------|
| Successfully Matched | 61 |
| - Manual Mappings | 8 |
| - Fuzzy Matches | 53 |
| Unmatched | 0 |

### ✓ 100% Match Rate Achieved!

All 61 expense reports were successfully matched to team members.

### Manual Name Mappings Applied

The following 8 name variations were successfully resolved through manual mapping:

1. **Byoung Hyun Bae** (subscriptions) → **Byoung Bae** (team list)
2. **Elias Mera Avila** (subscriptions) → **Elías Mera** (team list)
3. **Guilherme Boreki** (subscriptions) → **G Boreki** (team list)
4. **Liuqing Ma** (subscriptions) → **Monica Ma** (team list)
5. **Krishna Sai Pendela Bala Venkata** (subscriptions) → **Sai Pendela** (team list)
6. **Qihong Shao** (subscriptions) → **Tiffany Shao** (team list)
7. **Oluwatobi Oni-Orisan** (subscriptions) → **Tobi Oni-Orisan** (team list)
8. **Xing Liu** (subscriptions) → **Shane Liu** (team list)

---

## Data Quality Issues Identified

### 1. Missing 'Expensed' Column Markers

**13 people** reported AI expenses but are **NOT marked** in the 'Expensed' column of the People and AI Info sheet:

1. Shane Liu (matched as "Xing Liu" in subscriptions)
2. Xue Li
3. Yaolin Chen
4. Ying Lyu
5. Yisha Wu
6. Yuanpei Cao
7. Yujin Hong
8. Zecheng Xu
9. Zekun Wang
10. Zerui Wang
11. Zhang Zhang
12. Zhigang Zhang
13. Zhong Ren

**Recommendation:** Update the 'Expensed' column for these 13 team members to reflect their expense reports.

---

## People Who Did NOT Report (154 Team Members)

The complete list of 154 team members who have not reported AI expenses is available in:
- `outputs/expense_reporting_analysis.xlsx` (sheet: "Did Not Report")

### Notable Non-Reporters

Some key team members who haven't reported include managers and senior staff. Consider whether:
- They don't use AI tools (and thus have no expenses)
- They use company-provided tools only
- They need a reminder to submit expense reports

---

## Generated Files

### 1. Excel Report
**File:** `outputs/expense_reporting_analysis.xlsx`

**Sheets:**
- **Summary**: Key statistics and metrics
- **All Matches**: Complete list of 60 matched names with match scores and types
- **Unmatched Names**: The 1 remaining unmatched name
- **Did Not Report**: Full list of 155 non-reporters

### 2. Analysis Scripts
- **Python Script:** `src/analyze_expense_reporting.py` (re-runnable)
- **Jupyter Notebook:** `notebooks/ai_expense_reporting_analysis.ipynb` (for interactive analysis)

---

## Recommendations

### Immediate Actions

1. ✓ **All names successfully matched** - No further name verification needed

2. **Update Expensed markers:**
   - Mark the 13 people listed above as "Expensed" in the People and AI Info sheet

3. **Follow up with non-reporters:**
   - Consider sending reminders to the 154 team members who haven't reported
   - Verify if they actually have AI expenses to report

### Process Improvements

1. **Standardize name formats:**
   - Use consistent name formats across systems (full name vs. shortened)
   - Document English name vs. Chinese name preferences

2. **Regular reconciliation:**
   - Run this analysis monthly to catch discrepancies early
   - Automate the process with the provided scripts

3. **Improve data entry:**
   - Consider adding employee IDs to both systems for easier matching
   - The subscription report already includes IDs - leverage them

---

## Technical Notes

### Name Matching Methodology

- **Fuzzy matching** using token sort ratio algorithm (threshold: 85% similarity)
- **Manual mappings** for known name variations
- **Normalization** removes special characters, Chinese characters, and standardizes spacing

### Data Processing

- **Expense report entries:** 61 valid entries (after filtering blanks and totals)
- **Team members:** 215 active members
- **Match rate:** 100% (61 out of 61 successfully matched)

---

## Contact

For questions about this analysis or to request re-runs with updated data, please contact the analysis team.

**Last Updated:** October 17, 2025
