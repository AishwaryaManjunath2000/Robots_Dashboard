import streamlit as st
import pandas as pd
import uuid
import os
from faq_generator import generate_faq_pdf

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "auto_glance_robot" not in st.session_state:
    st.session_state.auto_glance_robot = None  # dict with selected robot info


# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(page_title="Busy Teachers Guide to Robots", layout="wide")


# --------------------------------------------------
# Load custom CSS
# --------------------------------------------------
def local_css(file_name: str):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("style.css")


# --------------------------------------------------
# Helper: cost estimation for a class
# --------------------------------------------------
def estimate_cost_for_students(robot: dict, num_students: int):
    """Return a list of (label, cost_float) purchase options for this robot."""
    if not num_students or num_students <= 0:
        return []

    def parse_price(val):
        if val is None:
            return 0.0
        s = str(val).replace("$", "").strip()
        try:
            return float(s)
        except Exception:
            return 0.0

    price_single = parse_price(robot.get("Price"))
    price_set = parse_price(robot.get("Price per Set"))

    try:
        max_users = int(float(robot.get("Max Users", 0)))
    except Exception:
        max_users = 0

    options = []

    # Classroom set option
    if price_set > 0 and max_users > 0:
        sets_needed = (num_students + max_users - 1) // max_users
        total_cost_sets = sets_needed * price_set
        options.append((f"Using classroom sets ({sets_needed} set(s))", total_cost_sets))

    # Individual purchase option
    if price_single > 0:
        total_cost_individual = num_students * price_single
        options.append((f"Buying individually ({num_students} unit(s))", total_cost_individual))

    return options


# --------------------------------------------------
# Helper: detect Battery Type column robustly
# --------------------------------------------------
def detect_battery_column(df: pd.DataFrame) -> str | None:
    # 0) Super-explicit: look for something that *is* "Battery Type"
    normalized = {
        col.strip().lower()
        .replace("\u00a0", " ")      # non-breaking space → normal space
        .replace(" ", ""): col
        for col in df.columns
    }

    if "batterytype" in normalized:
        return normalized["batterytype"]

    # 1) More relaxed: any header containing both "battery" and "type"
    for col in df.columns:
        cl = col.lower()
        if "battery" in cl and "type" in cl:
            return col

    # 2) Last-chance fallback: look at values and guess
    allowed_keywords = {
        "aa",
        "aaa",
        "d",
        "c",
        "9v",
        "none",
        "no batteries",
        "rechargeable replaceable",
        "rechargeable permanent",
        "not known",
        "other",
    }

    for col in df.columns:
        s = df[col].dropna().astype(str).str.strip().str.lower()
        if s.empty:
            continue

        is_allowed = (
            s.isin(allowed_keywords)
            | s.str.contains("rechargeable", na=False)
            | s.str.contains("battery", na=False)
        )
        score = is_allowed.mean()

        if score >= 0.5:
            return col

    return None


# --------------------------------------------------
# Title
# --------------------------------------------------
st.title("📘 Busy Teachers Guide to Robots")


# --------------------------------------------------
# Load data
# --------------------------------------------------
sheet_url = (
    "https://docs.google.com/spreadsheets/d/1lNqg5TCFLQ8Viwi5E99m5lJqe8AHnkXy/"
    "export?format=csv&gid=1286409959"
)

df_raw = pd.read_csv(sheet_url, skiprows=1)
df_raw.columns = df_raw.columns.str.strip()
df_raw = df_raw.dropna(subset=["Name", "Manufacturer"]).copy()

# ---- Detect battery type column safely ----
battery_col_name = detect_battery_column(df_raw)

# Clean battery type column if present
if battery_col_name is not None:
    df_raw[battery_col_name] = (
        df_raw[battery_col_name]
        .astype(str)
        .str.strip()
        .replace({"": None, "nan": None, "NaN": None})
    )

