import streamlit as st
import pandas as pd
import re
import io

# 1. Page Frame Configuration
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload your data once. Your file will remain safely cached in system memory while you modify formatting options.")

# 2. File Upload Box (Keeps track of data using Session State memory)
uploaded_file = st.file_uploader("Upload your messy spreadsheet here", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Save raw file state into permanent memory cache if it isn't there yet
    if "raw_df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
        if uploaded_file.name.endswith('.csv'):
            st.session_state["raw_df"] = pd.read_csv(uploaded_file)
        else:
            st.session_state["raw_df"] = pd.read_excel(uploaded_file)
        st.session_state["file_name"] = uploaded_file.name

    # Always clone a fresh working copy from our saved backup memory data
    working_df = st.session_state["raw_df"].copy()
    
    # 3. SIDEBAR CONTROLS (Toggling these will smoothly trigger live calculation changes)
    st.sidebar.header("🛠️ Cleaning Options")
    remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
    drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
    clean_contacts = st.sidebar.checkbox("Clean Contact Info (Names, Emails, Phones)", value=True)
    fix_dates_money = st.sidebar.checkbox("Standardize Dates & Repair Financial Data", value=True)
    
    # NEW PREMIUM MODULINE SWITCH
    st.sidebar.subheader("🚀 Advanced Cleaning Modules")
    validate_emails = st.sidebar.checkbox("Validate Email Structural Integrity", value=True)

    # 4. PROCESSING PIPELINE (Executes on your active working layout)
    if drop_empty:
        working_df = working_df.dropna(how='all')

    if remove_dup:
        working_df = working_df.drop_duplicates()

    if clean_contacts:
        if 'Name' in working_df.columns:
            working_df['Name'] = working_df['Name'].astype(str).str.strip().str.title().replace('Null', None)
        if 'Email' in working_df.columns:
            working_df['Email'] = working_df['Email'].astype(str).str.strip().str.lower()
        if 'Phone' in working_df.columns:
            working_df['Phone'] = working_df['Phone'].astype(str).str.replace(r'\D', '', regex=True)
            working_df['Phone'] = working_df['Phone'].replace('', 'MISSING')

    # NEW: EMAIL VALIDATION BLOCK (Using vectorized RegEx)
    if validate_emails:
        # Smart matching: find any column containing "email" or "e-mail"
        email_cols = [c for c in working_df.columns if 'email' in c.lower() or 'e-mail' in c.lower()]
        
        # Comprehensive email syntax pattern matching requirement (username@domain.extension)
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        for c in email_cols:
            # Force cleanup first to minimize parsing errors
            working_df[c] = working_df[c].astype(str).str.strip().str.lower()
            
            # Execute live RegEx matching line-by-line across memory index
            working_df[f'{c}_Status'] = working_df[c].apply(
                lambda x: "✅ Valid" if re.match(email_pattern, str(x)) else "❌ Invalid Format"
            )

    if fix_dates_money:
        if 'Signup Date' in working_df.columns:
            working_df['Signup Date'] = pd.to_datetime(working_df['Signup Date'], errors='coerce').dt.strftime('%Y-%m-%d')
        if 'Revenue' in working_df.columns:
            working_df['Revenue'] = working_df['Revenue'].astype(str).str.replace(r'[$,]', '', regex=True)
            working_df['Revenue'] = pd.to_numeric(working_df['Revenue'], errors='coerce').fillna(0.0)

    # 5. UI PREVIEW RENDER (Updates instantly when checkboxes are flipped)
    st.subheader("👀 Cleaned Data Preview")
    st.dataframe(working_df.head(5))git commit -m "Your descriptive update message"

    # 6. CONVERT CLEAN DATA INTO LIVE DOWNLOAD STREAM
    output_buffer = io.BytesIO()

    if uploaded_file.name.endswith('.csv'):
        working_df.to_csv(output_buffer, index=False)

        download_name = f"cleaned_{uploaded_file.name}"
        mime_type = "text/csv"

    else:
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            working_df.to_excel(writer, index=False)

        download_name = f"cleaned_{uploaded_file.name}"
        mime_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    output_buffer.seek(0)

    # 7. DOWNLOAD BUTTON (Now works natively on click without dropping data)
    st.write("---")
    st.download_button(
        label="🚀 Download Cleaned Spreadsheet",
        data=output_buffer.getvalue(),
        file_name=download_name,
        mime=mime_type
    )