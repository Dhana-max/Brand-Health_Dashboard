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
    1:"Helps me move forward professionally",
    2:"Helps me find the right job for me",
    3:"Helps me navigate my professional life",
    4:"Is a place I feel I belong",
    5:"Cares about issues that matter to me",
    6:"Is a brand I love",
    7:"Is a brand I trust",
    8:"Makes me feel like I'm part of a community",
    9:"Helps me stay informed on professional topics",
    10:"Work-related discussions happen",
    11:"Useful daily",
    12:"Create/share content",
    13:"Increased content usage",
    14:"Used for job",
    15:"Helps reach goals",
    16:"Local relevance",
    17:"Helps business growth"
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
            SUM(Global_weight_Stacked)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0,1)
    except:
        return 0

# -----------------------------
# ✅ CHATBOT HELPERS

def find_metric(q):
    keys=["awareness","favorability","favourability","consideration","effect"]
    for k in keys:
        if k in q:
            return "favorability" if "favor" in k else k
    m=get_close_matches(q,keys,1,0.5)
    return ("favorability" if "favor" in m[0] else m[0]) if m else None

def find_brands(q):
    found=[b for b in brand_map if b.lower() in q]
    if not found:
        for w in q.split():
            m=get_close_matches(w,list(brand_map.keys()),1,0.6)
            if m:
                found.append(m[0])
    return list(set(found))

def find_month(q):
    for m in months:
        if m.lower() in q:
            return [m]
    return None

def find_country(q):
    for c in countries:
        if c.lower() in q:
            return [c]
    return None

def find_segment(q):
    if "male" in q:
        return "Male"
    elif "female" in q:
        return "Female"
    return "Total"

def find_attribute(q):
    best=None;score=0
    for i,t in attr_map.items():
        s=len(set(q.split())&set(t.lower().split()))
        if s>score:
            best=i;score=s
    return best

# -----------------------------
def get_kpi(code,metric,where):
    col=f"Aided_Awareness_{code}_slice"
    formula=f"LOWER(TRIM({col}))='yes'"
    q=f"""
    SELECT SUM(CASE WHEN {formula}
    THEN Global_weight_Stacked ELSE 0 END)/SUM(Global_weight_Stacked)*100
    FROM df {where}
    """
    return round(con.execute(q).fetchone()[0] or 0,1)

# -----------------------------
def get_prev_month(m):
    if m and m[0] in months:
        i=months.index(m[0])
        if i>0: return [months[i-1]]
    return None

def get_last_year(m):
    if m:
        parts=m[0].split()
        if len(parts)==2:
            try:
                y=str(int(parts[1])-1)
                t=f"{parts[0]} {y}"
                if t in months: return [t]
            except: pass
    return None

# -----------------------------
def local_chatbot(query):

    q=query.lower()

    brands=find_brands(q)
    metric=find_metric(q)
    attr=find_attribute(q)
    month=find_month(q)
    country=find_country(q)
    seg=find_segment(q)

    if not brands:
        return "Please mention a valid brand."

    temp_where=build_where(month or selected_months,
                           country or selected_countries,
                           seg)

    # ✅ comparison
    if ("compare" in q or "vs" in q) and len(brands)>=2:
        if metric:
            v1=get_kpi(brand_map[brands[0]],metric,temp_where)
            v2=get_kpi(brand_map[brands[1]],metric,temp_where)
            diff=round(v1-v2,1)
            leader=brands[0] if diff>=0 else brands[1]

            return f"{brands[0]}: {v1}% | {brands[1]}: {v2}%\n✅ {leader} leads by {abs(diff)}% ({seg})"

    # ✅ KPI with wave + segment
    if metric:
        curr=get_kpi(brand_map[brands[0]],metric,temp_where)

        insight=""

        pm=get_prev_month(month)
        ly=get_last_year(month)

        if pm:
            prev=build_where(pm,country or selected_countries,seg)
            v=get_kpi(brand_map[brands[0]],metric,prev)
            d=round(curr-v,1)
            insight+=f"\n• vs {pm[0]}: {d}% {'📈' if d>0 else '📉'}"

        if ly:
            prev=build_where(ly,country or selected_countries,seg)
            v=get_kpi(brand_map[brands[0]],metric,prev)
            d=round(curr-v,1)
            insight+=f"\n• vs {ly[0]}: {d}% {'📈' if d>0 else '📉'}"

        return f"{brands[0]} {metric} ({seg}) is {curr}%\n📊 Insights:{insight}"

    # ✅ attribute
    if attr:
        val=get_metric(f"Attributes_New_DP_{brand_map[brands[0]]}_Q12a_{attr}_slice")
        return f"{brands[0]} ({seg}) attribute '{attr_map[attr]}' is {val}%"

    return "Ask KPI, comparison, attribute, trend"