# ---------- Optional numeric: space requirements (sq ft) ----------
space_range = None
if "Space Requirements (sq ft)" in df_raw.columns:
    space_series = pd.to_numeric(
        df_raw["Space Requirements (sq ft)"], errors="coerce"
    )
    if space_series.notna().any():
        df_raw["_space_sqft"] = space_series
    else:
        df_raw["_space_sqft"] = pd.NA
else:
    df_raw["_space_sqft"] = pd.NA

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("🔍 Filter Options")
search = st.sidebar.text_input("Search name or manufacturer")

# Manufacturer
manufacturer_options = ["All"] + sorted(df_raw["Manufacturer"].dropna().unique())
selected_manufacturer = st.sidebar.selectbox("Manufacturer", manufacturer_options)

# Grade level
grade_levels = df_raw["Min Grade Level"].dropna().unique()
grade_levels = sorted(
    grade_levels,
    key=lambda x: ("0" if x == "PK" else "1" if x == "K" else x),
)
selected_grades = st.sidebar.multiselect("Min Grade Level", grade_levels)

# Rechargeable
rechargeable_choice = st.sidebar.selectbox("Rechargeable?", ["All", "Yes", "No"])

# Needs batteries? (based on "Batteries" column)
needs_batteries_filter = st.sidebar.selectbox(
    "Needs batteries?",
    ["All", "Yes", "No"],
)

