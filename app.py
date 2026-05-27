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
@st.cache_data
def load_filters():
    df_temp = con.execute("""
        SELECT Month, ROW_NUMBER() OVER() AS rn
        FROM df WHERE Month IS NOT NULL
    """).df()

    months = (
        df_temp.drop_duplicates("Month")
        .sort_values("rn")["Month"]
        .tolist()
    )

    countries = con.execute("""
        SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL
    """).df()["Country_New"].tolist()

    return months, countries

months, countries = load_filters()

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
def get_brands_by_country(selected_countries):
    return brand_map

# -----------------------------
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
            THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5
            THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
# ✅ ✅ SMART FREE CHATBOT (ONLY CHANGE)

def extract_month(query):
    for m in months:
        if m.lower() in query:
            return m
    return None

def extract_brands(query):
    found = []
    for b in brand_map.keys():
        if b.lower() in query:
            found.append(b)
    return found

def local_chatbot(query):

    q = query.lower()

    brands = extract_brands(q)
    month = extract_month(q)

    temp_months = [month] if month else selected_months
    temp_where = build_where(temp_months, selected_countries, segment)

    def metric_value(brand, metric_type):
        code = brand_map[brand]

        if metric_type == "awareness":
            col = f"Aided_Awareness_{code}_slice"
            formula = f"LOWER(TRIM({col}))='yes'"
            q_sql = f"""
            SELECT SUM(CASE WHEN {formula}
            THEN Global_weight_Stacked ELSE 0 END)*100.0 /
            SUM(Global_weight_Stacked)
            FROM df {temp_where}
            """
        else:
            col_map = {
                "favorability": f"Brand_Favorability_{code}_slice",
                "consideration": f"Consideration_{code}_slice",
                "effect": f"Consideration_Effect_{code}_slice"
            }
            col = col_map[metric_type]

            q_sql = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
            THEN Global_weight_Stacked ELSE 0 END)*100.0 /
            SUM(Global_weight_Stacked)
            FROM df {temp_where}
            """

        return round(con.execute(q_sql).fetchone()[0] or 0, 1)

    if "awareness" in q:
        metric = "awareness"
    elif "favorability" in q:
        metric = "favorability"
    elif "consideration" in q:
        metric = "consideration"
    elif "effect" in q:
        metric = "effect"
    else:
        metric = None

    if ("compare" in q or "vs" in q) and len(brands) >= 2 and metric:
        results = [f"{b}: {metric_value(b, metric)}%" for b in brands]
        return f"Comparison ({metric}): " + " | ".join(results)

    if brands and metric:
        val = metric_value(brands[0], metric)
        return f"{brands[0]} {metric}" + (f" in {month}" if month else "") + f" is {val}%"

    if ("top" in q or "highest" in q) and metric:
        results = [(b, metric_value(b, metric)) for b in brand_map.keys()]
        top = max(results, key=lambda x: x[1])
        return f"Top brand for {metric}: {top[0]} ({top[1]}%)"

    if "trend" in q and brands:
        return f"Please check the graph tab for trend of {brands[0]}"

    if "attribute" in q and brands:
        code = brand_map[brands[0]]
        results = [(attr_map[i], get_metric(f\"Attributes_New_DP_{code}_Q12a_{i}_slice\")) for i in range(1,18)]
        top = max(results, key=lambda x: x[1])
        return f"Top attribute for {brands[0]}: {top[0]} ({top[1]}%)"

    return "Try: LinkedIn awareness, Compare LinkedIn vs Facebook, Top brand, or attributes."

# -----------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:
    colf1, colf2, colf3, colf4 = st.columns(4)

    selected_countries = colf1.multiselect("Country", countries)
    selected_months = colf2.multiselect("Month", months)
    segment = colf3.selectbox("Segment", ["Total","Male","Female"])

    filtered_brand_map = get_brands_by_country(selected_countries)
    selected_brand = colf4.selectbox("Brand", list(filtered_brand_map.keys()))

    code = filtered_brand_map[selected_brand]

    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Awareness", f"{get_metric(f'Aided_Awareness_{code}_slice','yesno')}%")
    col2.metric("Favorability", f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    col3.metric("Consideration", f"{get_metric(f'Consideration_{code}_slice')}%")
    col4.metric("Effect", f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

    st.subheader("Brand Attributes")

    attr_data = [{"Attribute": attr_map[i], "Value (%)": get_metric(f"Attributes_New_DP_{code}_Q12a_{i}_slice")} for i in range(1,18)]
    st.dataframe(pd.DataFrame(attr_data), use_container_width=True)

# -----------------------------
with tab2:

    colg1, colg2, colg3, colg4 = st.columns(4)

    g_country = colg1.multiselect("Country", countries, key="g_country")
    g_months = colg2.multiselect("Month", months, key="g_months")
    g_segment = colg3.selectbox("Segment", ["Total","Male","Female"], key="g_segment")

    brand_map_local = get_brands_by_country(g_country)
    brand_list = list(brand_map_local.keys())

    selected_brands = colg4.multiselect("Brands", brand_list, default=brand_list[:3], key="g_brands")

    view_type = st.radio("View Type", ["Trended View","Brand Comparison"], horizontal=True)

    graph_where = build_where(g_months, g_country, g_segment)

    queries = []
    for brand in selected_brands:
        code = brand_map_local[brand]
        col = f"Aided_Awareness_{code}_slice"
        formula = f"LOWER(TRIM({col}))='yes'"

        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN {formula}
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)

    if view_type == "Trended View":
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x=alt.X("Month_order:O", sort=months,
                    axis=alt.Axis(labelAngle=-45,labelOverlap=False)),
            y="Value:Q",
            color="Brand"
        )
    else:
        chart = alt.Chart(df_chart).mark_line(point=True).encode(
            x="Brand",
            y="Value:Q",
            color=alt.Color("Month:O", sort=months)
        )

    st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:

    st.subheader("🤖 Ask KPI Questions")

    user_query = st.text_input("Ask about KPIs")

    if user_query:
        response = local_chatbot(user_query)
        st.success(response)
