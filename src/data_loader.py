"""
Data loading utilities for survey analysis
"""
import pandas as pd
import requests
from pathlib import Path

def load_google_sheet_csv(sheet_id, gid=0):
    """
    Load data from a public Google Sheet as CSV
    
    Args:
        sheet_id: The Google Sheet ID from the URL
        gid: Sheet tab ID (default 0 for first sheet)
    
    Returns:
        pandas DataFrame
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to data folder
        data_dir = Path(__file__).parent.parent / 'data'
        data_dir.mkdir(exist_ok=True)
        csv_file = data_dir / f'survey_data_{sheet_id}.csv'
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Load as DataFrame
        df = pd.read_csv(csv_file)
        print(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Saved to: {csv_file}")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Google Sheet: {e}")
        print("Make sure the sheet is public (Anyone with link can view)")
        return None

def load_local_data(filename):
    """
    Load data from local file in data folder
    
    Args:
        filename: Name of file in data/ folder
    
    Returns:
        pandas DataFrame
    """
    data_dir = Path(__file__).parent.parent / 'data'
    file_path = data_dir / filename
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return None
    
    # Determine file type and load accordingly
    if filename.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        print(f"Unsupported file type: {filename}")
        return None
    
    print(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def preview_data(df, n_rows=5):
    """
    Show a preview of the dataset
    
    Args:
        df: pandas DataFrame
        n_rows: Number of rows to display
    """
    if df is None:
        return
    
    print("\n=== DATA PREVIEW ===")
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nFirst {n_rows} rows:")
    print(df.head(n_rows))
    print(f"\nData types:")
    print(df.dtypes)
    print(f"\nMissing values:")
    print(df.isnull().sum())

if __name__ == "__main__":
    # Example usage
    sheet_id = "1wPaM5TPKRj4pNZK75XaBLRUIeIBoJ_MwD2_Sed5W6Hk"
    df = load_google_sheet_csv(sheet_id)
    if df is not None:
        preview_data(df)