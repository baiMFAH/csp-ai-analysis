#!/usr/bin/env python3
"""
Update Expensed Column

This script updates the 'Expensed' column in the People and AI Info CSV
based on who actually reported expenses in the CS Monthly AI Subscriptions CSV.
"""

import pandas as pd
import re
import os


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


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    print("="*80)
    print("UPDATING EXPENSED COLUMN")
    print("="*80)

    # Load the subscription data
    print("\n1. Loading CS Monthly AI Subscriptions data...")
    subscriptions_df = pd.read_csv(
        os.path.join(data_dir, 'CS Monthly AI Subscriptions.csv'),
        skiprows=9,
        header=None
    )

    # Extract names from column 2
    subscriptions_df['extracted_name'] = subscriptions_df[2].apply(lambda x: extract_name_and_id(x)[0])

    # Filter valid names
    reported_expenses = subscriptions_df[subscriptions_df['extracted_name'].notna()].copy()
    reported_expenses = reported_expenses[~reported_expenses['extracted_name'].str.contains('AI Subscription|Users|blank', na=False, regex=True)]

    # Normalize names
    reported_expenses['normalized_name'] = reported_expenses['extracted_name'].apply(normalize_name)

    print(f"   Found {len(reported_expenses)} people who reported expenses")

    # Define manual name mappings
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

    # Create set of people who reported (apply manual mappings)
    reporters = set()
    for norm_name in reported_expenses['normalized_name'].tolist():
        if norm_name in manual_mappings:
            reporters.add(manual_mappings[norm_name])
        else:
            # Find original name from reported expenses
            original = reported_expenses[reported_expenses['normalized_name'] == norm_name]['extracted_name'].iloc[0]
            reporters.add(original)

    print(f"   Identified {len(reporters)} unique reporters (after manual mappings)")

    # Load the People and AI Info data
    print("\n2. Loading People and AI Info data...")
    people_file = os.path.join(data_dir, 'CSP AI Culture and Learning_ Tracking - People and AI Info_2025-10-17_UPDATED.csv')
    people_df = pd.read_csv(people_file)

    print(f"   Loaded {len(people_df)} team members")

    # Normalize team member names for matching
    people_df['normalized_name'] = people_df['Name'].apply(normalize_name)

    # Match and update Expensed column
    print("\n3. Updating Expensed column...")

    # Clear existing Expensed column
    people_df['Expensed'] = ''

    matched_count = 0
    unmatched_reporters = []

    for reporter_name in reporters:
        reporter_norm = normalize_name(reporter_name)

        # Find match in people_df
        mask = people_df['normalized_name'] == reporter_norm

        if mask.any():
            people_df.loc[mask, 'Expensed'] = 'Yes'
            matched_count += 1
        else:
            # Try fuzzy match with original names
            match_found = False
            for idx, row in people_df.iterrows():
                if reporter_norm in row['normalized_name'] or row['normalized_name'] in reporter_norm:
                    people_df.at[idx, 'Expensed'] = 'Yes'
                    matched_count += 1
                    match_found = True
                    break

            if not match_found:
                unmatched_reporters.append(reporter_name)

    print(f"   Matched {matched_count} reporters to team members")

    if unmatched_reporters:
        print(f"\n   WARNING: {len(unmatched_reporters)} reporters could not be matched:")
        for name in unmatched_reporters:
            print(f"     - {name}")

    # Remove the temporary normalized_name column
    people_df = people_df.drop('normalized_name', axis=1)

    # Save the updated file
    print("\n4. Saving updated file...")
    people_df.to_csv(people_file, index=False)
    print(f"   Saved to: {people_file}")

    # Show summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total team members: {len(people_df)}")
    print(f"People marked as 'Expensed': {(people_df['Expensed'] == 'Yes').sum()}")
    print(f"People NOT marked: {(people_df['Expensed'] != 'Yes').sum()}")
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)

    # Show who is marked as Expensed
    print("\n5. People marked as 'Expensed':")
    expensed_people = people_df[people_df['Expensed'] == 'Yes']['Name'].tolist()
    for i, name in enumerate(sorted(expensed_people), 1):
        print(f"   {i}. {name}")


if __name__ == "__main__":
    main()
