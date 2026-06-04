import streamlit as st
import pandas as pd
import io

# 1. Page Frame Setup
st.set_page_config(page_title="Universal Sheet Cleaner", page_icon="🧼")

# Premium access check
query_params = st.query_params
premium_unlocked = query_params.get("unlocked") == "true"

st.title("🧼 Universal Spreadsheet Data Cleaner")

if premium_unlocked:
    st.success("✨ Premium Session Active")
else:
    st.info("🔒 This is a read-only sandbox demo.")

st.write(
    "Upload your data once. Your file will remain safely cached in system memory while you modify formatting options."
)

# 2. FILE UPLOAD INTERFACE
uploaded_file = st.file_uploader(
    "Upload your messy spreadsheet here",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    if "raw_df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
        if uploaded_file.name.endswith(".csv"):
            st.session_state["raw_df"] = pd.read_csv(uploaded_file)
        else:
            st.session_state["raw_df"] = pd.read_excel(uploaded_file)

        st.session_state["file_name"] = uploaded_file.name

    working_df = st.session_state["raw_df"].copy()

    st.sidebar.header("🛠️ Cleaning Options")

    remove_dup = st.sidebar.checkbox("Delete Duplicate Rows", value=True)
    drop_empty = st.sidebar.checkbox("Drop Completely Empty Rows", value=True)

    # Premium-only options
    if premium_unlocked:
        clean_contacts = st.sidebar.checkbox(
            "Clean Contact Info (Names, Emails, Phones)",
            value=True
        )
        fix_dates_money = st.sidebar.checkbox(
            "Standardize Dates & Repair Financial Data",
            value=True
        )
    else:
        clean_contacts = False
        fix_dates_money = False

    # Basic cleaning
    if drop_empty:
        working_df = working_df.dropna(how="all")

    if remove_dup:
        working_df = working_df.drop_duplicates()

    # Premium cleaning
    if clean_contacts:
        if "Name" in working_df.columns:
            working_df["Name"] = (
                working_df["Name"]
                .astype(str)
                .str.strip()
                .str.title()
                .replace("Null", None)
            )

        if "Email" in working_df.columns:
            working_df["Email"] = (
                working_df["Email"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

        if "Phone" in working_df.columns:
            working_df["Phone"] = (
                working_df["Phone"]
                .astype(str)
                .str.replace(r"\D", "", regex=True)
            )
            working_df["Phone"] = working_df["Phone"].replace("", "MISSING")

    if fix_dates_money:
        if "Signup Date" in working_df.columns:
            working_df["Signup Date"] = (
                pd.to_datetime(
                    working_df["Signup Date"],
                    errors="coerce"
                )
                .dt.strftime("%Y-%m-%d")
            )

        if "Revenue" in working_df.columns:
            working_df["Revenue"] = (
                working_df["Revenue"]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
            )

            working_df["Revenue"] = (
                pd.to_numeric(
                    working_df["Revenue"],
                    errors="coerce"
                )
                .fillna(0.0)
            )

    st.subheader("👀 Cleaned Data Preview")
    st.dataframe(working_df.head(5))

    output_buffer = io.BytesIO()
    working_df.to_csv(output_buffer, index=False)
    output_buffer.seek(0)

    st.write("---")

    if premium_unlocked:
        st.download_button(
            label="🚀 Download Cleaned Spreadsheet",
            data=output_buffer,
            file_name=f"cleaned_{st.session_state['file_name']}",
            mime="text/csv"
        )
    else:
        st.warning(
            "Download is disabled in sandbox mode. Add ?unlocked=true to enable premium features."
        )