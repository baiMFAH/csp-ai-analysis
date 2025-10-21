#!/usr/bin/env python3
"""
AI Expense Reporting Analysis

This script analyzes AI subscription expense reporting by comparing:
1. CS Monthly AI Subscriptions CSV - people who reported expenses
2. People and AI Info CSV - all team members

The goal is to calculate what percentage of team members reported AI expenses
and identify name mismatches.
"""

import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import os

# Display settings
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def extract_name_and_id(name_with_id):
    """Extract name and employee ID from format 'Name (ID)'"""
    if pd.isna(name_with_id) or name_with_id == '(blank)':
        return None, None

    # Match pattern: text followed by (number)
    match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', str(name_with_id))
    if match:
        name = match.group(1).strip()
        emp_id = match.group(2).strip()
        return name, emp_id
    return str(name_with_id).strip(), None


def normalize_name(name):
    """Normalize name by removing special characters, extra spaces, and converting to lowercase"""
    if pd.isna(name):
        return ''

    # Convert to string and lowercase
    name = str(name).lower()

    # Remove Chinese characters in parentheses
    name = re.sub(r'[（(][^)）]*[）)]', '', name)

    # Remove special characters except spaces and hyphens
    name = re.sub(r'[^a-z\s-]', '', name)

    # Normalize spaces
    name = ' '.join(name.split())

    return name.strip()


def find_best_match(name, choices, threshold=85, manual_mappings=None):
    """Find the best fuzzy match for a name"""
    if not name or not choices:
        return None, 0

    # Check manual mappings first
    if manual_mappings and name in manual_mappings:
        manual_match = manual_mappings[name]
        if manual_match in choices:
            return manual_match, 100  # Perfect score for manual matches

    result = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
    if result and result[1] >= threshold:
        return result[0], result[1]
    return None, result[1] if result else 0


