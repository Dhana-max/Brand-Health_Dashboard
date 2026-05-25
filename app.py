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
# ✅ CLEAN DATA AT SOURCE
# -----------------------------
@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT 
            UPPER(TRIM(Month)) AS Month,
            UPPER(TRIM(Country_New)) AS Country_New,
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
# LOAD FILTER VALUES
# -----------------------------
@st.cache_data
def load_filters():
    df = con.execute("SELECT DISTINCT Month, Country_New FROM df").df()
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
# SAFE KPI FUNCTION
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
# SAFE AWARENESS
# -----------------------------
query_awareness = f"""
SELECT 
    SUM(CASE WHEN LOWER(TRIM({awareness_col}))='yes'
        THEN {weight_col} ELSE 0 END),
    SUM({weight_col})
FROM df
{where_clause}
"""

result = con.execute(query_awareness).fetchone()
if result:
    yes_wt, total_wt = result
    awareness = round((yes_wt / total_wt) * 100, 1) if total_wt else 0
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
# DASHBOARD TAB
# =============================
with tab1:

    st.subheader("Key Metrics")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Awareness", f"{awareness}%")
    c2.metric("Favorability", f"{favorability}%")
    c3.metric("Consideration", f"{consideration}%")
    c4.metric("Consideration Effect", f"{consideration_effect}%")

    # ✅ ATTRIBUTES FIXED
    attribute_cols = [
        f"Attributes_New_DP_{code}_Q12a_{i}_slice"
        for i in range(1, 18)
    ]

    attr_names = [f"Attribute {i}" for i in range(1, 18)]
    attr_values = []

    for col in attribute_cols:
        try:
            val = get_top2_metric(col)
        except:
            val = None
        attr_values.append(val)

    attribute_df = pd.DataFrame({
        "Attribute": attr_names,
        "Score (%)": attr_values
    }).dropna()

    st.subheader("Brand Attributes")
    st.dataframe(attribute_df, use_container_width=True)

# =============================
# GRAPHS TAB
# =============================
with tab2:

    st.subheader("📈 Awareness Trend (All Brands)")

    col1, col2 = st.columns(2)

    with col1:
        g_country = st.multiselect("Country", countries)

    with col2:
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

    # build data
    queries = []
    for brand_name, bcode in brand_map.items():
        col = f"Aided_Awareness_{bcode}_slice"

        q = f"""
        SELECT Month, '{brand_name}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100.0 /
        SUM({weight_col}) AS Awareness
        FROM df
        {graph_where}
        GROUP BY Month
        """
        queries.append(q)

    trend_df = con.execute(" UNION ALL ".join(queries)).df()

    # ✅ FORCE FULL MONTHS
    all_months = ["JAN","FEB","MAR","APR","MAY","JUN",
                  "JUL","AUG","SEP","OCT","NOV","DEC"]

    if not trend_df.empty:
        brands_df = pd.DataFrame({"Brand": trend_df["Brand"].unique()})
        months_df = pd.DataFrame({"Month": all_months})
        full = brands_df.merge(months_df, how="cross")

        trend_df = full.merge(trend_df, on=["Brand","Month"], how="left")
        trend_df["Awareness"] = trend_df["Awareness"].fillna(0)

        # chart
        chart = alt.Chart(trend_df).mark_line(interpolate="monotone").encode(
            x=alt.X("Month:N", sort=all_months),
            y=alt.Y("Awareness:Q", scale=alt.Scale(domain=[0,100])),
            color="Brand",
            tooltip=["Month", "Brand", alt.Tooltip("Awareness", format=".1f")]
        ).properties(height=420)

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No data for selected filters")

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
