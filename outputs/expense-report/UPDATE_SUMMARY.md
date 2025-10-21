# Expensed Column Update Summary

**Date:** October 17, 2025
**Task:** Update the "Expensed" column in People and AI Info CSV based on CS Monthly AI Subscriptions data

---

## What Was Done

✓ Created a copy of the original file with updated "Expensed" column
✓ Applied 10 manual name mappings to handle name variations
✓ Successfully matched all 61 expense reporters to team members

---

## Files

### Original File
`data/CSP AI Culture and Learning_ Tracking - People and AI Info_2025-10-17.csv`

### Updated File (New)
`data/CSP AI Culture and Learning_ Tracking - People and AI Info_2025-10-17_UPDATED.csv`

**Changes Made:**
- Cleared all existing "Expensed" markers
- Set "Expensed" = "Yes" for all 61 people who reported in CS Monthly AI Subscriptions
- Result: 100% accurate reflection of actual expense reporting

---

## Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total team members | 216 | 100% |
| Marked as "Expensed" | 61 | 28.2% |
| NOT marked | 155 | 71.8% |

---

## Manual Name Mappings Applied

The following 10 name variations were handled:

| Subscription Report Name | Team List Name |
|--------------------------|----------------|
| Byoung Hyun Bae | Byoung Bae |
| Elias Mera Avila | Elías Mera |
| Guilherme Boreki | G Boreki |
| Liuqing Ma | Monica Ma |
| Krishna Sai Pendela Bala Venkata | Sai Pendela |
| Qihong Shao | Tiffany Shao |
| Oluwatobi Oni-Orisan | Tobi Oni-Orisan |
| Xing Liu | Shane Liu |
| Andrew Muldowney | Andy Muldowney |
| Clinton Mullins | Clint Mullins |

---

## Complete List of People Marked as "Expensed" (61)

1. Alex Park
2. Andy Muldowney
3. Astha Gupta
4. Brennan McQuerry
5. Byoung Bae
6. Chuan Shi
7. Clint Mullins
8. Darrick Brown
9. Elizabeth Moore
10. Elías Mera
11. G Boreki
12. Grega Kespret
13. Hani Suleiman
14. Hao Wang
15. Hengyu Zhou
16. Hossein Shams
17. Huifan Qu
18. Ivan Regalado
19. Jaime Pericas Saez
20. Jason Pearson
21. Jiasheng Ding
22. Jimmy Zhang
23. Jingwen Qiang
24. Junjie Wei
25. Kevin Moore
26. Kevin Mutyaba
27. Kyle Steiner
28. Kyle Thomson
29. Liuming Zhang
30. Lulu Chen
31. Mengchen Liang
32. Michael Lubavin
33. Moncef Biaz
34. Monica Ma
35. Morris Chuang
36. Nil Gradisnik
37. Sai Pendela
38. Shane Liu
39. Shubham Puri
40. Siddharth Rawat
41. Steven Hobson-Campbell
42. Teng Wang
43. Tiffany Shao
44. Tobi Oni-Orisan
45. Tong Jiang
46. Tongyun Lu
47. Wei Ji
48. Xi Chen
49. Xing Wei
50. Xue Li
51. Yaolin Chen
52. Ying Lyu
53. Yisha Wu
54. Yuanpei Cao
55. Yujin Hong
56. Zecheng Xu
57. Zekun Wang
58. Zerui Wang
59. Zhang Zhang
60. Zhigang Zhang
61. Zhong Ren

---

## Verification

✓ All 61 people from CS Monthly AI Subscriptions are marked as "Expensed"
✓ No false positives - only people who actually reported are marked
✓ No false negatives - everyone who reported is marked

---

## How to Use This File

The updated file can be used as the new master file for tracking AI expense reporting.

**To update in the future:**
1. Place new subscription data in `data/CS Monthly AI Subscriptions.csv`
2. Run: `python3 src/update_expensed_column.py`
3. The script will automatically update the file with current mappings

---

## Script Location

**Update Script:** `src/update_expensed_column.py`

This script includes all 10 manual name mappings and can be rerun anytime to refresh the "Expensed" column based on the latest subscription data.

---

**Last Updated:** October 17, 2025