def main():
    # Get the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    output_dir = os.path.join(base_dir, 'outputs')

    # Create outputs directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    print("="*80)
    print("AI EXPENSE REPORTING ANALYSIS")
    print("="*80)

    # 1. Load Data
    print("\n1. Loading data...")
    # The CSV has no proper headers, so we need to load it without treating first row as header
    subscriptions_df = pd.read_csv(
        os.path.join(data_dir, 'CS Monthly AI Subscriptions.csv'),
        skiprows=9,
        header=None  # Don't use first row as header
    )
    people_df = pd.read_csv(
        os.path.join(data_dir, 'CSP AI Culture and Learning_ Tracking - People and AI Info_2025-10-17.csv')
    )

    print(f"   Subscriptions data shape: {subscriptions_df.shape}")
    print(f"   People data shape: {people_df.shape}")

    # 2. Extract Names from Subscriptions Data
    print("\n2. Extracting names from subscriptions data...")

    # The CSV structure has the first column as department and second column as name
    # Check if we have at least 2 columns
    if len(subscriptions_df.columns) < 2:
        print("ERROR: CSV doesn't have expected structure")
        return

    # Use the third column (index 2) which contains names with IDs
    # Column 0 is empty (NaN), Column 1 is department, Column 2 is name
    name_column_idx = 2

    # Debug: show what columns we have
    print(f"   Available columns: {subscriptions_df.columns.tolist()}")
    print(f"   Using column index {name_column_idx}: {subscriptions_df.columns[name_column_idx]}")

    # Extract names from the correct column
    extracted_data = subscriptions_df.iloc[:, name_column_idx].apply(extract_name_and_id)
    subscriptions_df['extracted_name'] = [x[0] for x in extracted_data]
    subscriptions_df['employee_id'] = [x[1] for x in extracted_data]

    # Filter out rows without valid names
    reported_expenses = subscriptions_df[subscriptions_df['extracted_name'].notna()].copy()
    reported_expenses = reported_expenses[~reported_expenses['extracted_name'].str.contains('AI Subscription|Users|blank', na=False, regex=True)]

    # Debug: show first few extracted names
    print(f"   First few extracted names:")
    for i, name in enumerate(reported_expenses['extracted_name'].head(5).tolist()):
        print(f"     {i+1}. {name}")

    print(f"   Number of expense reports found: {len(reported_expenses)}")

    # 3. Extract Names from People and AI Info Data
    print("\n3. Processing team member data...")
    people_df['Name'] = people_df['Name'].str.strip()
    all_team_members = people_df[people_df['Name'].notna() & (people_df['Name'] != '')].copy()
    all_team_members = all_team_members[~all_team_members['Name'].str.contains('@', na=False)]

    print(f"   Total team members: {len(all_team_members)}")

    # 4. Normalize Names
    print("\n4. Normalizing names...")
    reported_expenses['normalized_name'] = reported_expenses['extracted_name'].apply(normalize_name)
    all_team_members['normalized_name'] = all_team_members['Name'].apply(normalize_name)

    # 5. Match Names Using Fuzzy Matching
    print("\n5. Performing fuzzy name matching...")

    # Define manual name mappings (normalized names from subscriptions -> team names)
    manual_mappings = {
        'byoung hyun bae': 'Byoung Bae',
        'elias mera avila': 'Elías Mera',
        'guilherme boreki': 'G Boreki',
        'liuqing ma': 'Monica Ma',
        'krishna sai pendela bala venkata': 'Sai Pendela',
        'qihong shao': 'Tiffany Shao',
        'oluwatobi oni-orisan': 'Tobi Oni-Orisan',
        'xing liu': 'Shane Liu',
        'andrew muldowney': 'Andy Muldowney',
        'clinton mullins': 'Clint Mullins'
    }

    print(f"   Using {len(manual_mappings)} manual name mappings")

    team_names_list = all_team_members['normalized_name'].tolist()
    team_names_original = all_team_members['Name'].tolist()

    # Create a mapping from normalized to original team names
    norm_to_original = dict(zip(team_names_list, team_names_original))

    matches = []
    for idx, row in reported_expenses.iterrows():
        reported_name = row['normalized_name']

        # Check manual mappings first
        if reported_name in manual_mappings:
            original_match = manual_mappings[reported_name]
            # Find the normalized version of the manual match
            matched_norm = normalize_name(original_match)
            matches.append({
                'subscription_name': row['extracted_name'],
                'normalized_subscription': reported_name,
                'matched_team_name': original_match,
                'normalized_matched': matched_norm,
                'match_score': 100,
                'is_matched': True,
                'match_type': 'manual'
            })
        else:
            # Use fuzzy matching
            best_match, score = find_best_match(reported_name, team_names_list)

            # Get the original name from the team list
            original_match = None
            if best_match:
                original_match = norm_to_original[best_match]

            matches.append({
                'subscription_name': row['extracted_name'],
                'normalized_subscription': reported_name,
                'matched_team_name': original_match,
                'normalized_matched': best_match,
                'match_score': score,
                'is_matched': score >= 85,
                'match_type': 'fuzzy'
            })

    matches_df = pd.DataFrame(matches)

    manual_matches = len(matches_df[matches_df['match_type'] == 'manual'])
    fuzzy_matches = matches_df['is_matched'].sum() - manual_matches

    print(f"   Total expense reports: {len(matches_df)}")
    print(f"   Successfully matched: {matches_df['is_matched'].sum()}")
    print(f"     - Manual mappings: {manual_matches}")
    print(f"     - Fuzzy matches: {fuzzy_matches}")
    print(f"   Unmatched: {(~matches_df['is_matched']).sum()}")

    # 6. Show Unmatched Names
    print("\n" + "="*80)
    print("UNMATCHED OR LOW CONFIDENCE MATCHES (score < 85)")
    print("="*80)
    unmatched = matches_df[~matches_df['is_matched']]
    if len(unmatched) > 0:
        for idx, row in unmatched.iterrows():
            print(f"  {row['subscription_name']} -> {row['matched_team_name']} (score: {row['match_score']})")
    else:
        print("  All names matched successfully!")

    # 7. Calculate Reporting Statistics
    print("\n" + "="*80)
    print("REPORTING STATISTICS")
    print("="*80)

    matched_reporters = matches_df[matches_df['is_matched']]['matched_team_name'].unique()
    total_team_members = len(all_team_members)
    num_reporters = len(matched_reporters)
    reporting_percentage = (num_reporters / total_team_members) * 100

    print(f"Total team members: {total_team_members}")
    print(f"Team members who reported expenses: {num_reporters}")
    print(f"Reporting percentage: {reporting_percentage:.1f}%")
    print(f"Team members who did NOT report: {total_team_members - num_reporters}")

    # 8. Identify Non-Reporters
    print("\n" + "="*80)
    print(f"TEAM MEMBERS WHO DID NOT REPORT EXPENSES ({total_team_members - num_reporters})")
    print("="*80)

    all_team_names = set(all_team_members['Name'].tolist())
    reporters_set = set(matched_reporters)
    non_reporters = sorted(all_team_names - reporters_set)

    for i, name in enumerate(non_reporters, 1):
        print(f"{i}. {name}")

    # 9. Cross-Check with 'Expensed' Column
    if 'Expensed' in people_df.columns:
        print("\n" + "="*80)
        print("CROSS-CHECK WITH 'EXPENSED' COLUMN")
        print("="*80)

        marked_expensed = all_team_members[all_team_members['Expensed'].notna() &
                                           (all_team_members['Expensed'] != '')]['Name'].tolist()

        print(f"People marked as 'Expensed' in People sheet: {len(marked_expensed)}")
        print(f"People who actually reported (from subscriptions): {num_reporters}")

        # Find discrepancies
        marked_but_not_reported = set(marked_expensed) - reporters_set
        reported_but_not_marked = reporters_set - set(marked_expensed)

        if marked_but_not_reported:
            print(f"\nMarked as 'Expensed' but NOT in subscription report ({len(marked_but_not_reported)}):")
            for name in sorted(marked_but_not_reported):
                print(f"  - {name}")

        if reported_but_not_marked:
            print(f"\nReported expenses but NOT marked in 'Expensed' column ({len(reported_but_not_marked)}):")
            for name in sorted(reported_but_not_marked):
                print(f"  - {name}")

    # 10. Export Results
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    output_path = os.path.join(output_dir, 'expense_reporting_analysis.xlsx')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # All matches
        matches_df.to_excel(writer, sheet_name='All Matches', index=False)

        # Unmatched names
        unmatched.to_excel(writer, sheet_name='Unmatched Names', index=False)

        # Non-reporters
        non_reporters_df = pd.DataFrame({'Name': non_reporters})
        non_reporters_df.to_excel(writer, sheet_name='Did Not Report', index=False)

        # Summary statistics
        summary_df = pd.DataFrame({
            'Metric': [
                'Total Team Members',
                'Reported Expenses',
                'Did Not Report',
                'Reporting Percentage',
                'Matched Names',
                'Unmatched Names'
            ],
            'Value': [
                total_team_members,
                num_reporters,
                total_team_members - num_reporters,
                f"{reporting_percentage:.1f}%",
                matches_df['is_matched'].sum(),
                (~matches_df['is_matched']).sum()
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    print(f"Results exported to: {output_path}")
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
