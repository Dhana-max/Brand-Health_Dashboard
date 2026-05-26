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
# ✅ ATTRIBUTE LABELS (YOUR FINAL LIST)
attr_map = {
    1: "Helps me move forward professionally",
    2: "Helps me find the right job for me",
    3: "Helps me navigate my professional life",
    4: "Is a place I feel I belong",
    5: "Cares about issues that matter to me",
    6: "Is a brand I love",
    7: "Is a brand I trust",
    8: "Makes me feel like I'm part of a community",
    9: "Helps me stay informed on professional topics that matter to me",
    10: "Is a place where discussions related to my work life happen",
    11: "Is useful for me to visit every day",
    12: "Is a platform where I create/share content",
    13: "I use this more frequently to create/share content than before",
    14: "Is a platform I would use as part of my job",
    15: "Helps me reach my goals",
    16: "Is a locally relevant professional network",
    17: "Helps me move forward in my career/business"
}

# -----------------------------
# ✅ PRESERVE ORIGINAL MONTH ORDER
@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() AS rn
        FROM df
        WHERE Month IS NOT NULL
    """).df()

    months = (
        df_temp.drop_duplicates(subset=["Month"])
        .sort_values("rn")["Month"]
        .tolist()
    )

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df
        WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
# ✅ ORIGINAL BRAND LOGIC (UNCHANGED ✅)
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# ✅ FIX Twitter ONLY
fixed_map = {}
for k, v in brand_map.items():
    if k.lower().strip() in ["x", "twitter", "twitter/x", "x (twitter)"]:
        fixed_map["Twitter/X"] = v
    else:
        fixed_map[k] = v

if "Twitter/X" not in fixed_map:
    for k, v in brand_map.items():
        if "twitter" in k.lower():
            fixed_map["Twitter/X"] = v

brand_map = fixed_map

# ✅ Default brands logic
default_brands = ["LinkedIn","Facebook","Indeed","Twitter/X","TikTok","Google"]

# ✅ Country-based brand filter (UNCHANGED)
def get_brands_by_country(selected_countries):

    if not selected_countries:
        return brand_map

    if len(selected_countries) == len(countries):
        return {b: brand_map[b] for b in default_brands if b in brand_map}

    filtered = {}

    for brand, code in brand_map.items():
        col = f"Aided_Awareness_{code}_slice"

        query = f"""
        SELECT COUNT(*) FROM df
        WHERE Country_New IN ({",".join("'" + c + "'" for c in selected_countries)})
        AND {col} IS NOT NULL
        """

        if con.execute(query).fetchone()[0] > 0:
            filtered[brand] = code

    return filtered

# -----------------------------
def build_where(months_sel, countries_sel, segment):
    filters = []

    if months_sel:
        filters.append("Month IN (" + ",".join("'" + m + "'" for m in months_sel) + ")")

    if countries_sel:
        filters.append("Country_New IN (" + ",".join("'" + c + "'" for c in countries_sel) + ")")

    if segment == "Male":
        filters.append("Sex = 1")
    elif segment == "Female":
        filters.append("Sex = 2")

    return "WHERE " + " AND ".join(filters) if filters else ""

# -----------------------------
st.sidebar.header("Filters")

selected_countries = st.sidebar.multiselect("Country", countries)
selected_months = st.sidebar.multiselect("Month", months)
segment = st.sidebar.selectbox("Segment", ["Total","Male","Female"])

filtered_brand_map = get_brands_by_country(selected_countries)

selected_brand = st.sidebar.selectbox("Brand", sorted(filtered_brand_map.keys()))
code = filtered_brand_map[selected_brand]

where_clause = build_where(selected_months, selected_countries, segment)
weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

# -----------------------------
def get_metric(col, metric_type="top2"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0/
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

# -----------------------------
# ✅ DASHBOARD
with tab1:

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice','yesno')}%")
    col2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    col3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice')}%")
    col4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

    st.subheader("Brand Attributes")

    cols = st.columns(4)

    for i in range(1, 18):
        val = get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")
        cols[(i-1) % 4].metric(attr_map[i], f"{val}%")

# -----------------------------
# ✅ GRAPH
with tab2:

    g_country = st.multiselect("Country (graph)", countries)
    g_segment = st.selectbox("Segment (graph)", ["Total","Male","Female"])

    graph_where = build_where([], g_country, g_segment)
    brand_map_local = get_brands_by_country(g_country)

    metric_options = [
        "All Brands Awareness",
        "All Brands Favorability",
        "All Brands Consideration",
        "All Brands Effect"
    ] + [f"Attribute {i}" for i in range(1,18)]

    selected_metric = st.selectbox("Metric", metric_options)

    queries = []

    for brand, bcode in brand_map_local.items():

        if "Attribute" in selected_metric:
            i = int(selected_metric.split()[-1])
            col = f"Attributes_New_DP_{bcode}_Q12a_{i}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)"

        elif selected_metric == "All Brands Awareness":
            col = f"Aided_Awareness_{bcode}_slice"
            formula = f"LOWER(TRIM({col}))='yes'"

        elif selected_metric == "All Brands Favorability":
            col = f"Brand_Favorability_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)"

        elif selected_metric == "All Brands Consideration":
            col = f"Consideration_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)"

        elif selected_metric == "All Brands Effect":
            col = f"Consideration_Effect_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)"

        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN {formula}
        THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col}) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    # ✅ ORDER FIX
    df_chart["Month_order"] = pd.Categorical(
        df_chart["Month"], categories=months, ordered=True
    )

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X(
            "Month_order:O",
            axis=alt.Axis(
                labelAngle=-45,
                labelOverlap=False,
                labelFontSize=9
            )
        ),
        y="Value:Q",
        color="Brand"
    ).properties(height=450)

    st.altair_chart(chart, use_container_width=True)
