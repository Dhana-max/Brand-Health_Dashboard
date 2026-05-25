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
# ✅ CLEAN DATA (FINAL FIX)
# -----------------------------
@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT 

        -- ✅ CLEAN MONTH
        CASE 
            WHEN UPPER(TRIM(Month)) LIKE '%JAN%' THEN 'JAN'
            WHEN UPPER(TRIM(Month)) LIKE '%FEB%' THEN 'FEB'
            WHEN UPPER(TRIM(Month)) LIKE '%MAR%' THEN 'MAR'
            WHEN UPPER(TRIM(Month)) LIKE '%APR%' THEN 'APR'
            WHEN UPPER(TRIM(Month)) LIKE '%MAY%' THEN 'MAY'
            WHEN UPPER(TRIM(Month)) LIKE '%JUN%' THEN 'JUN'
            WHEN UPPER(TRIM(Month)) LIKE '%JUL%' THEN 'JUL'
            WHEN UPPER(TRIM(Month)) LIKE '%AUG%' THEN 'AUG'
            WHEN UPPER(TRIM(Month)) LIKE '%SEP%' THEN 'SEP'
            WHEN UPPER(TRIM(Month)) LIKE '%OCT%' THEN 'OCT'
            WHEN UPPER(TRIM(Month)) LIKE '%NOV%' THEN 'NOV'
            WHEN UPPER(TRIM(Month)) LIKE '%DEC%' THEN 'DEC'
            ELSE NULL
        END AS Month,

        -- ✅ CLEAN COUNTRY
        CASE 
            WHEN UPPER(TRIM(Country_New)) IN ('US','USA','U.S.','UNITED STATES') 
                THEN 'UNITED STATES'
            WHEN UPPER(TRIM(Country_New)) LIKE '%INDIA%' 
                THEN 'INDIA'
            ELSE UPPER(TRIM(Country_New))
        END AS Country_New,

        *
        EXCLUDE (Month, Country_New)

        FROM read_parquet('{PARQUET_URL}')
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
# LOAD FILTERS
# -----------------------------
@st.cache_data
def load_filters():
    df = con.execute("""
        SELECT DISTINCT Month, Country_New 
        FROM df
        WHERE Month IS NOT NULL AND Country_New IS NOT NULL
    """).df()

    return sorted(df["Month"]), sorted(df["Country_New"])

months, countries = load_filters()

# -----------------------------
# BRAND MAP
# -----------------------------
brand_rows = map_df[map_df["Variable"].str.contains("Aided_Awareness_", na=False)]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip(): int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

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
# WEIGHT
# -----------------------------
weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

# -----------------------------
# KPI COLUMNS
# -----------------------------
awareness_col = f"Aided_Awareness_{code}_slice"
fav_col = f"Brand_Favorability_{code}_slice"
cons_col = f"Consideration_{code}_slice"
eff_col = f"Consideration_Effect_{code}_slice"

# -----------------------------
# ✅ SAFE KPI FUNCTION
# -----------------------------
def get_top2_metric(col):
    try:
        query = f"""
        SELECT 
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)
                THEN {weight_col} ELSE 0 END),
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IS NOT NULL
                THEN {weight_col} ELSE 0 END)
        FROM df
        {where_clause}
        """
        result = con.execute(query).fetchone()
        if not result:
            return 0
        num, den = result
        return round((num / den) * 100, 1) if den else 0
    except:
        return 0

# -----------------------------
# ✅ FIXED AWARENESS (KEY FIX)
# -----------------------------
query_awareness = f"""
SELECT 
    SUM(CASE 
        WHEN LOWER(TRIM({awareness_col})) IN ('yes','1','true','selected')
        THEN {weight_col} ELSE 0 END),

    SUM(CASE 
        WHEN {awareness_col} IS NOT NULL
        THEN {weight_col} ELSE 0 END)

FROM df
{where_clause}
"""

res = con.execute(query_awareness).fetchone()

if res and res[1]:
    awareness = round((res[0] / res[1]) * 100, 1)
else:
    awareness = 0

# -----------------------------
# KPI VALUES
# -----------------------------
favorability = get_top2_metric(fav_col)
consideration = get_top2_metric(cons_col)
consideration_effect = get_top2_metric(eff_col)

# -----------------------------
# TABS
# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard", "📈 Graphs"])

# =============================
# DASHBOARD
# =============================
with tab1:

    st.subheader("Key Metrics")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Awareness", f"{awareness}%")
    c2.metric("Favorability", f"{favorability}%")
    c3.metric("Consideration", f"{consideration}%")
    c4.metric("Consideration Effect", f"{consideration_effect}%")

    # ✅ Attributes
    attrs = []
    for i in range(1,18):
        col = f"Attributes_New_DP_{code}_Q12a_{i}_slice"
        val = get_top2_metric(col)
        attrs.append([f"Attribute {i}", val])

    attr_df = pd.DataFrame(attrs, columns=["Attribute","Score (%)"])

    st.subheader("Brand Attributes")
    st.dataframe(attr_df)

# =============================
# GRAPH TAB
# =============================
with tab2:

    st.subheader("📈 Awareness Trend (All Brands)")

    g_country = st.multiselect("Country", countries)
    g_segment = st.selectbox("Segment", ["Total", "Male", "Female"])

    graph_filters = []

    if g_country:
        graph_filters.append(
            "Country_New IN ({})".format(",".join([f"'{c}'" for c in g_country]))
        )

    if g_segment == "Male":
        graph_filters.append("Sex = 1")
    elif g_segment == "Female":
        graph_filters.append("Sex = 2")

    graph_where = " AND ".join(graph_filters)
    if graph_where:
        graph_where = "WHERE " + graph_where

    queries = []

    for brand, bcode in brand_map.items():
        col = f"Aided_Awareness_{bcode}_slice"

        q = f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col})) IN ('yes','1','true')
            THEN {weight_col} ELSE 0 END)*100.0 /
        SUM({weight_col}) AS Awareness
        FROM df {graph_where}
        GROUP BY Month
        """
        queries.append(q)

    trend_df = con.execute(" UNION ALL ".join(queries)).df()

    all_months = ["JAN","FEB","MAR","APR","MAY","JUN",
                  "JUL","AUG","SEP","OCT","NOV","DEC"]

    if not trend_df.empty:
        brands = pd.DataFrame({"Brand": trend_df["Brand"].unique()})
        months_df = pd.DataFrame({"Month": all_months})
        grid = brands.merge(months_df, how="cross")

        trend_df = grid.merge(trend_df, on=["Brand","Month"], how="left")
        trend_df["Awareness"] = trend_df["Awareness"].fillna(0)

        chart = alt.Chart(trend_df).mark_line(
            interpolate="monotone",
            strokeWidth=2
        ).encode(
            x=alt.X("Month:N", sort=all_months),
            y=alt.Y("Awareness:Q", scale=alt.Scale(domain=[0,100])),
            color="Brand",
            tooltip=["Month","Brand","Awareness"]
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No data available")

# -----------------------------
# SUMMARY
# -----------------------------
st.subheader("Applied Filters")

st.write({
    "Brand": selected_brand,
    "Months": selected_months or "All",
    "Countries": selected_countries or "All",
    "Segment": segment
})
