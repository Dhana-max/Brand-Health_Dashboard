import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(layout="wide")
st.title("Brand Health Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# -----------------------------
# DUCKDB CONNECTION
# -----------------------------
@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

# -----------------------------
# LOAD MAP FILE
# -----------------------------
@st.cache_data
def load_map():
    map_df = pd.read_excel(MAP_FILE, header=1)
    map_df.columns = map_df.columns.astype(str).str.strip()
    return map_df

map_df = load_map()

# -----------------------------
# LOAD FILTER VALUES
# -----------------------------
@st.cache_data
def load_filters():
    temp = con.execute("""
        SELECT DISTINCT Month, Country_New FROM df
    """).df()

    return (
        sorted(temp["Month"].dropna().unique()),
        sorted(temp["Country_New"].dropna().unique())
    )

months, countries = load_filters()

# -----------------------------
# BRAND MAP
# -----------------------------
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {}

for _, r in brand_rows.iterrows():
    code = int(re.findall(r"\d+", str(r["Variable"]))[0])
    name = str(r["Label"]).split(" - ")[-1].strip()
    brand_map[name] = code

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filters")

selected_brand = st.sidebar.selectbox("Brand", sorted(brand_map.keys()))
selected_months = st.sidebar.multiselect("Month", months)
selected_countries = st.sidebar.multiselect("Country", countries)
segment = st.sidebar.selectbox("Segment", ["Total", "Male", "Female"])

code = brand_map[selected_brand]

# -----------------------------
# FILTER CONDITIONS
# -----------------------------
filters = []

if selected_months:
    filters.append("Month IN ({})".format(",".join([f"'{m}'" for m in selected_months])))

if selected_countries:
    filters.append("Country_New IN ({})".format(",".join([f"'{c}'" for c in selected_countries])))

if segment == "Male":
    filters.append("Sex = 1")
elif segment == "Female":
    filters.append("Sex = 2")

where_clause = " AND ".join(filters)
if where_clause:
    where_clause = "WHERE " + where_clause

# -----------------------------
# WEIGHT COLUMN
# -----------------------------
weight_col = (
    "Weight_Post"
    if selected_countries and len(selected_countries) == 1
    else "Global_weight_Stacked"
)

# -----------------------------
# KPI COLUMN NAMES
# -----------------------------
awareness_col = f"Aided_Awareness_{code}_slice"
favorability_col = f"Brand_Favorability_{code}_slice"
consideration_col = f"Consideration_{code}_slice"
effect_col = f"Consideration_Effect_{code}_slice"

# -----------------------------
# KPI FUNCTION
# -----------------------------
def get_top2_metric(col):
    query = f"""
    SELECT 
        SUM(
            CASE 
                WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
                THEN {weight_col} ELSE 0 
            END
        ),
        SUM(
            CASE 
                WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
                THEN {weight_col} ELSE 0 
            END
        )
    FROM df
    {where_clause}
    """
    num, den = con.execute(query).fetchone()
    return round((num / den) * 100, 1) if den else 0

# -----------------------------
# AWARENESS
# -----------------------------
query_awareness = f"""
SELECT 
    SUM(CASE WHEN LOWER(TRIM({awareness_col}))='yes' THEN {weight_col} ELSE 0 END),
    SUM(CASE WHEN {awareness_col} IS NOT NULL THEN {weight_col} ELSE 0 END)
FROM df
{where_clause}
"""

yes_wt, total_wt = con.execute(query_awareness).fetchone()
awareness = round((yes_wt / total_wt) * 100, 1) if total_wt else 0

# -----------------------------
# KPI METRICS
# -----------------------------
favorability = get_top2_metric(favorability_col)
consideration = get_top2_metric(consideration_col)
consideration_effect = get_top2_metric(effect_col)

# -----------------------------
# ✅ TABS ADDED HERE
# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

# =============================
# DASHBOARD TAB (UNCHANGED)
# =============================
with tab1:

    st.subheader("Key Metrics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Awareness", f"{awareness}%")
    c2.metric("Favorability", f"{favorability}%")
    c3.metric("Consideration", f"{consideration}%")
    c4.metric("Consideration Effect", f"{consideration_effect}%")

# =============================
# ✅ GRAPH TAB
# =============================
with tab2:

    st.subheader("📈 Awareness Trend")

    trend_df = con.execute(f"""
    SELECT 
        Month,
        SUM(CASE WHEN LOWER(TRIM({awareness_col}))='yes'
            THEN {weight_col} ELSE 0 END) * 100.0 /
        SUM(CASE WHEN {awareness_col} IS NOT NULL
            THEN {weight_col} ELSE 0 END) AS Awareness
    FROM df
    {where_clause}
    GROUP BY Month
    """).df()

    if trend_df.empty:
        st.warning("No data to display")
    else:
        chart = alt.Chart(trend_df).mark_line(
            interpolate="monotone",
            strokeWidth=2
        ).encode(
            x=alt.X("Month:N"),
            y=alt.Y("Awareness:Q"),
            tooltip=["Month", "Awareness"]
        )

        st.altair_chart(chart, use_container_width=True)

# -----------------------------
# FILTER SUMMARY
# -----------------------------
st.subheader("Applied Filters")

st.write({
    "Brand": selected_brand,
    "Months": selected_months or "All",
    "Countries": selected_countries or "All",
    "Segment": segment,
    "Weight Used": weight_col
})
