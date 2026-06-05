import streamlit as st
import pandas as pd
import io

# 1. PAGE CONFIG
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼", layout="centered")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload a messy file, instantly apply basic fixes, and download your perfect version.")

# RESET FUNCTIONALITY
# Clicking this will wipe the session state and rerun the app cleanly
if st.button("🔄 Reset & Clear Everything", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 2. SINGLE FILE UPLOAD INTERFACE
uploaded_file = st.file_uploader("Upload your messy spreadsheet here (CSV or Excel)", type=["csv", "xlsx"], accept_file_output=False)

if uploaded_file is not None:
    # Cache raw file state to prevent unnecessary re-uploads on widget toggles
    if "raw_df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state["raw_df"] = pd.read_csv(uploaded_file)
            else:
                st.session_state["raw_df"] = pd.read_excel(uploaded_file)
            st.session_state["file_name"] = uploaded_file.name
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()

    working_df = st.session_state["raw_df"].copy()
    
    # 3. SIDEBAR CONTROLS (Your basic requested features)
    st.sidebar.header("🛠️ Auto-Cleaning Toggles")
    drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
    remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
    clean_text = st.sidebar.checkbox("Standardize Text & Emails (Spaces & Case)", value=True)
    clean_numbers = st.sidebar.checkbox("Repair Numbers & Financials", value=True)

    # Dictionary to track metrics for the user satisfaction dashboard
    stats = {"dups_removed": 0, "empty_removed": 0, "text_fixed": 0, "nums_fixed": 0}

    # 4. AUTOMATED PROCESSING PIPELINE
    
    # Feature: Drop Empty Rows
    if drop_empty:
        before = len(working_df)
        working_df = working_df.dropna(how='all')
        stats["empty_removed"] = before - len(working_df)

    # Feature: Remove Duplicates
    if remove_dup:
        before = len(working_df)
        working_df = working_df.drop_duplicates()
        stats["dups_removed"] = before - len(working_df)

    # Smart Scanning Loops across all columns
    for col in working_df.columns:
        # Skip fully empty columns
        if working_df[col].isnull().all():
            continue
            
        # Create a clean string version of the column to scan its patterns safely
        sample_str = working_df[col].dropna().astype(str).str.strip()
        if sample_str.empty:
            continue

        # Feature: Text & Email Automation (Spaces, Case fixing)
        if clean_text and working_df[col].dtype == 'object':
            # Check if it looks like an email column
            if sample_str.str.contains(r'@', regex=True).any():
                working_df[col] = working_df[col].fillna('').astype(str).str.strip().str.lower()
                working_df[col] = working_df[col].replace(['nan', 'none', ''], None)
                stats["text_fixed"] += 1
            # Standard text cleaning (Names, Cities, formatting text)
            else:
                working_df[col] = working_df[col].fillna('').astype(str).str.strip().str.title()
                working_df[col] = working_df[col].replace(['nan', 'none', ''], None)
                stats["text_fixed"] += 1

        # Feature: Number & Currency Automation
        if clean_numbers:
            # Check if strings contain hidden money formatting masking real numbers (like $ or , )
            if working_df[col].dtype == 'object' and sample_str.str.contains(r'[\$,%]', regex=True).any():
                working_df[col] = working_df[col].fillna('').astype(str).str.replace(r'[\$,%]', '', regex=True)
                working_df[col] = pd.to_numeric(working_df[col], errors='coerce')
                stats["nums_fixed"] += 1
            # Clean floating numbers down to standard 2 decimal places
            elif pd.api.types.is_float_dtype(working_df[col]):
                working_df[col] = working_df[col].round(2)
                stats["nums_fixed"] += 1

    # 5. VISUAL PROOF DASHBOARD (Shows the user what they saved time on)
    st.subheader("📊 Cleaning Report")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Empty Rows Hit", stats["empty_removed"])
    c2.metric("Duplicates Hit", stats["dups_removed"])
    c3.metric("Text Columns Fixed", stats["text_fixed"])
    c4.metric("Numbers Repaired", stats["nums_fixed"])

    # 6. UI PREVIEW RENDER
    st.subheader("👀 Cleaned Data Preview")
    st.dataframe(working_df.head(15), use_container_width=True)

    # 7. DOWNLOAD STREAM
    st.write("---")
    base_name = st.session_state['file_name'].rsplit('.', 1)[0]
    
    # Cache download to prevent dataset re-compiling unless the data changes
    @st.cache_data(show_spinner=False)
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv_bytes = convert_df(working_df)

    st.download_button(
        label="🚀 Download Cleaned CSV",
        data=csv_bytes,
        file_name=f"cleaned_{base_name}.csv",
        mime="text/csv",
        use_container_width=True
    )