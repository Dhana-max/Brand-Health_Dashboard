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
# ATTRIBUTE LABELS
attr_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Attributes_New_DP_", na=False)
]

attr_map = {}
for _, r in attr_rows.iterrows():
    var = str(r["Variable"])
    label = str(r["Label"]).strip()
    match = re.findall(r"Q12a_(\d+)", var)
    if match:
        attr_map[int(match[0])] = label

# -----------------------------
@st.cache_data
def load_filters():
    months = con.execute("""
        SELECT Month FROM (
            SELECT Month, ROW_NUMBER() OVER() rn
            FROM df WHERE Month IS NOT NULL
        )
        GROUP BY Month ORDER BY MIN(rn)
    """).df()["Month"].tolist()

    countries = con.execute("""
        SELECT Country_New FROM (
            SELECT Country_New, ROW_NUMBER() OVER() rn
            FROM df WHERE Country_New IS NOT NULL
        )
        GROUP BY Country_New ORDER BY MIN(rn)
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
# BRAND MAP
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# ✅ Fix Twitter
fixed_map = {}
for k, v in brand_map.items():
    if k.lower() in ["x", "twitter", "twitter/x", "x (twitter)"]:
        fixed_map["Twitter/X"] = v
    else:
        fixed_map[k] = v

if "Twitter/X" not in fixed_map:
    for k, v in brand_map.items():
        if "twitter" in k.lower():
            fixed_map["Twitter/X"] = v

brand_map = fixed_map

# -----------------------------
default_brands = ["LinkedIn","Facebook","Indeed","Twitter/X","TikTok","Google"]

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
with tab1:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice','yesno')}%")
    col2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    col3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice')}%")
    col4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

    st.subheader("Attributes")

    cols = st.columns(4)
    for i in range(1, 18):
        label = attr_map.get(i, f"Attribute {i}")
        val = get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")
        cols[(i-1) % 4].metric(label, f"{val}%")

# -----------------------------
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
    ] + [f"All Brands Attribute {i}" for i in range(1, 18)]

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

    df_chart["Month_order"] = pd.Categorical(
        df_chart["Month"], categories=months, ordered=True
    )

    # ✅ FINAL GRAPH MATCHING IMAGE 2
    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X(
            "Month_order:O",
            axis=alt.Axis(
                labelAngle=-45,
                labelOverlap=False,   # ✅ SHOW ALL LABELS
                labelFontSize=9,
                labelLimit=200,
                labelBound=False
            )
        ),
        y="Value:Q",
        color="Brand"
    ).properties(height=450)

    st.altair_chart(chart, use_container_width=True)
