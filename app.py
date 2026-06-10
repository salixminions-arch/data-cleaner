import streamlit as st
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼", layout="centered")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload a messy file or load a sample dataset instantly to test out the basic cleaning fixes.")

# 2. DEFINING THREE DISTINCT MOCK SPREADSHEETS
SAMPLES = {
    "Sales Data": pd.DataFrame({
        "Date": ["2026-01-01  ", "2026-01-02", "2026-01-02", None],
        "Product": ["widget a", "WIDGET B", "widget b", None],
        "Revenue": ["$1,200", "$850", "$850", None],
        "Status": ["Completed", "Pending", "Pending", None]
    }),
    "Inventory Data": pd.DataFrame({
        "SKU": ["INV-001", "INV-002", "INV-002", None],
        "Item": ["  laptop  ", "monitor", "monitor", None],
        "Stock": [45.123, 12.000, 12.000, None],
        "Warehouse": ["North", "East", "East", None]
    }),
    "Employee Directory": pd.DataFrame({
        "ID": ["E01", "E02", "E02", None],
        "Name": ["alice smith", "BOB JONES", "BOB JONES", None],
        "Email": ["ALICE@COMPANY.COM", "bob@company.com", "bob@company.com", None],
        "Department": ["Engineering", "Marketing", "Marketing", None]
    })
}

# 3. TAB NAVIGATION (MAIN APP VS VIEW SAMPLES)
app_tab, view_samples_tab = st.tabs(["💻 Main Application", "🔍 View Sample Files"])

# ==========================================
# TAB 1: MAIN APPLICATION
# ==========================================
with app_tab:
    # RESET FUNCTIONALITY
    if st.button("🔄 Reset & Clear Everything", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # 4. TWO WAYS TO LOAD DATA (UPLOAD OR SAMPLES)
    st.write("### 📥 Step 1: Choose Your Data Source")
    
    # Method A: File Upload
    uploaded_file = st.file_uploader("Option A: Upload your own messy file (CSV or Excel)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        if "raw_df" not in st.session_state or st.session_state.get("file_source") != "uploaded" or st.session_state.get("file_name") != uploaded_file.name:
            try:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state["raw_df"] = pd.read_csv(uploaded_file)
                else:
                    st.session_state["raw_df"] = pd.read_excel(uploaded_file)
                st.session_state["file_name"] = uploaded_file.name
                st.session_state["file_source"] = "uploaded"
            except Exception as e:
                st.error(f"Could not read file: {e}")
                st.stop()

    st.write("OR")
    st.write("##### Option B: One-Click Sample File Loader")
    
    # Method B: One-click buttons
    c1, c2, c3 = st.columns(3)
    if c1.button("📊 Load Sales Data", use_container_width=True):
        st.session_state["raw_df"] = SAMPLES["Sales Data"].copy()
        st.session_state["file_name"] = "Sales Data (Sample)"
        st.session_state["file_source"] = "sample"
    if c2.button("📦 Load Inventory Data", use_container_width=True):
        st.session_state["raw_df"] = SAMPLES["Inventory Data"].copy()
        st.session_state["file_name"] = "Inventory Data (Sample)"
        st.session_state["file_source"] = "sample"
    if c3.button("👥 Load Employee Directory", use_container_width=True):
        st.session_state["raw_df"] = SAMPLES["Employee Directory"].copy()
        st.session_state["file_name"] = "Employee Directory (Sample)"
        st.session_state["file_source"] = "sample"

    # 5. PIPELINE PROCESSING ENGINE
    if "raw_df" in st.session_state:
        original_df = st.session_state["raw_df"]
        working_df = original_df.copy(deep=True)
        
        # SIDEBAR CONTROLS
        st.sidebar.header("🛠️ Auto-Cleaning Toggles")
        drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
        remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
        clean_text = st.sidebar.checkbox("Standardize Text & Emails (Spaces & Case)", value=True)
        clean_numbers = st.sidebar.checkbox("Repair Numbers & Financials", value=True)

        # Dictionary to track metrics
        stats = {"dups_removed": 0, "empty_removed": 0, "text_fixed": 0, "nums_fixed": 0}

        # AUTOMATED PROCESSING PIPELINE
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

            # Text Cleaning
            if clean_text:
                if working_df[col].dtype == 'object' or sample_str.str.replace(r'[^a-zA-Z]', '', regex=True).str.len().gt(0).any():
                    working_df[col] = working_df[col].fillna('').astype(str).str.strip()
                    
                    if sample_str.str.contains(r'@', regex=True).any():
                        working_df[col] = working_df[col].str.lower()
                        stats["text_fixed"] += 1
                    else:
                        working_df[col] = working_df[col].str.title()
                        stats["text_fixed"] += 1
                    
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

        # 6. VISUAL PROOF DASHBOARD
        st.write("---")
        st.subheader(f"📊 Cleaning Report: {st.session_state['file_name']}")
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Empty Rows Hit", stats["empty_removed"])
        mc2.metric("Duplicates Hit", stats["dups_removed"])
        mc3.metric("Text Columns Fixed", stats["text_fixed"])
        mc4.metric("Numbers Repaired", stats["nums_fixed"])

        # 7. BEFORE VS AFTER PREVIEW TABS
        st.subheader("👀 Data Preview")
        tab_clean, tab_original = st.tabs(["✨ Cleaned Data Version", "⚠️ Original Messy Version"])
        
        with tab_clean:
            st.write("Here is your beautifully formatted data:")
            st.dataframe(working_df, use_container_width=True)
            
        with tab_original:
            st.write("Here is the raw data exactly how it was loaded:")
            st.dataframe(original_df, use_container_width=True)
    else:
        st.info("💡 Please upload a file or click one of the sample load buttons above to begin.")

# ==========================================
# TAB 2: VIEW SAMPLE FILES (INSPECTION PAGE)
# ==========================================
with view_samples_tab:
    st.header("🔍 Pre-Testing Data Inspection")
    st.write("Inspect the exact structure, messiness, and contents of the sample datasets before choosing to load them.")
    
    st.write("---")
    st.subheader("1. 📊 Sales Data Sample")
    st.write("Contains extra spaces, mixed string casing, duplicates, and empty rows.")
    st.dataframe(SAMPLES["Sales Data"], use_container_width=True)
    
    st.write("---")
    st.subheader("2. 📦 Inventory Data Sample")
    st.write("Contains extra column padding, unrounded decimal floats, duplicates, and empty rows.")
    st.dataframe(SAMPLES["Inventory Data"], use_container_width=True)
    
    st.write("---")
    st.subheader("3. 👥 Employee Directory Sample")
    st.write("Contains mixed case emails, messy name strings, duplicates, and empty rows.")
    st.dataframe(SAMPLES["Employee Directory"], use_container_width=True)
