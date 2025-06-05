import streamlit as st
import pandas as pd

# --- Page config ---
st.set_page_config(page_title="Busy Teachers Guide to Robots", layout="wide")

# --- Load custom CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# --- Initialize session state for popup ---
if "show_popup" not in st.session_state:
    st.session_state["show_popup"] = False

# --- Title ---
st.title("📘 Busy Teachers Guide to Robots")

# --- Load data ---
sheet_url = "https://docs.google.com/spreadsheets/d/1I4r5mQm3Fwn39bKVYGHB3qXFn1sHNzmC/export?format=csv"
df_raw = pd.read_csv(sheet_url, skiprows=1)
df_raw.columns = df_raw.columns.str.strip()
df_raw = df_raw.dropna(subset=["Name", "Manufacturer"]).copy()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Options")
search = st.sidebar.text_input("Search name or manufacturer")

manufacturer_options = ["All"] + sorted(df_raw["Manufacturer"].dropna().unique())
selected_manufacturer = st.sidebar.selectbox("Manufacturer", manufacturer_options)

grade_levels = df_raw["Min Grade Level"].dropna().unique()
grade_levels = sorted(grade_levels, key=lambda x: ("0" if x == "PK" else "1" if x == "K" else x))
selected_grades = st.sidebar.multiselect("Min Grade Level", grade_levels)

rechargeable_choice = st.sidebar.selectbox("Rechargeable?", ["All", "Yes", "No"])
battery_filter = st.sidebar.selectbox("Needs Batteries?", ["All", "Yes", "No"])
availability_filter = st.sidebar.checkbox("Available at WWU's EduToyPia only")

# Price and Age filters
price_col = pd.to_numeric(df_raw["Price"].str.replace("$", "", regex=False), errors='coerce')
age_col = pd.to_numeric(df_raw["Min Age"], errors='coerce')

min_price, max_price = int(price_col.min()), int(price_col.max())
price_range = st.sidebar.slider("Price Range", min_price, max_price, (min_price, max_price))

min_age, max_age = int(age_col.min()), int(age_col.max())
age_range = st.sidebar.slider("Minimum Age", min_age, max_age, (min_age, max_age))

# Sort
sort_options = ["Price", "Min Age", "Name"]
sort_by = st.sidebar.selectbox("Sort By", sort_options)

# --- Filtering ---
filtered = df_raw.copy()
if search:
    filtered = filtered[
        filtered["Name"].str.contains(search, case=False, na=False) |
        filtered["Manufacturer"].str.contains(search, case=False, na=False)
    ]

if selected_manufacturer != "All":
    filtered = filtered[filtered["Manufacturer"] == selected_manufacturer]

if selected_grades:
    filtered = filtered[filtered["Min Grade Level"].isin(selected_grades)]

if rechargeable_choice != "All":
    filtered = filtered[filtered["Rechargeable"] == rechargeable_choice]

if battery_filter != "All":
    filtered = filtered[filtered["Batteries"] == battery_filter]

if availability_filter:
    filtered = filtered[filtered["Set Available"] == "Yes"]

filtered["_price"] = price_col
filtered = filtered[(filtered["_price"] >= price_range[0]) & (filtered["_price"] <= price_range[1])]

filtered["_age"] = age_col
filtered = filtered[(filtered["_age"] >= age_range[0]) & (filtered["_age"] <= age_range[1])]

# Sort
if sort_by == "Price":
    filtered = filtered.sort_values(by="_price")
elif sort_by == "Min Age":
    filtered = filtered.sort_values(by="_age")
else:
    filtered = filtered.sort_values(by="Name")

# --- Display Results ---
st.markdown(f"### Showing {len(filtered)} matching robots")
cols = st.columns(3)

# --- Card Loop ---
for i, (_, row) in enumerate(filtered.iterrows()):
    with cols[i % 3]:
        name = row['Name']
        image_url = row.get("Image", "https://via.placeholder.com/300x300")

        st.markdown(f"""
        <div class="robot-card" style="text-align: center;">
            <img src="{image_url}" alt="{name} image"
                 style="width: 100%; height: 250px; object-fit: cover; border-radius: 12px;">
            <h4 class="robot-title" style="margin-top: 10px;">{name}</h4>
            <p style="font-weight: 600; color: #444; margin: 0.2rem 0;">${row.get('Price', 'N/A')}</p>
            <p style="margin: 0.1rem 0; font-size: 0.9rem; color: #666;">{row['Manufacturer']}</p>
            <p style="margin: 0.1rem 0; font-size: 0.9rem; color: #666;">Grade: {row.get('Min Grade Level', 'N/A')} | Age: {row.get('Min Age', 'N/A')}</p>
        """, unsafe_allow_html=True)

        with st.expander("▼ More Info"):
            st.markdown(f"""
                <p style="font-size: 0.85rem;"><strong>Rechargeable:</strong> {row.get('Rechargeable', 'N/A')}</p>
                <p style="font-size: 0.85rem;"><strong>Batteries:</strong> {row.get('Batteries', 'N/A')}</p>
                <p style="font-size: 0.85rem;"><strong>Set Available:</strong> {row.get('Set Available', 'N/A')} ({row.get('Set size', 'N/A')})</p>
                <p style="font-size: 0.85rem;"><strong>Max Users:</strong> {row.get('Max Users', 'N/A')}</p>
                <p style="font-size: 0.85rem;"><strong>Device Required:</strong> {row.get('Device Required', 'N/A')}</p>
                <p style="font-size: 0.85rem;"><strong>Visual Cues:</strong> {row.get('Visual Accessibility', 'N/A')}</p>
                <p style="font-size: 0.85rem;"><a href="{row.get('Purchase Website', '#')}" target="_blank">🔗 Buy Now</a></p>
            """, unsafe_allow_html=True)

            if name == "Code-a-pillar Twist":
                if st.button("🔍 FAQ", key=f"popup-btn-{i}"):
                    st.session_state["show_popup"] = True

                if st.session_state["show_popup"]:
                    st.image("code-a-pillar.png", caption="Code-a-pillar", use_container_width=True)
                    if st.button("❌ Close Image", key=f"close-popup-{i}"):
                        st.session_state["show_popup"] = False

        st.markdown("</div>", unsafe_allow_html=True)
