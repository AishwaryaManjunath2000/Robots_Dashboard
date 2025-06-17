import streamlit as st
import pandas as pd
import uuid
import os
from faq_generator import generate_faq_pdf

# --- Page config ---
st.set_page_config(page_title="Busy Teachers Guide to Robots", layout="wide")

# --- Load custom CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

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

# --- Price filter ---
price_col = pd.to_numeric(df_raw["Price"].str.replace("$", "", regex=False), errors='coerce')
min_price, max_price = int(price_col.min()), int(price_col.max())
price_range = st.sidebar.slider("Price Range", min_price, max_price, (min_price, max_price))

# --- Sort dropdown ---
col1, col2 = st.columns([8, 2])
with col2:
    sort_options = ["Price", "Name"]
    sort_by = st.selectbox("Sort By", sort_options, key="sort-top")

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
filtered = filtered.sort_values(by="_price" if sort_by == "Price" else "Name")

# --- Display Results ---
st.markdown(f"### Showing {len(filtered)} matching robots")
cols = st.columns(3)

for i, (_, row) in enumerate(filtered.iterrows()):
    with cols[i % 3]:
        name = row['Name']
        image_url = row.get("Image", "https://via.placeholder.com/300x300")
        clean_price = str(row.get('Price', 'N/A')).replace('$', '')

        st.markdown(f"""
        <div style="text-align: center;">
            <img src="{image_url}" alt="{name} image"
                 style="width: 100%; height: 250px; object-fit: cover; border-radius: 12px;">
            <h4 style="margin-top: 10px;">{name}</h4>
            <p><strong>${clean_price}</strong></p>
            <p>{row['Manufacturer']} | Grade: {row.get('Min Grade Level', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("▼ More Info"):
            st.markdown(f"""
                - Rechargeable: {row.get('Rechargeable', 'N/A')}
                - Batteries: {row.get('Batteries', 'N/A')}
                - Set Available: {row.get('Set Available', 'N/A')}
                - Max Users: {row.get('Max Users', 'N/A')}
                - Device Required: {row.get('Device Required', 'N/A')}
                - Visual Cues: {row.get('Visual Accessibility', 'N/A')}
                - [🔗 Buy Now]({row.get('Purchase Website', '#')})
            """)

        # ✅ Generate PDF and show download button
        if st.button("📄 Auto Glance", key=f"faq-btn-{i}"):
            unique_id = str(uuid.uuid4())
            safe_filename = f"{unique_id}_{name.replace(' ', '_')}_FAQ.pdf"
            filepath = os.path.join("static", safe_filename)
            os.makedirs("static", exist_ok=True)

            generate_faq_pdf(row, filename=filepath)

            with open(filepath, "rb") as f:
                pdf_data = f.read()
                st.download_button(
                    label="⬇️ Click to Download PDF",
                    data=pdf_data,
                    file_name=f"{name}_FAQ.pdf",
                    mime="application/pdf"
                )
