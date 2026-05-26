import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

st.set_page_config(layout="wide")
st.title("Brand Health Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

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
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# -----------------------------
@st.cache_data
def load_filters():
    months = con.execute(
        "SELECT DISTINCT Month FROM df WHERE Month IS NOT NULL"
    ).df()["Month"].tolist()

    countries = con.execute(
        "SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL"
    ).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
# BRAND MAP
# -----------------------------
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip(): int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

brand_alias = {
    "x": "Twitter/X",
    "twitter": "Twitter/X",
    "twitter/x": "Twitter/X"
}

brand_map = {
    brand_alias.get(k.lower().strip(), k): v
    for k, v in brand_map.items()
}

# -----------------------------
# ✅ SAFE WHERE BUILDER
# -----------------------------
def build_where(months_sel, countries_sel, segment):
    filters = []

    if months_sel:
        mvals = ",".join("'" + str(m) + "'" for m in months_sel)
        filters.append("Month IN (" + mvals + ")")

    if countries_sel:
        cvals = ",".join("'" + str(c) + "'" for c in countries_sel)
        filters.append("Country_New IN (" + cvals + ")")

    if segment == "Male":
        filters.append("Sex = 1")
    elif segment == "Female":
        filters.append("Sex = 2")

    return "WHERE " + " AND ".join(filters) if filters else ""

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Filters")

selected_countries = st.sidebar.multiselect("Country", countries)
selected_months = st.sidebar.multiselect("Month", months)
segment = st.sidebar.selectbox("Segment", ["Total","Male","Female"])

selected_brand = st.sidebar.selectbox("Brand", sorted(brand_map.keys()))
code = brand_map[selected_brand]

where_clause = build_where(selected_months, selected_countries, segment)
weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

# -----------------------------
# ✅ METRIC FUNCTION
# -----------------------------
def get_metric(col, metric_type="top2"):
    try:
        # Awareness (yes/no)
        if metric_type == "yesno":
            q = f"""
            SELECT 
            SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/
            SUM({weight_col})
            FROM df {where_clause}
            """

        else:
            q = f"""
            SELECT 
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0/
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """

        result = con.execute(q).fetchone()[0]
        return round(result or 0, 1)

    except:
        return 0

# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

# -----------------------------
# DASHBOARD
# -----------------------------
with tab1:
    st.subheader("Key Metrics")

    st.metric("Awareness",
        f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno')}%")

    st.metric("Favorability",
        f"{get_metric(f'Brand_Favorability_{code}_slice')}%")

    st.metric("Consideration",
        f"{get_metric(f'Consideration_{code}_slice')}%")

    st.metric("Consideration Effect",
        f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

# -----------------------------
# ✅ GRAPH (ALL BRANDS FOR ALL METRICS)
# -----------------------------
with tab2:

    st.subheader("📈 Trend Chart")

    g_country = st.multiselect("Country (graph)", countries)
    g_segment = st.selectbox("Segment (graph)", ["Total","Male","Female"])

    graph_where = build_where(selected_months, g_country, g_segment)

    metric_options = [
        "All Brands Awareness",
        "Awareness",
        "Favorability",
        "Consideration",
        "Consideration Effect"
    ] + [f"Attribute {i}" for i in range(1,18)]

    selected_metric = st.selectbox("Select Metric", metric_options)

    queries = []

    for brand, bcode in brand_map.items():

        # Awareness
        if selected_metric in ["All Brands Awareness", "Awareness"]:
            col = f"Aided_Awareness_{bcode}_slice"

            queries.append(f"""
            SELECT Month, '{brand}' AS Brand,
            SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0 / SUM({weight_col}) AS Value
            FROM df {graph_where}
            GROUP BY Month
            """)

        # Other KPIs
        elif selected_metric in ["Favorability","Consideration","Consideration Effect"]:
            col_map = {
                "Favorability": f"Brand_Favorability_{bcode}_slice",
                "Consideration": f"Consideration_{bcode}_slice",
                "Consideration Effect": f"Consideration_Effect_{bcode}_slice"
            }

            col = col_map[selected_metric]

            queries.append(f"""
            SELECT Month, '{brand}' AS Brand,
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END) AS Value
            FROM df {graph_where}
            GROUP BY Month
            """)

        # Attributes
        else:
            i = int(selected_metric.split()[-1])
            col = f"Attributes_New_DP_{bcode}_Q12a_{i}_slice"

            queries.append(f"""
            SELECT Month, '{brand}' AS Brand,
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END) AS Value
            FROM df {graph_where}
            GROUP BY Month
            """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X("Month:N", sort=months),
        y=alt.Y("Value:Q", title=selected_metric),
        color="Brand"
    )

    st.altair_chart(chart, use_container_width=True)
