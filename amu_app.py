import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

st.set_page_config(page_title="Average Monthly Usage", layout="wide", page_icon="🦷")

# --- HELPER: EXCEL DOWNLOADER ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

st.title("🦷 Average Monthly Usage (AMU) Engine")

# --- GLOBAL STORAGE ---
if 'usage_raw' not in st.session_state: st.session_state.usage_raw = pd.DataFrame()
if 'usage_filtered' not in st.session_state: st.session_state.usage_filtered = pd.DataFrame()
if 'amu_final' not in st.session_state: st.session_state.amu_final = pd.DataFrame()

# --- SEARCH BOX ---
search_query = st.sidebar.text_input("Search Item Name:", placeholder="e.g. Articaine")

# --- TAB STRUCTURE ---
t1a, t1b, t1c, t1d = st.tabs(["1.a Data Upload", "1.b Filtering", "1.c Consolidation", "1.d AMU Calc"])

# ---------------------------------------------------------
# 1.a DATA UPLOAD
# ---------------------------------------------------------
with t1a:
    st.subheader("1.a Upload Excel Sheets")
    files = st.file_uploader("Upload usage records", accept_multiple_files=True)
    if files:
        dfs = [pd.read_excel(f) for f in files]
        st.session_state.usage_raw = pd.concat(dfs, ignore_index=True)
        st.success(f"Merged {len(files)} files.")
        
        display_df = st.session_state.usage_raw
        if search_query:
            item_col = display_df.columns[8] # Column I
            display_df = display_df[display_df[item_col].astype(str).str.contains(search_query, case=False, na=False)]
        
        st.dataframe(display_df)
        st.download_button("📥 Download Merged Raw Data", data=to_excel(display_df), file_name="merged_raw_usage.xlsx")

# ---------------------------------------------------------
# 1.b DATA FILTERING
# ---------------------------------------------------------
with t1b:
    st.subheader("1.b Data Filtering (Columns C, F, I, K, M)")
    if not st.session_state.usage_raw.empty:
        cols = [2, 5, 8, 10, 12]
        filtered = st.session_state.usage_raw.iloc[:, cols].copy()
        filtered.columns = ['Amount', 'Price', 'inventoryItem', 'inventoryType', 'Created']
        
        if search_query:
            filtered = filtered[filtered['inventoryItem'].str.contains(search_query, case=False, na=False)]
        
        st.session_state.usage_filtered = filtered
        st.dataframe(filtered)
        st.download_button("📥 Download Filtered List", data=to_excel(filtered), file_name="filtered_usage.xlsx")

# ---------------------------------------------------------
# 1.c CONSOLIDATION
# ---------------------------------------------------------
with t1c:
    st.subheader("1.c Consolidation (Max Price & Oldest Date)")
    if not st.session_state.usage_filtered.empty:
        df = st.session_state.usage_filtered.copy()
        df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
        
        consolidated = df.groupby(['inventoryItem', 'inventoryType']).agg({
            'Amount': 'sum', 'Price': 'max', 'Created': 'min'
        }).reset_index()
        
        today = pd.to_datetime(datetime.now())
        consolidated['No. of Months'] = consolidated['Created'].apply(
            lambda x: max(1, round((today - x).days / 30, 2)) if pd.notnull(x) else 1
        )
        
        if search_query:
            consolidated = consolidated[consolidated['inventoryItem'].str.contains(search_query, case=False, na=False)]
            
        st.session_state.amu_final = consolidated
        st.dataframe(consolidated)
        st.download_button("📥 Download Consolidated Report", data=to_excel(consolidated), file_name="consolidated_usage.xlsx")

# ---------------------------------------------------------
# 1.d AMU CALCULATION
# ---------------------------------------------------------
with t1d:
    st.subheader("1.d Final AMU Results")
    if not st.session_state.amu_final.empty:
        df = st.session_state.amu_final.copy()
        df['AMU'] = (df['Amount'] / df['No. of Months']).round(2)
        
        st.dataframe(df[['inventoryItem', 'inventoryType', 'AMU', 'Price']])
        st.download_button("📥 Download Final AMU Calculation", data=to_excel(df), file_name="final_amu_results.xlsx")