# Battery type (values come from detected battery column)
if battery_col_name is not None:
    battery_type_raw = (
        df_raw[battery_col_name]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    battery_type_values = sorted(
        t for t in battery_type_raw.unique()
        if t not in ("", "nan", "NaN", None)
    )
else:
    battery_type_values = []

selected_battery_types = st.sidebar.multiselect(
    "Battery type",
    options=battery_type_values,
)

# Debug caption so you can see what it picked
st.sidebar.caption(
    f"Battery column detected: {battery_col_name or '❌ not found – please confirm header says “Battery Type”'}"
)

# ---------- NEW: Accessibility filters ----------
auditory_filter = "All"
visual_filter = "All"
fine_motor_filter = "All"

if "Auditory Accessibility" in df_raw.columns:
    auditory_filter = st.sidebar.selectbox(
        "Auditory accessibility",
        ["All", "Yes", "No"],
        help="Filter by the Auditory Accessibility column.",
    )

if "Visual Accessibility" in df_raw.columns:
    visual_filter = st.sidebar.selectbox(
        "Visual accessibility",
        ["All", "Yes", "No"],
        help="Filter by the Visual Accessibility column.",
    )

if "Fine Motor Accessibility" in df_raw.columns:
    fine_motor_filter = st.sidebar.selectbox(
        "Fine motor accessibility",
        ["All", "Yes", "No"],
        help="Filter by the Fine Motor Accessibility column.",
    )
# -----------------------------------------------

# ---------- NEW: Screen-free + device + internet filters ----------
screen_free_choice = st.sidebar.selectbox(
    "Screen-free mode",
    ["All", "Screen-free only", "Devices only"],
    help="Filter robots that can be used screen-free, or those that require a device.",
)

DEVICE_COLUMN_MAP = {
    "iPad / tablet (iOS)": "iPad",
    "Android tablet / phone": "Android",
    "Windows laptop / PC": "PC",
    "Mac laptop / desktop": "Mac",
}

selected_devices = st.sidebar.multiselect(
    "Devices required (any of these)",
    options=list(DEVICE_COLUMN_MAP.keys()),
    help="Leave empty to include all robots regardless of device type.",
)

internet_choice = st.sidebar.selectbox(
    "Internet use",
    ["All", "Required", "Not used", "Optional"],
    help="Based on the Internet column in the grid.",
)
# ------------------------------------------------------------------

# ---------- Optional: space + consumables filters ----------
if df_raw["_space_sqft"].notna().any():
    space_min = int(df_raw["_space_sqft"].min())
    space_max = int(df_raw["_space_sqft"].max())
    space_range = st.sidebar.slider(
        "Space requirements (sq ft)",
        min_value=space_min,
        max_value=space_max,
        value=(space_min, space_max),
        help="Filter robots by approximate floor space required.",
    )

consumables_filter = None
if "Consumables Required" in df_raw.columns:
    consumables_filter = st.sidebar.selectbox(
        "Consumables required?",
        ["All", "Yes", "No"],
        help="Will be used once this column is populated in the grid.",
    )
# ------------------------------------------------------------------

# Only WWU sets
availability_filter = st.sidebar.checkbox("Available at WWU's EduToyPia only")

# Number of students for cost estimation
num_students = st.sidebar.number_input(
    "Number of students (optional)",
    min_value=0,
    step=1,
    value=0,
    help="Enter a class size to estimate total cost for this robot",
)

# --------------------------------------------------
# Price filter
# --------------------------------------------------
price_col = pd.to_numeric(
    df_raw["Price"].str.replace("$", "", regex=False),
    errors="coerce",
)
df_raw["_price"] = price_col
min_price, max_price = int(price_col.min()), int(price_col.max())
price_range = st.sidebar.slider(
    "Price Range",
    min_price,
    max_price,
    (min_price, max_price),
)

# Sort dropdown
col1, col2 = st.columns([8, 2])
with col2:
    sort_options = ["Price", "Name"]
    sort_by = st.selectbox("Sort By", sort_options, key="sort-top")

# --------------------------------------------------
# Apply filters
# --------------------------------------------------
filtered = df_raw.copy()

# Search name/manufacturer
if search:
    filtered = filtered[
        filtered["Name"].str.contains(search, case=False, na=False)
        | filtered["Manufacturer"].str.contains(search, case=False, na=False)
    ]

# Manufacturer filter
if selected_manufacturer != "All":
    filtered = filtered[filtered["Manufacturer"] == selected_manufacturer]

# Grade filter
if selected_grades:
    filtered = filtered[filtered["Min Grade Level"].isin(selected_grades)]

# Rechargeable filter
if rechargeable_choice != "All":
    filtered = filtered[filtered["Rechargeable"] == rechargeable_choice]

# Needs batteries filter
if needs_batteries_filter == "Yes":
    filtered = filtered[
        filtered["Batteries"]
        .astype(str)
        .str.strip()
        .str.lower()
        .ne("no")
        & filtered["Batteries"].notna()
    ]
elif needs_batteries_filter == "No":
    filtered = filtered[
        filtered["Batteries"].isna()
        | filtered["Batteries"].astype(str).str.strip().str.lower().eq("no")
    ]

# Battery type filter (only if we found the column)
if selected_battery_types and battery_col_name is not None:
    filtered = filtered[
        filtered[battery_col_name]
        .fillna("")
        .astype(str)
        .str.strip()
        .isin(selected_battery_types)
    ]

# ---------- Accessibility filters ----------
if auditory_filter != "All" and "Auditory Accessibility" in filtered.columns:
    filtered = filtered[filtered["Auditory Accessibility"] == auditory_filter]

if visual_filter != "All" and "Visual Accessibility" in filtered.columns:
    filtered = filtered[filtered["Visual Accessibility"] == visual_filter]

if fine_motor_filter != "All" and "Fine Motor Accessibility" in filtered.columns:
    filtered = filtered[filtered["Fine Motor Accessibility"] == fine_motor_filter]
# ------------------------------------------

# ---------- Screen-free, device, internet ----------
if screen_free_choice != "All" and "ScreenFree" in filtered.columns:
    sf = filtered["ScreenFree"].astype(str).str.strip().str.lower()
    if screen_free_choice == "Screen-free only":
        filtered = filtered[sf.eq("yes")]
    elif screen_free_choice == "Devices only":
        filtered = filtered[~sf.eq("yes")]

if selected_devices:
    device_cols = [DEVICE_COLUMN_MAP[label] for label in selected_devices]
    mask = None
    for col in device_cols:
        if col in filtered.columns:
            col_mask = (
                filtered[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("yes")
            )
            mask = col_mask if mask is None else (mask | col_mask)
    if mask is not None:
        filtered = filtered[mask]

if internet_choice != "All" and "Internet" in filtered.columns:
    inet = filtered["Internet"].astype(str).str.strip().str.lower()
    if internet_choice == "Required":
        filtered = filtered[inet.isin(["yes", "required"])]
    elif internet_choice == "Not used":
        filtered = filtered[inet.isin(["no", "not used", "none", ""])]
    elif internet_choice == "Optional":
        filtered = filtered[inet.isin(["optional", "maybe"])]
# -------------------------------------------------

# ---------- Space + consumables ----------
if space_range is not None and "_space_sqft" in filtered.columns:
    filtered = filtered[
        filtered["_space_sqft"].notna()
        & (filtered["_space_sqft"] >= space_range[0])
        & (filtered["_space_sqft"] <= space_range[1])
    ]

if consumables_filter and consumables_filter != "All" and "Consumables Required" in filtered.columns:
    filtered = filtered[filtered["Consumables Required"] == consumables_filter]
# --------------------------------------------------

# Only WWU sets
if availability_filter:
    filtered = filtered[filtered["Set Available"] == "Yes"]

# Price range + sort
filtered["_price"] = pd.to_numeric(
    filtered["Price"].str.replace("$", "", regex=False),
    errors="coerce",
)
filtered = filtered[
    (filtered["_price"] >= price_range[0]) & (filtered["_price"] <= price_range[1])
]
filtered = filtered.sort_values(by="_price" if sort_by == "Price" else "Name")

# --------------------------------------------------
# MODE 1: Auto Glance full-page view
# --------------------------------------------------
if st.session_state.auto_glance_robot is not None:
    robot = st.session_state.auto_glance_robot
    name = robot.get("Name", "Robot")

    st.markdown(f"### 📄 Auto Glance — {name}")

    col_img, col_summary = st.columns([1, 2])

    image_url = robot.get("Image", "")
    if isinstance(image_url, str) and image_url.strip():
        with col_img:
            st.image(image_url, use_container_width=True)
    else:
        with col_img:
            st.info("No image available")

    with col_summary:
        st.subheader("Product Summary")
        summary = robot.get("Description", "No summary available.")
        st.write(summary)

    st.markdown("---")

    # Battery type value
    bt_value = (
        robot.get(battery_col_name, "N/A")
        if battery_col_name is not None
        else "N/A"
    )

    # Power & batteries
    power_rows = [
        ["Rechargeable", robot.get("Rechargeable", "N/A")],
        ["Needs Batteries", robot.get("Batteries", "N/A")],
        ["Battery Type", bt_value],
    ]
    power_df = pd.DataFrame(power_rows, columns=["Attribute", "Value"])
    st.subheader("Power & Batteries")
    st.table(power_df.astype(str))

    # Accessibility table
    comp_df = pd.DataFrame(
        [
            ["Device Required", robot.get("Device Required", "N/A")],
            ["Visual Cues", robot.get("Visual Accessibility", "N/A")],
            [
                "Auditory Cues",
                robot.get(
                    "Does the device rely on AUDITORY cues for interations and functionality?",
                    "N/A",
                ),
            ],
        ],
        columns=["Attribute", "Value"],
    )
    st.subheader("Accessibility & Interaction")
    st.table(comp_df.astype(str))

    # Usage
    age_df = pd.DataFrame(
        [
            ["Min Grade Level", robot.get("Min Grade Level", "N/A")],
            ["Max Users", robot.get("Max Users", "N/A")],
        ],
        columns=["Attribute", "Value"],
    )
    st.subheader("Usage")
    st.table(age_df.astype(str))

    # Price table
    price_df = pd.DataFrame(
        [
            ["Single Unit", robot.get("Price", "N/A")],
            ["Classroom Set", robot.get("Price per Set", "N/A")],
        ],
        columns=["Type", "Price"],
    )
    st.subheader("Price")
    st.table(price_df.astype(str))

    # Cost estimator
    if num_students and num_students > 0:
        options = estimate_cost_for_students(robot, num_students)
        if options:
            st.markdown(f"#### Estimated cost for **{num_students}** students")
            best_label, best_cost = min(options, key=lambda x: x[1])
            for label, cost in options:
                prefix = "✅ " if (label, cost) == (best_label, best_cost) else "• "
                st.markdown(f"{prefix}{label}: **${cost:,.2f}**")
        else:
            st.info(
                "Price data is incomplete for estimating total cost "
                f"for {num_students} students."
            )

    # Purchase link
    link = robot.get("Purchase Website", "")
    if isinstance(link, str) and link.strip():
        st.markdown(f"**More Info / Buy:** [{link}]({link})")

    st.markdown("### ")
    if st.button("⬇️ Download this Auto Glance as PDF"):
        unique_id = str(uuid.uuid4())
        safe_name = "".join(
            ch if ch.isalnum() or ch in " _-" else "_" for ch in name
        )
        safe_filename = f"{unique_id}_{safe_name.replace(' ', '_')}_FAQ.pdf"

        os.makedirs("static", exist_ok=True)
        filepath = os.path.join("static", safe_filename)

        row_series = pd.Series(robot)
        generate_faq_pdf(row_series, filename=filepath)

        with open(filepath, "rb") as f:
            pdf_data = f.read()

        st.download_button(
            label="📄 Click to Download PDF",
            data=pdf_data,
            file_name=f"{name}_AutoGlance.pdf",
            mime="application/pdf",
        )

    if st.button("⬅ Back to robots list"):
        st.session_state.auto_glance_robot = None
        st.rerun()

    st.stop()  # don’t render the grid when in detail mode


# --------------------------------------------------
# MODE 2: Normal grid of robot cards
# --------------------------------------------------
st.markdown(f"### Showing {len(filtered)} matching robots")
cols = st.columns(3)

for i, (_, row) in enumerate(filtered.iterrows()):
    with cols[i % 3]:
        name = row["Name"]
        image_url = row.get("Image", "")
        clean_price_raw = row.get("Price", "N/A")
        clean_price = str(clean_price_raw).replace("$", "")

        # Card image or placeholder
        if isinstance(image_url, str) and image_url.strip().lower() not in ["", "nan"]:
            img_block = f"<img src='{image_url}' alt='{name} image' />"
        else:
            img_block = "<div class='robot-img-placeholder'>Image not available</div>"

        card_html = f"""
        <div class="robot-card">
            <div class="robot-card-img">
                {img_block}
            </div>
            <h4 class="robot-title">{name}</h4>
            <p><strong>${clean_price}</strong></p>
            <p>{row['Manufacturer']} | Grade: {row.get('Min Grade Level', 'N/A')}</p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        # Battery type value
        bt_value = (
            row.get(battery_col_name, "N/A")
            if battery_col_name is not None
            else "N/A"
        )

        # More info
        with st.expander("▼ More Info"):
            st.markdown(
                f"""
                - Rechargeable: {row.get('Rechargeable', 'N/A')}
                - Needs Batteries: {row.get('Batteries', 'N/A')}
                - Battery Type: {bt_value}
                - Set Available: {row.get('Set Available', 'N/A')}
                - Max Users: {row.get('Max Users', 'N/A')}
                - Device Required: {row.get('Device Required', 'N/A')}
                - Visual Accessibility: {row.get('Visual Accessibility', 'N/A')}
                - Auditory Accessibility: {row.get('Auditory Accessibility', 'N/A')}
                - Fine Motor Accessibility: {row.get('Fine Motor Accessibility', 'N/A')}
                - Internet: {row.get('Internet', 'N/A')}
                - Screen-free mode: {row.get('ScreenFree', 'N/A')}
                - [🔗 Buy Now]({row.get('Purchase Website', '#')})
                """
            )

        # Auto Glance button → open full-page view
        if st.button("📄 Auto Glance", key=f"faq-btn-{i}"):
            st.session_state.auto_glance_robot = row.to_dict()
            st.rerun()
