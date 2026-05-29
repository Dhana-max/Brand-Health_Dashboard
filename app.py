# =========================================================
# PREMIUM BRAND HEALTH DASHBOARD
# =========================================================

import streamlit as st
import duckdb
import pandas as pd
import re
import plotly.express as px
from streamlit_option_menu import option_menu

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Brand Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# PREMIUM UI (FIXED)
# =========================================================

st.markdown("""
<style>

.stApp {
    background: #f4f7fb;
}

.block-container {
    padding-top: 1rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

section[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e2e8f0;
}

html, body, p, div, span, label {
    color: #111827 !important;
}

h1,h2,h3,h4,h5,h6 {
    color: #0f172a !important;
}

/* FILTERS */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: white !important;
    border: 1px solid #dbe4f0 !important;
    border-radius: 18px !important;
    min-height: 56px;
}

/* KPI CARDS */
.metric-card {
    background: white;
    border-radius: 24px;
    padding: 28px;
    border: 1px solid #e2e8f0;
}

.metric-header {
    display: flex;
    justify-content: space-between;
}

.metric-title {
    font-size: 14px;
    font-weight: 700;
    color: #64748b;
}

.metric-subtitle {
    font-size: 13px;
    color: #94a3b8;
}

.metric-badge {
    background: #2563eb;
    color: white;
    padding: 6px 12px;
    border-radius: 10px;
    font-weight: 700;
}

.metric-value {
    margin-top: 20px;
    font-size: 42px;
    font-weight: 800;
}

.metric-progress {
    height: 10px;
    background: #e2e8f0;
    border-radius: 10px;
    margin-top: 10px;
}

.metric-fill {
    height: 100%;
    background: linear-gradient(90deg,#8b5cf6,#3b82f6);
}

/* GRAPH CARD */
.graph-card {
    background: white;
    border-radius: 20px;
    padding: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE (FIXED)
# =========================================================

st.markdown("""
<h1 style='font-size:56px;font-weight:800;margin-bottom:0;'>
🚀 Brand Health Dashboard
</h1>

<p style='font-size:20px;color:#64748b;margin-top:0;'>
Interactive analytics platform for tracking brand performance
</p>
""", unsafe_allow_html=True)

# =========================================================
# FILES
# =========================================================

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# =========================================================
# CONNECTION
# =========================================================

@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

# =========================================================
# LOAD MAP
# =========================================================

@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# =========================================================
# BRAND MAP
# =========================================================

brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# =========================================================
# FUNCTIONS
# =========================================================

def build_where(months_sel, countries_sel, segment):
    filters = []

    if months_sel:
        filters.append("Month IN (" + ",".join(f"'{m}'" for m in months_sel) + ")")

    if countries_sel:
        filters.append("Country_New IN (" + ",".join(f"'{c}'" for c in countries_sel) + ")")

    if segment == "Male":
        filters.append("Sex = 1")
    elif segment == "Female":
        filters.append("Sex = 2")

    return "WHERE " + " AND ".join(filters) if filters else ""

def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0 / SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM({weight_col})
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

# =========================================================
# DASHBOARD
# =========================================================

countries = con.execute("SELECT DISTINCT Country_New FROM df").df()["Country_New"].tolist()
months = con.execute("SELECT DISTINCT Month FROM df").df()["Month"].tolist()

c1, c2, c3 = st.columns(3)

with c1:
    selected_countries = st.multiselect("Country", countries)

with c2:
    selected_months = st.multiselect("Month", months)

with c3:
    segment = st.selectbox("Segment", ["Total","Male","Female"])

brand = st.selectbox("Brand", list(brand_map.keys()))
code = brand_map[brand]

where = build_where(selected_months, selected_countries, segment)

# KPIs
awareness = get_metric(f"Aided_Awareness_{code}_slice","yesno",where)
favorability = get_metric(f"Brand_Favorability_{code}_slice","top2",where)
consideration = get_metric(f"Consideration_{code}_slice","top2",where)
effect = get_metric(f"Consideration_Effect_{code}_slice","top2",where)

st.markdown("<br>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

cards = [
    (c1, "Awareness", awareness),
    (c2, "Favorability", favorability),
    (c3, "Consideration", consideration),
    (c4, "Effect", effect)
]

for col, title, value in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <div>
                    <div class="metric-title">{title}</div>
                    <div class="metric-subtitle">KPI Score</div>
                </div>
                <div class="metric-badge">{value}</div>
            </div>
            <div class="metric-value">{value}%</div>
            <div class="metric-progress">
                <div class="metric-fill" style="width:{value}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# ATTRIBUTES
# =========================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown('<div class="graph-card">', unsafe_allow_html=True)

st.subheader("📊 Brand Attributes")

attr_data = []

for i in range(1, 18):
    val = get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice","top2",where)
    attr_data.append({"Attribute": i, "Value": val})

df_attr = pd.DataFrame(attr_data)

fig = px.bar(df_attr, x="Value", y="Attribute", orientation="h")

st.plotly_chart(fig, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
