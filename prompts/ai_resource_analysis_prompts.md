# AI Learning Resource Analysis Prompts

## Main Task

Read wide_research_prompt_en.md, and use Wide Research to complete the following task:

**Input file:**
`/Users/bai_xiao/Documents/Code/claude-playground/csp-ai-analysis/outputs/self-report/curated_resource_list_2025-10-17.csv`

This file contains AI learning resources submitted by team members. Only the URLs are accurate. I want to accomplish the following:

## Task Breakdown

### 1. Extract Data
Extract the title and URL from the file.

### 2. Content Summary
Use Wide Research to read the content of each URL and summarize it in the format of "title + brief description".

### 3. Additional data
Use web search tool to search for description or reviews of the given resource, and enrich the description generated in step 2. to have a more comprehensive overview of the resource

### 4. Categorization by Type and Topic
Review the summarized results and categorize these learning resources by type and topic.

### 5. Tag Assignment
Call Wide Research again to assign five tags to each link based on its content

### 6. Recommendation Score
Add a column to give each resource a recommendation score (1-5), where 5 means highly recommended. Also, provide a reasoning brief to explain why it's recommended.

### 7. Comprehensive Report Generation
Based on all the above content, compile and organize a single-page in-depth analysis report.

**Report Objectives:**
- The fundamental goal is to recommend the most valuable AI learning resources to share with team members
- Emphasize depth of thinking and provide surprising insights
- Make people feel enlightened while being able to easily verify its correctness
- Do not abbreviate results obtained from Wide Research - include them directly in the final report
- Publish the final results

**Additional Notes:**
- No need to save the original text of each resource
- When information is insufficient to analyze resource content, try using web search to search the title and obtain more useful review information as a reference for summarization
- Generate final report in both html and md
