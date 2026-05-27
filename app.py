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

    months = df_temp.drop_duplicates("Month").sort_values("rn")["Month"].tolist()

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
# ✅ ADVANCED CHATBOT

def find_metric(q):
    keys = ["awareness","favorability","favourability","consideration","effect"]
    for k in keys:
        if k in q:
            return "favorability" if k in ["favorability","favourability"] else k
    match = get_close_matches(q, keys, n=1, cutoff=0.5)
    if match:
        return "favorability" if match[0] in ["favorability","favourability"] else match[0]
    return None

def find_brands(q):
    found = [b for b in brand_map if b.lower() in q]
    if found:
        return found
    for w in q.split():
        m = get_close_matches(w, list(brand_map.keys()), n=1, cutoff=0.6)
        if m:
            found.append(m[0])
    return list(set(found))

def find_country(q):
    for c in countries:
        if c.lower() in q:
            return [c]
    for w in q.split():
        m = get_close_matches(w, countries, n=1, cutoff=0.6)
        if m:
            return m
    return None

def find_month(q):
    for m in months:
        if m.lower() in q:
            return [m]
    return None

def find_attribute(q):
    best, score = None, 0
    for i, txt in attr_map.items():
        s = len(set(q.split()) & set(txt.lower().split()))
        if s > score:
            best, score = i, s
    return best

def get_kpi(code, metric, where):
    if metric == "awareness":
        col = f"Aided_Awareness_{code}_slice"
        formula = f"LOWER(TRIM({col}))='yes'"
        q = f"""
        SELECT SUM(CASE WHEN {formula}
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked)
        FROM df {where}
        """
    else:
        m = {
            "favorability":"Brand_Favorability",
            "consideration":"Consideration",
            "effect":"Consideration_Effect"
        }[metric]
        col = f"{m}_{code}_slice"
        q = f"""
        SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5)
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked)
        FROM df {where}
        """
    return round(con.execute(q).fetchone()[0] or 0,1)

def local_chatbot(query):

    q = query.lower()
    brands = find_brands(q)
    metric = find_metric(q)
    attr = find_attribute(q)
    country_sel = find_country(q)
    month_sel = find_month(q)

    if not brands:
        return "Please mention a valid brand."

    temp_where = build_where(month_sel or selected_months,
                             country_sel or selected_countries,
                             segment)

    # ✅ comparison
    if ("compare" in q or "vs" in q) and len(brands)>=2:
        if metric:
            res=[f"{b}: {get_kpi(brand_map[b],metric,temp_where)}%" for b in brands[:2]]
            return "Comparison ("+metric+") → " + " | ".join(res)
        if attr:
            res=[]
            for b in brands[:2]:
                val=get_metric(f"Attributes_New_DP_{brand_map[b]}_Q12a_{attr}_slice")
                res.append(f"{b}: {val}%")
            return f"Comparison (Attribute: {attr_map[attr]}) → "+" | ".join(res)

    # ✅ top
    if "top" in q or "highest" in q:
        if metric:
            res=[(b,get_kpi(brand_map[b],metric,temp_where)) for b in brand_map]
            t=max(res,key=lambda x:x[1])
            return f"Top brand for {metric} → {t[0]} ({t[1]}%)"

    # ✅ attribute
    if not metric and attr:
        val=get_metric(f"Attributes_New_DP_{brand_map[brands[0]]}_Q12a_{attr}_slice")
        return f"{brands[0]} attribute \"{attr_map[attr]}\" is {val}%"

    # ✅ trend
    if "trend" in q:
        return f"Check Graph tab for trend of {brands[0]}"

    # ✅ KPI
    if metric:
        val=get_kpi(brand_map[brands[0]],metric,temp_where)
        return f"{brands[0]} {metric} is {val}%"

    return "Try KPI, attribute, comparison or trend questions."

# -----------------------------
tab1,tab2,tab3=st.tabs(["📊 Dashboard","📈 Graphs","🤖 Chatbot"])

# -----------------------------
with tab1:
    c1,c2,c3,c4=st.columns(4)
    selected_countries=c1.multiselect("Country",countries)
    selected_months=c2.multiselect("Month",months)
    segment=c3.selectbox("Segment",["Total","Male","Female"])
    selected_brand=c4.selectbox("Brand",list(brand_map.keys()))
    code=brand_map[selected_brand]

    where_clause=build_where(selected_months,selected_countries,segment)
    weight_col="Weight_Post" if len(selected_countries)==1 else "Global_weight_Stacked"

    m1,m2,m3,m4=st.columns(4)
    m1.metric("Awareness",f"{get_metric(f'Aided_Awareness_{code}_slice','yesno')}%")
    m2.metric("Favorability",f"{get_metric(f'Brand_Favorability_{code}_slice')}%")
    m3.metric("Consideration",f"{get_metric(f'Consideration_{code}_slice')}%")
    m4.metric("Effect",f"{get_metric(f'Consideration_Effect_{code}_slice')}%")

# -----------------------------
with tab2:
    g1,g2,g3,g4=st.columns(4)
    g_country=g1.multiselect("Country",countries,key="g_country")
    g_months=g2.multiselect("Month",months,key="g_months")
    g_segment=g3.selectbox("Segment",["Total","Male","Female"],key="g_segment")
    selected_brands=g4.multiselect("Brands",list(brand_map.keys()),default=list(brand_map.keys())[:3])

    view_type=st.radio("View Type",["Trended View","Brand Comparison"],horizontal=True)

    graph_where=build_where(g_months,g_country,g_segment)

    queries=[]
    for b in selected_brands:
        code=brand_map[b]
        queries.append(f"""
        SELECT Month,'{b}' AS Brand,
        SUM(CASE WHEN LOWER(TRIM(Aided_Awareness_{code}_slice))='yes'
        THEN Global_weight_Stacked ELSE 0 END)*100.0 /
        SUM(Global_weight_Stacked) AS Value
        FROM df {graph_where}
        GROUP BY Month
        """)

    df_chart=con.execute(" UNION ALL ".join(queries)).df()
    df_chart["Month_order"]=pd.Categorical(df_chart["Month"],categories=months,ordered=True)

    if view_type=="Trended View":
        chart=alt.Chart(df_chart).mark_line(point=True).encode(
            x="Month_order:O",y="Value:Q",color="Brand")
    else:
        chart=alt.Chart(df_chart).mark_line(point=True).encode(
            x="Brand",y="Value:Q",color="Month")

    st.altair_chart(chart,use_container_width=True)

# -----------------------------
with tab3:
    q=st.text_input("Ask KPI Questions")
    if q:
        st.success(local_chatbot(q))
