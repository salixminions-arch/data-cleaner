import streamlit as st
import pandas as pd
import io

# 1. PAGE CONFIG
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼", layout="centered")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload a messy file, instantly apply basic fixes, and download your perfect version.")

# RESET FUNCTIONALITY
if st.button("🔄 Reset & Clear Everything", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 2. FILE UPLOAD INTERFACE
uploaded_file = st.file_uploader("Upload your messy spreadsheet here (CSV or Excel)", type=["csv", "xlsx"])

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

    # FIX 1: Use .copy(deep=True) so cleaning 'working_df' leaves 'original_df' completely alone
    original_df = st.session_state["raw_df"]
    working_df = original_df.copy(deep=True)
    
    # 3. SIDEBAR CONTROLS
    st.sidebar.header("🛠️ Auto-Cleaning Toggles")
    drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
    remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
    clean_text = st.sidebar.checkbox("Standardize Text & Emails (Spaces & Case)", value=True)
    clean_numbers = st.sidebar.checkbox("Repair Numbers & Financials", value=True)

    # Dictionary to track metrics
    stats = {"dups_removed": 0, "empty_removed": 0, "text_fixed": 0, "nums_fixed": 0}

    # 4. AUTOMATED PROCESSING PIPELINE
    if drop_empty:
        before = len(working_df)
        working_df = working_df.dropna(how='all')
        stats["empty_removed"] = before - len(working_df)

    if remove_dup:
        before = len(working_df)
        working_df = working_df.drop_duplicates()
        stats["dups_removed"] = before - len(working_df)

    for col in working_df.columns:
        if working_df[col].isnull().all():
            continue
            
        sample_str = working_df[col].dropna().astype(str).str.strip()
        if sample_str.empty:
            continue

        # FIX 2: Better string detection and clean formatting application
        if clean_text:
            # Check if column is text/object, or if it mostly contains words
            if working_df[col].dtype == 'object' or sample_str.str.replace(r'[^a-zA-Z]', '', regex=True).str.len().gt(0).any():
                # Convert the entire series to clean strings safely
                working_df[col] = working_df[col].fillna('').astype(str).str.strip()
                
                if sample_str.str.contains(r'@', regex=True).any():
                    working_df[col] = working_df[col].str.lower()
                    stats["text_fixed"] += 1
                else:
                    working_df[col] = working_df[col].str.title()
                    stats["text_fixed"] += 1
                
                # Turn empty strings back into clean, recognizable blank cells
                working_df[col] = working_df[col].replace(['Nan', 'nan', 'None', 'none', ''], None)

        # Number Cleaning
        if clean_numbers:
            if working_df[col].dtype == 'object' and sample_str.str.contains(r'[\$,%]', regex=True).any():
                working_df[col] = working_df[col].fillna('').astype(str).str.replace(r'[\$,%]', '', regex=True)
                working_df[col] = pd.to_numeric(working_df[col], errors='coerce')
                stats["nums_fixed"] += 1
            elif pd.api.types.is_float_dtype(working_df[col]):
                working_df[col] = working_df[col].round(2)
                stats["nums_fixed"] += 1

    # 5. VISUAL PROOF DASHBOARD
    st.subheader("📊 Cleaning Report")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Empty Rows Hit", stats["empty_removed"])
    c2.metric("Duplicates Hit", stats["dups_removed"])
    c3.metric("Text Columns Fixed", stats["text_fixed"])
    c4.metric("Numbers Repaired", stats["nums_fixed"])

    # 6. BEFORE VS AFTER PREVIEW TABS
    st.subheader("👀 Data Preview")
    tab_clean, tab_original = st.tabs(["✨ Cleaned Data Version", "⚠️ Original Messy Version"])
    
    with tab_clean:
        st.write("Here is your beautifully formatted data:")
        st.dataframe(working_df.head(15), use_container_width=True)
        
    with tab_original:
        st.write("Here is the raw data exactly how you uploaded it:")
        st.dataframe(original_df.head(15), use_container_width=True)

    # 7. FIX 3: EXCEL DOWNLOAD STREAM
    st.write("---")
    base_name = st.session_state['file_name'].rsplit('.', 1)[0]
    
    # We use an in-memory buffer to build an Excel file without saving to a hard drive
    @st.cache_data(show_spinner=False)
    def convert_df_to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        return output.getvalue()

    excel_bytes = convert_df_to_excel(working_df)
