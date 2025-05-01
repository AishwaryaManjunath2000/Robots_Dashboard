import streamlit as st
import pandas as pd

st.set_page_config(page_title="Robots Dashboard", layout="wide")
st.title("🤖 CS Educational Robots Dashboard ")

# --- Load data ---
sheet_url = "https://docs.google.com/spreadsheets/d/1I4r5mQm3Fwn39bKVYGHB3qXFn1sHNzmC/export?format=csv"

# The actual headers are on the second row (row 2), so skip row 1
df_raw = pd.read_csv(sheet_url, skiprows=1)

# Clean column names
df_raw.columns = df_raw.columns.str.strip()

# Validate columns
if "Name" not in df_raw.columns or "Manufacturer" not in df_raw.columns:
    st.error("❌ Sheet missing required columns: 'Name' and 'Manufacturer'")
    st.stop()

# Drop rows with missing name or manufacturer
df_raw = df_raw.dropna(subset=["Name", "Manufacturer"]).copy()

# Sidebar filters
st.sidebar.header("🔍 Filter")
search = st.sidebar.text_input("Search name or manufacturer")

grade_options = df_raw["Min Grade Level"].dropna().unique()
grade_filter = st.sidebar.multiselect("Min Grade Level", sorted(grade_options))

rechargeable_filter = st.sidebar.selectbox("Rechargeable?", ["All", "Yes", "No"])

# Filter logic
filtered = df_raw.copy()

if search:
    filtered = filtered[
        filtered["Name"].str.contains(search, case=False, na=False) |
        filtered["Manufacturer"].str.contains(search, case=False, na=False)
    ]

if grade_filter:
    filtered = filtered[filtered["Min Grade Level"].isin(grade_filter)]

if rechargeable_filter != "All":
    filtered = filtered[filtered["Rechargeable"] == rechargeable_filter]

st.markdown(f"### Showing {len(filtered)} robots")

# Layout for cards
cols = st.columns(2)

for i, (_, row) in enumerate(filtered.iterrows()):
    with cols[i % 2]:
        with st.container():
            st.subheader(row["Name"])
            st.write(f"**Manufacturer:** {row['Manufacturer']}")
            st.write(f"**Price:** {row.get('Price', 'N/A')}")
            st.write(f"**Min Grade:** {row.get('Min Grade Level', 'N/A')} | **Age:** {row.get('Min Age', 'N/A')}")
            st.write(f"**Rechargeable:** {row.get('Rechargeable', 'N/A')}")

            with st.expander("📖 More Details"):
                st.write(f"**Set Available:** {row.get('Set Available', 'N/A')} ({row.get('Set size', 'N/A')})")
                st.write(f"**Max Users:** {row.get('Max Users', 'N/A')}")
                st.write(f"**Auditory Cues:** {row.get('Auditory Accessibility', 'N/A')}")
                st.write(f"**Visual Cues:** {row.get('Visual Accessibility', 'N/A')}")
                st.write(f"**Device Required:** {row.get('Device Required', 'N/A')}")
                st.write(f"**Description:** {row.get('Description', 'N/A')}")
                st.markdown(f"[🔗 Purchase Link]({row.get('Purchase Website', '#')})")
                st.markdown(f"[🏭 Manufacturer]({row.get('Manfacturer Website', '#')})")
