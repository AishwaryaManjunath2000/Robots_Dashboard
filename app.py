import streamlit as st
import pandas as pd

st.set_page_config(page_title="Busy Teachers Guide to Robots", layout="wide")
st.title("📘 Busy Teachers Guide to Robots")

# --- Load data ---
sheet_url = "https://docs.google.com/spreadsheets/d/1I4r5mQm3Fwn39bKVYGHB3qXFn1sHNzmC/export?format=csv"
df_raw = pd.read_csv(sheet_url, skiprows=1)
df_raw.columns = df_raw.columns.str.strip()

# Validate required columns
required_cols = ["Name", "Manufacturer"]
missing_cols = [col for col in required_cols if col not in df_raw.columns]
if missing_cols:
    st.error(f"❌ Sheet missing required columns: {missing_cols}")
    st.stop()

# Drop rows with missing required fields
df_raw = df_raw.dropna(subset=["Name", "Manufacturer"]).copy()

# Normalize grades for sorting
def grade_sort_key(grade):
    if grade == "PK": return -2
    if grade == "K": return -1
    try:
        return int(grade)
    except:
        return 100  # unknowns at end

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
search = st.sidebar.text_input("Search name or manufacturer")

manufacturers = sorted(df_raw["Manufacturer"].dropna().unique())
manufacturer_filter = st.sidebar.selectbox("Manufacturer", ["All"] + manufacturers)

grades = sorted(df_raw["Min Grade Level"].dropna().unique(), key=grade_sort_key)
grade_filter = st.sidebar.multiselect("Min Grade Level", grades)

rechargeable_filter = st.sidebar.radio("Rechargeable?", ["Yes", "No"])

availability_filter = st.sidebar.checkbox("Available at WWU's EduToyPia only", value=False)

# Convert Price and Min Age for sliders
df_raw["Price"] = pd.to_numeric(df_raw["Price"].replace("\$", "", regex=True), errors="coerce")
df_raw["Min Age"] = pd.to_numeric(df_raw["Min Age"], errors="coerce")

min_price, max_price = int(df_raw["Price"].min()), int(df_raw["Price"].max())
price_range = st.sidebar.slider("Price Range", min_price, max_price, (min_price, max_price))

min_age, max_age = int(df_raw["Min Age"].min()), int(df_raw["Min Age"].max())
age_range = st.sidebar.slider("Minimum Age", min_age, max_age, (min_age, max_age))

sort_by = st.sidebar.selectbox("Sort By", ["Price", "Min Age", "Name"])

# Filter logic
filtered = df_raw.copy()

if search:
    filtered = filtered[filtered["Name"].str.contains(search, case=False, na=False) |
                        filtered["Manufacturer"].str.contains(search, case=False, na=False)]

if manufacturer_filter != "All":
    filtered = filtered[filtered["Manufacturer"] == manufacturer_filter]

if grade_filter:
    filtered = filtered[filtered["Min Grade Level"].isin(grade_filter)]

filtered = filtered[filtered["Rechargeable"] == rechargeable_filter]

if availability_filter:
    filtered = filtered[filtered["Set Available"] == "Yes"]

filtered = filtered[(filtered["Price"] >= price_range[0]) & (filtered["Price"] <= price_range[1])]
filtered = filtered[(filtered["Min Age"] >= age_range[0]) & (filtered["Min Age"] <= age_range[1])]

# Sorting
if sort_by == "Min Age":
    filtered = filtered.sort_values(by="Min Age")
elif sort_by == "Price":
    filtered = filtered.sort_values(by="Price")
else:
    filtered = filtered.sort_values(by="Name")

st.markdown(f"### Showing {len(filtered)} matching robots")

cols = st.columns(2)

for i, (_, row) in enumerate(filtered.iterrows()):
    with cols[i % 2]:
        with st.container():
            st.markdown("""
                <div style="border:1px solid #ccc; padding:1rem; border-radius:8px; margin-bottom:1rem; background-color: #f9f9f9">
                    <h4>{}</h4>
                    <p><strong>Manufacturer:</strong> {}</p>
                    <p><strong>Price:</strong> ${}</p>
                    <p><strong>Min Grade:</strong> {} | <strong>Age:</strong> {}</p>
                    <p><strong>Rechargeable:</strong> {}</p>
                </div>
            """.format(
                row["Name"],
                row["Manufacturer"],
                row.get("Price", "N/A"),
                row.get("Min Grade Level", "N/A"),
                row.get("Min Age", "N/A"),
                row.get("Rechargeable", "N/A")
            ), unsafe_allow_html=True)

            with st.expander("📘 More Details"):
                st.write(f"**Set Available:** {row.get('Set Available', 'N/A')} ({row.get('Set size', 'N/A')})")
                st.write(f"**Max Users:** {row.get('Max Users', 'N/A')}")
                st.write(f"**Auditory Cues:** {row.get('Auditory Accessibility', 'N/A')}")
                st.write(f"**Visual Cues:** {row.get('Visual Accessibility', 'N/A')}")
                st.write(f"**Device Required:** {row.get('Device Required', 'N/A')}")
                st.write(f"**Description:** {row.get('Description', 'N/A')}")
                st.markdown(f"[🔗 Purchase Link]({row.get('Purchase Website', '#')})")
                st.markdown(f"[🏭 Manufacturer]({row.get('Manfacturer Website', '#')})")