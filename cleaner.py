import pandas as pd
import re

def clean_spreadsheet(input_file, output_file):
    print(f"Loading {input_file}...")
    # 1. Load the data into a Pandas DataFrame
    df = pd.read_csv(input_file) if input_file.endswith('.csv') else pd.read_excel(input_file)

    # 2. Text Scrubbing (Vectorized: Capitalize names, lowercase emails, strip trailing whitespace)
    if 'Name' in df.columns:
        df['Name'] = df['Name'].astype(str).str.strip().str.title().replace('Null', None)
    
    if 'Email' in df.columns:
        df['Email'] = df['Email'].astype(str).str.strip().str.lower()

    # 3. Standardize Phone Numbers (Strip dashes, dots, spaces, leave a clean 10-digit string)
    if 'Phone' in df.columns:
        df['Phone'] = df['Phone'].astype(str).str.replace(r'\D', '', regex=True)
        df['Phone'] = df['Phone'].replace('', 'MISSING')

    # 4. Standardize Irregular Dates into YYYY-MM-DD format
    if 'Signup Date' in df.columns:
        df['Signup Date'] = pd.to_datetime(df['Signup Date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # 5. Financial Data Repair (Strip '$' and ',' characters, convert to float, fill missing values with 0)
    if 'Revenue' in df.columns:
        df['Revenue'] = df['Revenue'].astype(str).str.replace(r'[$,]', '', regex=True)
        df['Revenue'] = pd.to_numeric(df['Revenue'], errors='coerce').fillna(0.0)

    # 6. Export beautifully cleaned data
    if output_file.endswith('.csv'):
        df.to_csv(output_file, index=False)
    else:
        df.to_excel(output_file, index=False)
        
    print(f" Success! Cleaned file saved as: {output_file}")

# Execution Rule
if __name__ == "__main__":
    clean_spreadsheet("Messy file.xlsx", "Clean file.xlsx")