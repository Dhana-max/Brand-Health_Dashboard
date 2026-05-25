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
# CONNECTION
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
# LOAD MAP
# -----------------------------
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# -----------------------------
# LOAD FILTERS (ORDER PRESERVED)
# -----------------------------
@st.cache_data
def load_filters():

    temp = con.execute("""
        SELECT Month FROM (
            SELECT Month, ROW_NUMBER() OVER() rn
            FROM df WHERE Month IS NOT NULL
        )
        GROUP BY Month ORDER BY MIN(rn)
    """).df()

    months = temp["Month"].tolist()

    ctemp = con.execute("""
        SELECT Country_New FROM (
            SELECT Country_New, ROW_NUMBER() OVER() rn
            FROM df WHERE Country_New IS NOT NULL
        )
        GROUP BY Country_New ORDER BY MIN(rn)
    """).df()

    countries = ctemp["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
# BRAND MAP
# -----------------------------
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# -----------------------------
# DASHBOARD FILTERS
# -----------------------------
st.sidebar.header("Filters")

selected_brand = st.sidebar.selectbox("Brand", sorted(brand_map.keys()))
selected_months = st.sidebar.multiselect("Month", months)
selected_countries = st.sidebar.multiselect("Country", countries)
segment = st.sidebar.selectbox("Segment", ["Total","Male","Female"])

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
# WEIGHT
# -----------------------------
weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

# -----------------------------
# KPI COLUMNS
# -----------------------------
awareness_col = f"Aided_Awareness_{code}_slice"
fav_col = f"Brand_Favorability_{code}_slice"
cons_col = f"Consideration_{code}_slice"
eff_col = f"Consideration_Effect_{code}_slice"

# -----------------------------
# KPI FUNCTION (UNCHANGED)
# -----------------------------
def get_top2_metric(col):
    try:
        query = f"""
        SELECT 
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
                THEN {weight_col} ELSE 0 END),
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
                THEN {weight_col} ELSE 0 END)
        FROM df {where_clause}
        """
        res = con.execute(query).fetchone()
        return round((res[0]/res[1])*100,1) if res and res[1] else 0
    except:
        return 0

# -----------------------------
# AWARENESS KPI
# -----------------------------
query_awareness = f"""
SELECT 
SUM(CASE WHEN LOWER(TRIM({awareness_col}))='yes' THEN {weight_col} ELSE 0 END),
SUM(CASE WHEN LOWER(TRIM({awareness_col})) IN ('yes','no','dont know','don''t know')
    THEN {weight_col} ELSE 0 END)
FROM df {where_clause}
"""

res = con.execute(query_awareness).fetchone()
awareness = round((res[0]/res[1])*100,1) if res and res[1] else 0

# KPI VALUES
favorability = get_top2_metric(fav_col)
consideration = get_top2_metric(cons_col)
consideration_effect = get_top2_metric(eff_col)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

# -----------------------------
# DASHBOARD TAB
# -----------------------------
with tab1:

    st.subheader("Key Metrics")

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Awareness", f"{awareness}%")
    c2.metric("Favorability", f"{favorability}%")
    c3.metric("Consideration", f"{consideration}%")
    c4.metric("Consideration Effect", f"{consideration_effect}%")

    # ✅ ATTRIBUTES (RESTORED)
    attribute_cols = [
        f"Attributes_New_DP_{code}_Q12a_{i}_slice"
        for i in range(1, 18)
    ]

    attribute_values = [get_top2_metric(col) for col in attribute_cols]

    attr_df = pd.DataFrame({
        "Attribute": [f"Attribute {i}" for i in range(1, 18)],
        "Score (%)": attribute_values
    })

    st.subheader("Brand Attributes")
    st.dataframe(attr_df)

# -----------------------------
# GRAPH TAB
# -----------------------------
with tab2:

    st.subheader("📈 Awareness Trend (All Brands)")

    # ✅ GRAPH FILTERS (Independent)
    col1, col2 = st.columns(2)

    with col1:
        g_country = st.multiselect("Country", countries)

    with col2:
        g_segment = st.selectbox("Segment", ["Total","Male","Female"])

    graph_filters = []

    if g_country:
        graph_filters.append("Country_New IN ({})".format(",".join([f"'{c}'" for c in g_country])))

    if g_segment == "Male":
        graph_filters.append("Sex = 1")
    elif g_segment == "Female":
        graph_filters.append("Sex = 2")

    graph_where = " AND ".join(graph_filters)
    if graph_where:
        graph_where = "WHERE " + graph_where

    queries = []

    for b, bcode in brand_map.items():
        col = f"Aided_Awareness_{bcode}_slice"

        q = f"""
        SELECT Month, '{b}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0 /
        SUM({weight_col}) AS Awareness
        FROM df {graph_where}
        GROUP BY Month
        """
        queries.append(q)

    trend_df = con.execute(" UNION ALL ".join(queries)).df()

    if not trend_df.empty:

        chart = alt.Chart(trend_df).mark_line(
            interpolate="monotone"
        ).encode(
            x=alt.X("Month:N", sort=months),
            y=alt.Y("Awareness:Q", scale=alt.Scale(domain=[0,100])),
            color="Brand",
            tooltip=["Month","Brand","Awareness"]
        )

        points = chart.mark_circle(size=40)

        st.altair_chart(chart + points, use_container_width=True)

    else:
        st.warning("No data available")
