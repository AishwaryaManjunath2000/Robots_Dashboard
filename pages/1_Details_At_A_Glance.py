import streamlit as st
import pandas as pd

st.set_page_config(page_title="Details At-A-Glance", layout="wide")
st.title("🔍 Details At-a-Glance: Busy Teachers' Guide to Robots")

# --- Navigation Buttons ---
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")  # go back to main page

# --- Load data ---
sheet_url = "https://docs.google.com/spreadsheets/d/1I4r5mQm3Fwn39bKVYGHB3qXFn1sHNzmC/export?format=csv"
df_raw = pd.read_csv(sheet_url, skiprows=1)
df_raw.columns = df_raw.columns.str.strip()
df_raw = df_raw.dropna(subset=["Name", "Manufacturer"]).copy()

# --- Clean Price column
df_raw["Price"] = df_raw["Price"].str.replace("$", "", regex=False)
df_raw["Price"] = pd.to_numeric(df_raw["Price"], errors='coerce')

# --- Columns to show
cols_to_show = [
    "Name", "Manufacturer", "Price", "Min Grade Level", "Rechargeable",
    "Batteries", "Set Available", "Max Users", "Device Required"
]

# --- Search/filter
search = st.text_input("Search by name or manufacturer:")
if search:
    df_filtered = df_raw[
        df_raw["Name"].str.contains(search, case=False, na=False) |
        df_raw["Manufacturer"].str.contains(search, case=False, na=False)
    ]
else:
    df_filtered = df_raw

# --- Format Price again for display
df_filtered["Price"] = df_filtered["Price"].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")

# --- Show Table
st.dataframe(
    df_filtered[cols_to_show].sort_values(by="Price", na_position="last").reset_index(drop=True),
    use_container_width=True
)
