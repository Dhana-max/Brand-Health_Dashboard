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
# ATTRIBUTES
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
# MONTH ORDER
@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() rn
        FROM df WHERE Month IS NOT NULL
    """).df()

    months = df_temp.drop_duplicates("Month").sort_values("rn")["Month"].tolist()

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

# -----------------------------
# BRAND LOGIC (UNCHANGED)
brand_rows = map_df[
    map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)
]

brand_map = {
    str(r["Label"]).split(" - ")[-1].strip():
    int(re.findall(r"\d+", str(r["Variable"]))[0])
    for _, r in brand_rows.iterrows()
}

fixed_map = {}
for k,v in brand_map.items():
    if k.lower() in ["x","twitter","twitter/x","x (twitter)"]:
        fixed_map["Twitter/X"] = v
    else:
        fixed_map[k] = v

if "Twitter/X" not in fixed_map:
    for k,v in brand_map.items():
        if "twitter" in k.lower():
            fixed_map["Twitter/X"] = v

brand_map = fixed_map

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
def get_metric(col, where_clause, weight_col, metric_type="top2"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes'
            THEN {weight_col} ELSE 0 END)*100/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)
            THEN {weight_col} ELSE 0 END)*100/SUM({weight_col})
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
tab1, tab2 = st.tabs(["📊 Dashboard","📈 Graphs"])

# -----------------------------
# ✅ DASHBOARD (UPDATED UI)
with tab1:

    st.subheader("Filters")
    f1,f2,f3,f4 = st.columns(4)

    selected_countries = f1.multiselect("Country", countries)
    selected_months = f2.multiselect("Month", months)
    segment = f3.selectbox("Segment", ["Total","Male","Female"])

    filtered_brand_map = get_brands_by_country(selected_countries)
    selected_brand = f4.selectbox("Brand", sorted(filtered_brand_map.keys()))
    code = filtered_brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

    # KPIs
    st.subheader("KPIs")
    c1,c2,c3,c4 = st.columns(4)

    c1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice',where_clause,weight_col,'yesno')}%")
    c2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice',where_clause,weight_col)}%")
    c3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice',where_clause,weight_col)}%")
    c4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice',where_clause,weight_col)}%")

    # ✅ TABLE FORMAT (NO SCROLL, COMPACT)
    st.subheader("Brand Attributes")

    attr_data = []
    for i in range(1,18):
        val = get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice",where_clause,weight_col)
        attr_data.append([attr_map[i], f"{val}%"])

    df_attr = pd.DataFrame(attr_data, columns=["Attribute","Score"])

    st.table(df_attr)

# -----------------------------
# ✅ GRAPH (FILTERS RESTORED)
with tab2:

    st.subheader("Filters")
    g1,g2 = st.columns(2)

    g_country = g1.multiselect("Country", countries)
    g_segment = g2.selectbox("Segment", ["Total","Male","Female"])

    graph_where = build_where([], g_country, g_segment)
    brand_map_local = get_brands_by_country(g_country)

    metric_options = [
        "All Brands Awareness",
        "All Brands Favorability",
        "All Brands Consideration",
        "All Brands Effect"
    ] + list(attr_map.values())

    selected_metric = st.selectbox("Metric", metric_options)

    queries = []

    for brand,bcode in brand_map_local.items():

        if selected_metric in attr_map.values():
            i = list(attr_map.keys())[list(attr_map.values()).index(selected_metric)]
            col = f"Attributes_New_DP_{bcode}_Q12a_{i}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)"

        elif selected_metric == "All Brands Awareness":
            col = f"Aided_Awareness_{bcode}_slice"
            formula = f"LOWER(TRIM({col}))='yes'"

        elif selected_metric == "All Brands Favorability":
            col = f"Brand_Favorability_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)"

        elif selected_metric == "All Brands Consideration":
            col = f"Consideration_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)"

        elif selected_metric == "All Brands Effect":
            col = f"Consideration_Effect_{bcode}_slice"
            formula = f"TRY_CAST(REGEXP_EXTRACT({col}, '\\d+') AS INT) IN (4,5)"

        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN {formula}
        THEN {weight_col} ELSE 0 END)*100/SUM({weight_col}) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x=alt.X("Month_order:O",
                sort=months,
                axis=alt.Axis(labelAngle=-45,labelOverlap=False,labelFontSize=9)),
        y="Value:Q",
        color="Brand"
    ).properties(height=450)

    st.altair_chart(chart, use_container_width=True)
