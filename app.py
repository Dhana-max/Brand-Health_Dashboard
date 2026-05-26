import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

# -----------------------------
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
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip(): int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

# ✅ Normalize names
brand_alias = {
    "x": "Twitter/X",
    "twitter": "Twitter/X",
    "twitter/x": "Twitter/X",
    "x (twitter)": "Twitter/X"
}

brand_map = {
    brand_alias.get(k.lower().strip(), k): v
    for k, v in brand_map.items()
}

# ✅ ensure Twitter/X exists
if "Twitter/X" not in brand_map:
    for k, v in brand_map.items():
        if "twitter" in k.lower():
            brand_map["Twitter/X"] = v
            break

default_brands = ["LinkedIn","Indeed","Facebook","Google","Twitter/X","TikTok"]

# -----------------------------
def get_brands_by_country(selected_countries):

    if selected_countries and len(selected_countries) == len(countries):
        return {b: brand_map[b] for b in default_brands if b in brand_map}

    if not selected_countries:
        return brand_map

    filtered = {}

    for brand, code in brand_map.items():
        col = f"Aided_Awareness_{code}_slice"

        try:
            query = f"""
            SELECT COUNT(*) FROM df
            WHERE Country_New IN ({",".join([f"'{c}'" for c in selected_countries])})
            AND {col} IS NOT NULL
            """
            if con.execute(query).fetchone()[0] > 0:
                filtered[brand] = code
        except:
            pass

    return filtered

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Filters")

selected_countries = st.sidebar.multiselect("Country", countries)
filtered_brand_map = get_brands_by_country(selected_countries)

selected_brand = st.sidebar.selectbox("Brand", sorted(filtered_brand_map.keys()))
selected_months = st.sidebar.multiselect("Month", months)
segment = st.sidebar.selectbox("Segment", ["Total","Male","Female"])

code = filtered_brand_map[selected_brand]

# -----------------------------
# WHERE
# -----------------------------
filters = []

if selected_months:
    filters.append(f"Month IN ({','.join([f'\\'{m}\\'' for m in selected_months])})")

if selected_countries:
    filters.append(f"Country_New IN ({','.join([f'\\'{c}\\'' for c in selected_countries])})")

if segment == "Male":
    filters.append("Sex = 1")
elif segment == "Female":
    filters.append("Sex = 2")

where_clause = " AND ".join(filters)
if where_clause:
    where_clause = "WHERE " + where_clause

weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

awareness_col = f"Aided_Awareness_{code}_slice"
fav_col = f"Brand_Favorability_{code}_slice"
cons_col = f"Consideration_{code}_slice"
eff_col = f"Consideration_Effect_{code}_slice"

# -----------------------------
def get_top2_metric(col):
    try:
        q = f"""
        SELECT 
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END),
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
        FROM df {where_clause}
        """
        a, b = con.execute(q).fetchone()
        return round((a/b)*100,1) if b else 0
    except:
        return 0

# -----------------------------
# DASHBOARD
# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

with tab1:

    st.subheader("Key Metrics")

    st.metric("Awareness", f"{get_top2_metric(awareness_col)}%")
    st.metric("Favorability", f"{get_top2_metric(fav_col)}%")
    st.metric("Consideration", f"{get_top2_metric(cons_col)}%")
    st.metric("Consideration Effect", f"{get_top2_metric(eff_col)}%")

# -----------------------------
# ✅ SINGLE GRAPH WITH METRIC SELECTOR
# -----------------------------
with tab2:

    st.subheader("📈 Trend Chart")

    g_country = st.multiselect("Country", countries)
    g_segment = st.selectbox("Segment", ["Total","Male","Female"])

    graph_where = ""

    # ✅ Metric Selector added here
    metric_options = ["All Brands Awareness"] + [
        "Awareness","Favorability","Consideration","Consideration Effect"
    ] + [f"Attribute {i}" for i in range(1,18)]

    selected_metric = st.selectbox("Select Metric", metric_options)

    # -----------------------------
    # ALL BRANDS
    # -----------------------------
    if selected_metric == "All Brands Awareness":

        brand_map_local = get_brands_by_country(g_country)
        queries = []

        for b, bcode in brand_map_local.items():
            col = f"Aided_Awareness_{bcode}_slice"

            queries.append(f"""
            SELECT Month, '{b}' AS Brand,
            SUM(CASE WHEN LOWER(TRIM({col}))='yes'
                THEN {weight_col} ELSE 0 END)*100.0 / SUM({weight_col}) AS Value
            FROM df
            GROUP BY Month
            """)

        df_chart = con.execute(" UNION ALL ".join(queries)).df()

        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x=alt.X("Month:N", sort=months),
            y="Value:Q",
            color="Brand"
        )

    # -----------------------------
    # SINGLE KPI
    # -----------------------------
    else:

        if selected_metric == "Awareness":
            col = awareness_col
            query = f"""
            SELECT Month,
            SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col}) as Value
            FROM df GROUP BY Month
            """

        elif selected_metric in ["Favorability","Consideration","Consideration Effect"]:
            col_map = {
                "Favorability": fav_col,
                "Consideration": cons_col,
                "Consideration Effect": eff_col
            }
            col = col_map[selected_metric]

            query = f"""
            SELECT Month,
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0/
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END) as Value
            FROM df GROUP BY Month
            """

        else:
            i = int(selected_metric.split()[-1])
            col = f"Attributes_New_DP_{code}_Q12a_{i}_slice"

            query = f"""
            SELECT Month,
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100.0/
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END) as Value
            FROM df GROUP BY Month
            """

        df_chart = con.execute(query).df()

        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x=alt.X("Month:N", sort=months),
            y=alt.Y("Value:Q", title=selected_metric)
        )

    st.altair_chart(chart, use_container_width=True)
