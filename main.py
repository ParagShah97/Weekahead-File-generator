import io
import streamlit as st
from datetime import datetime
from script_based_generation import _build_bytes_for_year
from util.ai_worker3 import controller

st.set_page_config(page_title="FY Text Generator", layout="centered")

st.title("Financial Year TXT Generator")

# Dropdown: 2024 → 2030
years = list(range(2024, 2031))
selected_year = st.selectbox("Select Financial Year", years, index=0)

# Submit
if st.button("Submit"):
    file_bytes = _build_bytes_for_year(selected_year)
    filename = f"financial_year_{selected_year}.txt"
    st.success(f"Generated file for FY {selected_year}.")
    st.download_button(
        label="Download TXT",
        data=file_bytes,
        file_name=filename,
        mime="text/plain",
    )
    
if st.button("Submit to AI"):
    file_bytes = controller(selected_year)
    filename = f"financial_year_{selected_year}_AI_Gen.txt"
    st.success(f"Generated file for FY {selected_year}.")
    st.download_button(
        label="Download TXT",
        data=file_bytes,
        file_name=filename,
        mime="text/plain",
    )

