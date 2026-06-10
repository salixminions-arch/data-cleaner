import streamlit as st
import pandas as pd
import io

# 1. PAGE CONFIG
st.set_page_config(page_title="Universal Sheet Cleaner - Demo", page_icon="🧼", layout="centered")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("### 🕹️ Interactive Playground")
st.write("See how the core processing engine handles chaotic, real-world data nightmares instantly. Toggle the rules in the sidebar to see it adapt in real-time.")

# --- HARDCODED MOCK DATASETS (THE "CHAOS" OPTIONS) ---
@st.cache_data
def load_scenarios():
    # Scenario A: E-Commerce / Contact List Nightmare
    ecommerce_data = {
        "Full Name": ["john doe", "  SARAH SMITH  ", "john doe", "AMY ADAMS", None, "BOB JOHNSON"],
        "Email Address": ["JOHN@gmail.com", "sarah.s@Yahoo.com", "JOHN@gmail.com", "AMY@ADAMS.CO", None, "bob@outlook.com"],
        "Phone Number": ["(555) 123-4567", "5551234567", "(555) 123-4567", "555-123-4567", None, "555.123.4567"]
    }
    df_ecom = pd.DataFrame(ecommerce_data)
    # Add a completely empty row to simulate empty row drops
    df_ecom.loc[4] = [None, None, None]

    # Scenario B: SaaS Financial Report Mess
    finance_data = {
        "Company": ["Acme Corp", "  Beta Industries", "Acme Corp", "Delta LLC", "Echo Ltd"],
        "MRR ARR": ["$1,200.50", " £4,500.00 ", "$1,200.50", " 350.00% ", "$0.00"],
        "Growth Rate": [0.12456, 0.05123, 0.12456, 0.45891, 0.0000]
    }
    df_finance = pd.DataFrame(finance_data)
    
    return {"📧 Marketing & Contact List": df_ecom, "💰 SaaS Financial Export": df_finance}

scenarios = load_scenarios()

# 2. SELECT YOUR NIGHTMARE INTERFACE
selected_scenario = st.selectbox(
    "👉 Select a messy data scenario to test:",
    list(scenarios.keys())
)

# Fetch the static raw dataset based on selection
raw_df = scenarios[selected_scenario]

# Fix 1: Clone it safely
original_df = raw_df.copy(deep=True)
working_df = original_df.copy(deep=True)
 
# 3. SIDEBAR CONTROLS & PREMIUM CTA
st.sidebar.header("🛠️ Auto-Cleaning Toggles")
drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
clean_text = st.sidebar.checkbox("Standardize Text & Emails (Spaces & Case)", value=True)
clean_numbers = st.sidebar.checkbox("Repair Numbers & Financials", value=True)

# THE PREMIUM CTA
st.sidebar.markdown("---")
st.sidebar.subheader("🚀 Go Pro & Run Offline")
st.sidebar.write("Want to clean massive, 100,000+ row customer and financial data files with 100% data privacy?")
st.sidebar.markdown(
    """
    <a href="YOUR_GUMROAD_LINK_HERE" target="_blank">
        <button style="
            background-color: #FF4B4B; 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 14px;
            width: 100%;">
            Get Desktop App ($29 One-Time)
        </button>
    </a>
    """, 
    unsafe_html=True
)

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

    # Text / Email Cleaning Logic
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

    # Number / Financial Cleaning Logic
    if clean_numbers:
        if working_df[col].dtype == 'object' and sample_str.str.contains(r'[\$,%£]', regex=True).any():
            working_df[col] = working_df[col].fillna('').astype(str).str.replace(r'[\$,%£]', '', regex=True)
            working_df[col] = pd.to_numeric(working_df[col], errors='coerce')
            stats["nums_fixed"] += 1
        elif pd.api.types.is_float_dtype(working_df[col]):
            working_df[col] = working_df[col].round(2)
            stats["nums_fixed"] += 1

# 5. VISUAL PROOF DASHBOARD
st.subheader("📊 Live Performance Report")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Empty Rows Hit", stats["empty_removed"])
c2.metric("Duplicates Hit", stats["dups_removed"])
c3.metric("Text Columns Fixed", stats["text_fixed"])
c4.metric("Numbers Repaired", stats["nums_fixed"])

# 6. BEFORE VS AFTER PREVIEW TABS
st.subheader("👀 Real-Time Transformation")
tab_clean, tab_original = st.tabs(["✨ Cleaned Version", "⚠️ Original Messy Version"])
 
with tab_clean:
    st.write("How the desktop utility formats the output instantly:")
    st.dataframe(working_df, use_container_width=True)
    
with tab_original:
    st.write("The raw data input before your structural rules run:")
    st.dataframe(original_df, use_container_width=True)

