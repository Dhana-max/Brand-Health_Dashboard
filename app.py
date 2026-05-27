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
def run_with_filters(month_sel, country_sel, seg, func):
    global where_clause, weight_col

    old_where = where_clause
    old_weight = weight_col

    temp_where = build_where(month_sel, country_sel, seg)
    temp_weight = "Weight_Post" if country_sel and len(country_sel)==1 else "Global_weight_Stacked"

    where_clause = temp_where
    weight_col = temp_weight

    result = func()

    where_clause = old_where
    weight_col = old_weight

    return result

# -----------------------------
# ✅ FINAL CHATBOT

def local_chatbot(query):

    q = query.lower()

    brands = [b for b in brand_map if b.lower() in q]

    if not brands:
        return "Please mention a valid brand."

    # ✅ Comparison
    if ("compare" in q or "vs" in q) and len(brands) >= 2:

        b1, b2 = brands[0], brands[1]

        v1 = get_metric(f"Aided_Awareness_{brand_map[b1]}_slice","yesno")
        v2 = get_metric(f"Aided_Awareness_{brand_map[b2]}_slice","yesno")

        diff = round(v1 - v2, 1)
        leader = b1 if diff >= 0 else b2

        return f"{b1}: {v1}% | {b2}: {v2}%\n✅ {leader} leads by {abs(diff)}%"

    brand = brands[0]

    # ✅ Month detection (flexible)
    selected_month = None
    for m in months:
        if m.lower() in q or m.lower().replace(" ", "") in q:
            selected_month = m
            break

    # ✅ Trend with month → MoM + YoY
    if "trend" in q and selected_month:

        idx = months.index(selected_month)

        current = run_with_filters([selected_month], selected_countries, segment, lambda:
            get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
        )

        output = f"{brand} awareness in {selected_month} is {current}%\n\n📊 Insights:"

        # MoM
        if idx > 0:
            prev = months[idx-1]
            prev_val = run_with_filters([prev], selected_countries, segment, lambda:
                get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
            )
            diff = round(current - prev_val,1)
            output += f"\n• vs {prev}: {diff}% {'📈' if diff>0 else '📉'}"

        # YoY
        parts = selected_month.split()
        if len(parts)==2:
            yoy = f"{parts[0]} {int(parts[1])-1}"
            if yoy in months:
                yoy_val = run_with_filters([yoy], selected_countries, segment, lambda:
                    get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
                )
                diff = round(current - yoy_val,1)
                output += f"\n• vs {yoy}: {diff}% {'📈' if diff>0 else '📉'}"

        return output

    # ✅ Trend full
    if "trend" in q:

        trend_data = []

        for m in months:
            val = run_with_filters([m], selected_countries, segment, lambda:
                get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
            )
            trend_data.append(f"{m}: {val}%")

        return f"Trend for {brand} (Awareness):\n\n" + "\n".join(trend_data[:8])

    # ✅ KPI
    if "awareness" in q:
        val = get_metric(f"Aided_Awareness_{brand_map[brand]}_slice","yesno")
        return f"{brand} awareness is {val}%"

    if "favor" in q:
        val = get_metric(f"Brand_Favorability_{brand_map[brand]}_slice")
        return f"{brand} favorability is {val}%"

    return "Try: LinkedIn awareness or trend linkedin or compare linkedin vs indeed"
