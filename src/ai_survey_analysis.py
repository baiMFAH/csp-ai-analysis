from airbnb_identity import GoogleIapCredential
from openai import AzureOpenAI
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

# Setup AI Gateway
# See the list of available models at https://devaigateway.a.musta.ch/v1/models
# And contact #ai-for-dev-productivity for current recommendations for your usage case
# ('best_coding' aliases to the strongest current model for coding)
endpoint = "https://devaigateway.a.musta.ch"
auth = GoogleIapCredential().authenticate(endpoint)
model_name = "o3-high"

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_version="2025-01-01-preview",
    azure_ad_token=auth.headers["Authorization"].split()[-1]
)

# Load survey data
print("Loading survey data...")
survey_df = pd.read_csv('data/CSP AI Use and Confidence (Sept 2025) (Responses)_2025_10_03.csv')
print(f"Total responses: {len(survey_df)}")

# Prepare survey data summary for AI analysis
col_frequency = survey_df.columns[2]
col_contexts = survey_df.columns[3]
col_barriers = survey_df.columns[4]
col_comfort = survey_df.columns[5]
col_understanding = survey_df.columns[6]
col_risks = survey_df.columns[7]
col_growth = survey_df.columns[8]
col_optional = survey_df.columns[9]

# Create a data summary
data_summary = f"""
Survey: CSP AI Use and Confidence (September 2025)
Total Responses: {len(survey_df)}

Question 1: Usage Frequency
{survey_df[col_frequency].value_counts().to_string()}

Question 2: AI Use Contexts (top 10)
{survey_df[col_contexts].value_counts().head(10).to_string()}

Question 3: Barriers to Adoption (top 10)
{survey_df[col_barriers].value_counts().head(10).to_string()}

Question 4: Comfort Level
{survey_df[col_comfort].value_counts().to_string()}

Question 5: Understanding Strengths/Limitations (1-5 scale)
{survey_df[col_understanding].value_counts().sort_index().to_string()}
Average: {survey_df[col_understanding].mean():.2f}

Question 6: Understanding Risks (1-5 scale)
{survey_df[col_risks].value_counts().sort_index().to_string()}
Average: {survey_df[col_risks].mean():.2f}

Question 7: Growth Areas (top 10)
{survey_df[col_growth].value_counts().head(10).to_string()}

Question 8: Notable Use Cases (sample of 10)
{survey_df[col_optional].dropna().head(10).to_string()}
"""

# Create the analysis prompt
analysis_prompt = f"""You are an expert data analyst specializing in organizational AI adoption and learning.

Analyze the following survey data from CSP (Customer Service Platform) team about their AI use and confidence.

{data_summary}

Please provide a comprehensive analysis covering:

1. **Key Themes & Patterns**: What are the most significant patterns you observe across the responses?

2. **Strengths**: What is the team doing well in terms of AI adoption?

3. **Challenges & Gaps**: What are the major obstacles and skill gaps that need to be addressed?

4. **Hidden Insights**: What non-obvious insights can you extract from the data that might not be immediately apparent?

5. **Actionable Recommendations**: Provide 5-7 specific, actionable recommendations prioritized by impact.

6. **Geographic Considerations**: Note any geographic-specific challenges mentioned.

7. **Culture & Sentiment**: What does the data reveal about the team's overall attitude and culture around AI?

Be specific, data-driven, and insightful. Focus on actionable intelligence rather than just restating the data.
"""

print("\nSending data to GPT-4o for analysis...")
print("This may take a minute...\n")

# Call GPT-4o
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "system",
            "content": "You are an expert data analyst specializing in organizational AI adoption, learning & development, and team culture analysis."
        },
        {
            "role": "user",
            "content": analysis_prompt
        }
    ],
    temperature=0.7,
    max_tokens=4000
)

# Get the analysis
ai_analysis = response.choices[0].message.content

print("=" * 80)
print("AI-GENERATED INSIGHTS FROM GPT-4O")
print("=" * 80)
print(ai_analysis)
print("=" * 80)

# Save to file
output_dir = Path('outputs/survey-insights')
output_dir.mkdir(parents=True, exist_ok=True)

date_suffix = datetime.now().strftime('%Y_%m_%d')
output_file = output_dir / f'ai_qualitative_analysis_{model_name}_{date_suffix}.txt'

with open(output_file, 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("CSP AI SURVEY - QUALITATIVE INSIGHTS (GPT-4O ANALYSIS)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Model: {model_name}\n")
    f.write(f"Total Survey Responses Analyzed: {len(survey_df)}\n")
    f.write("=" * 80 + "\n\n")
    f.write(ai_analysis)
    f.write("\n\n" + "=" * 80 + "\n")

print(f"\n✓ Saved to: {output_file}")

# Also save as Markdown for Google Docs (import as-is)
output_file_md = output_dir / f'ai_qualitative_analysis_{model_name}_{date_suffix}.md'

with open(output_file_md, 'w') as f:
    f.write('# CSP AI Survey - Qualitative Insights (GPT-4O Analysis)\n\n')
    f.write(f'**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  \n')
    f.write(f'**Model:** {model_name}  \n')
    f.write(f'**Survey Responses Analyzed:** {len(survey_df)}\n\n')
    f.write('---\n\n')
    f.write(ai_analysis)

print(f"✓ Saved Markdown to: {output_file_md}")
print("  (Can be imported directly into Google Docs via File > Import)")
