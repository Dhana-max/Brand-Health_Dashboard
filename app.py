import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt
from difflib import get_close_matches

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
# ✅ ✅ ✅ ADVANCED FREE CHATBOT

def find_metric(q):
    keywords = ["awareness","favorability","favourability","consideration","effect"]
    for k in keywords:
        if k in q:
            return "favorability" if k in ["favorability","favourability"] else k

    match = get_close_matches(q, keywords, n=1, cutoff=0.5)
    if match:
        return "favorability" if match[0] in ["favorability","favourability"] else match[0]
    return None

def find_brands(q):
    found = []
    for b in brand_map.keys():
        if b.lower() in q:
            found.append(b)

    if found:
        return found

    words = q.split()
    for w in words:
        match = get_close_matches(w, list(brand_map.keys()), n=1, cutoff=0.6)
        if match:
            found.append(match[0])

    return list(set(found))

def find_attribute(q):
    best = None
    best_score = 0

    for i, text in attr_map.items():
        score = len(set(q.split()) & set(text.lower().split()))
        if score > best_score:
            best_score = score
            best = i

    return best

def get_kpi(code, metric):
    if metric == "awareness":
        return get_metric(f"Aided_Awareness_{code}_slice","yesno")
    else:
        col_map = {
            "favorability":"Brand_Favorability",
            "consideration":"Consideration",
            "effect":"Consideration_Effect"
        }
        return get_metric(f"{col_map[metric]}_{code}_slice")

def local_chatbot(query):

    q = query.lower()
    brands = find_brands(q)
    metric = find_metric(q)

    if not brands:
        return "Please mention a valid brand."

    # ✅ Comparison
    if ("compare" in q or "vs" in q) and len(brands) >= 2:
        if metric:
            res = [f"{b}: {get_kpi(brand_map[b], metric)}%" for b in brands[:2]]
            return "Comparison ("+metric+") → " + " | ".join(res)
        return "Please specify a metric."

    # ✅ Top brand
    if "top" in q or "highest" in q:
        if metric:
            vals = [(b, get_kpi(brand_map[b], metric)) for b in brand_map.keys()]
            top = max(vals, key=lambda x: x[1])
            return f"Top brand for {metric} → {top[0]} ({top[1]}%)"
        return "Specify a metric."

    # ✅ Attribute
    if not metric:
        attr_id = find_attribute(q)
        if attr_id:
            val = get_metric(f"Attributes_New_DP_{brand_map[brands[0]]}_Q12a_{attr_id}_slice")
            return f"{brands[0]} attribute \"{attr_map[attr_id]}\" is {val}%"

        return "Ask about awareness, favorability, consideration, effect or attributes."

    # ✅ Trend
    if "trend" in q:
        return f"Check Graph tab for trend of {brands[0]}"

    # ✅ Single KPI
    val = get_kpi(brand_map[brands[0]], metric)
    return f"{brands[0]} {metric} is {val}%"

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

    selected_brands = colg4.multiselect("Brands", list(brand_map_local.keys()),
                                        default=list(brand_map_local.keys())[:3], key="g_brands")

    view_type = st.radio("View Type", ["Trended View","Brand Comparison"], horizontal=True)

    graph_where = build_where(g_months, g_country, g_segment)

    queries = []
    for brand in selected_brands:
        code = brand_map_local[brand]
        col = f"Aided_Awareness_{code}_slice"

        queries.append(f"""
        SELECT Month,'{brand}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM({col}))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart = con.execute(" UNION ALL ".join(queries)).df()

    df_chart["Month_order"] = pd.Categorical(df_chart["Month"], categories=months, ordered=True)

    chart = alt.Chart(df_chart).mark_line(point=True).encode(
        x="Month_order:O",
        y="Value:Q",
        color="Brand"
    )

    st.altair_chart(chart, use_container_width=True)

# -----------------------------
with tab3:
    st.subheader("🤖 Ask KPI Questions")

    user_query = st.text_input("Ask about KPIs")

    if user_query:
        st.success(local_chatbot(user_query))
