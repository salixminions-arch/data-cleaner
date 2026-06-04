import streamlit as st
import pandas as pd
import re
import io

# 1. Page Configuration and Styling
st.set_page_config(page_title="Instant Spreadsheet Cleaner", page_icon="🧼")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload any messy CSV or Excel file. Clean it instantly. No data is ever stored on our servers.")

# 2. File Upload Widget
uploaded_file = st.file_uploader("Drag and drop your messy spreadsheet here", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Read the uploaded file directly into RAM memory
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    st.success("File uploaded successfully!")
    
    # 3. Running the Python Core Cleaning Logic
    # (Clean names, emails, and strip whitespace)
    for col in df.columns:
        if df[col].dtype == 'object': # If the column contains text string data
            df[col] = df[col].astype(str).str.strip()
            
    # Example: If a 'Name' column exists, auto-fix capitalization rules
    name_cols = [c for c in df.columns if 'name' in c.lower()]
    for c in name_cols:
        df[c] = df[c].str.title()

    # 4. Display a "Teaser" Preview of the cleaned data
    st.subheader("👀 Preview of your cleaned data:")
    st.dataframe(df.head(5)) # Shows only the first 5 rows to prove the code worked

    # 5. Convert the clean DataFrame back into downloadable bytes in memory
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    # 6. The Monetization Action Button
    st.write("---")
    st.subheader("📥 Download your complete cleaned file")
    st.write("Unlock unlimited access to your clean, production-ready file for a one-time processing fee.")
    
    # In a production app, you wrap this button in a Lemon Squeezy payment link script
    st.download_button(
        label="🚀 Unlock & Download Cleaned Spreadsheet ($12)",
        data=buffer,
        file_name=f"perfectly_cleaned_{uploaded_file.name}",
        mime="text/csv"
    )