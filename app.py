import streamlit as st
import pandas as pd
import io

# 1. Page Frame Setup
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼")
st.title("🧼 Universal Spreadsheet Data Cleaner")
st.write("Upload your data once. Your file will remain safely cached in system memory while you modify formatting options.")

# 2. FILE UPLOAD INTERFACE (Keeps track of data using Session State memory)
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
    
    # 3. SIDEBAR CONTROLS (Toggling these will now smoothly trigger live calculation changes)
    st.sidebar.header("🛠️ Cleaning Options")
    remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
    drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)
    clean_contacts = st.sidebar.checkbox("Clean Contact Info (Names, Emails, Phones)", value=True)
    fix_dates_money = st.sidebar.checkbox("Standardize Dates & Repair Financial Data", value=True)

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

    # Wrap individual processing steps defensively
    if fix_dates_money:
        try:
            date_cols = working_df(['date', 'time', 'created', 'signup'])
            for c in date_cols:
                working_df[c] = pd.to_datetime(working_df[c], errors='coerce').dt.strftime('%Y-%m-%d')
        except Exception as e:
            st.sidebar.warning("⚠️ Some complex date formats couldn't be parsed automatically.")

        try:
            money_cols = working_df(['revenue', 'amount', 'price', 'sales', 'cost', 'total'])
            for c in money_cols:
                if working_df[c].dtype == 'object':
                    working_df[c] = working_df[c].astype(str).str.replace(r'[$,\s]', '', regex=True)
                working_df[c] = pd.to_numeric(working_df[c], errors='coerce').fillna(0.0)
        except Exception as e:
            st.sidebar.warning("⚠️ Money normalization skipped on highly complex character strings.")
            
    # 5. UI PREVIEW RENDER (Updates instantly when checkboxes are flipped)
    st.subheader("👀 Cleaned Data Preview")
    st.dataframe(working_df.head(5))
    st.subheader("🎯 Engine Targets Detected")
    with st.expander("Click to see which columns the AI-cleaner targeted", expanded=True):
        # Re-run the finder logic visually for the user
        detected_dates = working_df(['date', 'time', 'created', 'signup'])
        detected_money = working_df(['revenue', 'amount', 'price', 'sales', 'cost', 'total'])
        detected_phones = working_df(['phone', 'tel', 'mobile', 'ph'])
        
        st.markdown(f"**📅 Date Columns Identified:** {', '.join(detected_dates) if detected_dates else 'None'}")
        st.markdown(f"**💰 Financial Columns Identified:** {', '.join(detected_money) if detected_money else 'None'}")
        st.markdown(f"**📞 Contact Columns Identified:** {', '.join(detected_phones) if detected_phones else 'None'}")

    # 6. CONVERT CLEAN DATA INTO LIVE DOWNLOAD STREAM
    output_buffer = io.BytesIO()
    working_df.to_csv(output_buffer, index=False)
    output_buffer.seek(0)


    # 7. DOWNLOAD BUTTON (Now works natively on click without dropping data)
    st.write("---")
    st.download_button(
        label="🚀 Download Cleaned Spreadsheet",
        data=output_buffer,
        file_name=f"cleaned_{st.session_state['file_name']}",
        mime="text/csv"
    )