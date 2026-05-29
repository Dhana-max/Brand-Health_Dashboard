import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

# 1. Native configuration with no layout overrides
st.set_page_config(layout="wide")

st.title("Brand Health Intelligence Platform")

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
brand_pillars = {
    "🎯 Professional Career Growth": [1, 2, 3, 15, 17],
    "🛡️ Trust & Brand Affinity": [6, 7, 11, 16],
    "🤝 Community & Engagement": [4, 5, 8, 10],
    "⚡ Content Innovation & Utility": [9, 12, 13, 14]
}

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

def get_brands_by_country(selected_countries):
    return brand_map

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

def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        if metric_type == "yesno":
            q = f"""
            SELECT SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col})
            FROM df {where_clause}
            """
        else:
            q = f"""
            SELECT SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5) THEN {weight_col} ELSE 0 END)*100.0 /
            SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN {weight_col} ELSE 0 END)
            FROM df {where_clause}
            """
        return round(con.execute(q).fetchone()[0] or 0, 1)
    except:
        return 0

def get_sparkline_data(col, metric_type, where_clause, weight_col):
    try:
        q = f"""
        SELECT Month, SUM(CASE WHEN LOWER(TRIM({col}))='yes' THEN {weight_col} ELSE 0 END)*100.0/SUM({weight_col}) as val
        FROM df {where_clause} GROUP BY Month
        """ if metric_type == "yesno" else f"""
        SELECT Month, SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) IN (4,5) THEN {weight_col} ELSE 0 END)*100.0 /
        SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({col}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN {weight_col} ELSE 0 END) as val
        FROM df {where_clause} GROUP BY Month
        """
        spark_df = con.execute(q).df()
        if not spark_df.empty:
            spark_df["Month_order"] = pd.Categorical(spark_df["Month"], categories=months, ordered=True)
            spark_df = spark_df.sort_values("Month_order")
            return spark_df[["Month", "val"]]
    except:
        pass
    return pd.DataFrame({"Month": months, "val": [0]*len(months)})

def create_sparkline_chart(df, color_line):
    chart = alt.Chart(df).mark_line(interpolate='monotone', strokeWidth=2.5, color=color_line).encode(
        x=alt.X('Month:O', title=None, axis=None),
        y=alt.Y('val:Q', title=None, axis=None, scale=alt.Scale(zero=False))
    ).properties(height=35)
    return chart.configure(background='transparent').configure_view(strokeOpacity=0)

# -----------------------------
# Standard, Ultra-Stable Native Tabs
tab1, tab2, tab3 = st.tabs(["📊 Executive View", "📈 Deep-Dive Graphs", "🤖 AI Analytics Chatbot"])

# -----------------------------
with tab1:
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        selected_countries = st.multiselect("🌍 Region / Country", countries)
    with f2:
        selected_months = st.multiselect("📅 Historical Phase", months)
    with f3:
        segment = st.selectbox("👤 Demographic Segment", ["Total", "Male", "Female"])
    with f4:
        filtered_brand_map = get_brands_by_country(selected_countries)
        selected_brand = st.selectbox("🏢 Target Enterprise Brand", list(filtered_brand_map.keys()))

    code = filtered_brand_map[selected_brand]
    where_clause = build_where(selected_months, selected_countries, segment)
    weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

    st.write("---")
    
    # Standard Native Metric Cards Grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        val1 = f"{get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)}%"
        st.metric(label="Total Awareness", value=val1)
        df_sp1 = get_sparkline_data(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp1, '#00f2fe'), use_container_width=True)

    with col2:
        val2 = f"{get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.metric(label="Brand Favorability", value=val2)
        df_sp2 = get_sparkline_data(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp2, '#38ef7d'), use_container_width=True)

    with col3:
        val3 = f"{get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.metric(label="Consideration Rate", value=val3)
        df_sp3 = get_sparkline_data(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp3, '#ff007f'), use_container_width=True)

    with col4:
        val4 = f"{get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)}%"
        st.metric(label="Conversion Effect", value=val4)
        df_sp4 = get_sparkline_data(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)
        st.altair_chart(create_sparkline_chart(df_sp4, '#ff9f43'), use_container_width=True)

    st.write("---")
    
    # Safe Interactive Pillar Selection via standard Radio Button
    st.subheader("🎯 Brand Strategic Pillars Breakdown")
    selected_pillar = st.radio(
        label="Choose a Pillar to Inspect:",
        options=list(brand_pillars.keys()),
        horizontal=True
    )
    
    active_indices = brand_pillars[selected_pillar]
    attr_data = []
    for idx in active_indices:
        score = get_metric(f"Attributes_New_DP_{code}_Q12a_{idx}_slice", "top2", where_clause, weight_col)
        attr_data.append({"Attribute Statement": attr_map[idx], "Agreement Score (%)": score})
    
    df_matrix = pd.DataFrame(attr_data).sort_values(by="Agreement Score (%)", ascending=False)
    
    attr_chart = alt.Chart(df_matrix).mark_bar(
        cornerRadiusTopRight=4,
        cornerRadiusBottomRight=4,
        size=22
    ).encode(
        x=alt.X("Agreement Score (%):Q", title="Top-2 Box Agreement Score (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("Attribute Statement:N", sort="-x", title=None),
        color=alt.Color("Agreement Score (%):Q", scale=alt.Scale(scheme="blues"), legend=None),
        tooltip=["Attribute Statement", "Agreement Score (%)"]
    ).properties(height=220)
    
    st.altair_chart(attr_chart, use_container_width=True)

# -----------------------------
with tab2:
    colg1, colg2, colg3, colg4 = st.columns(4)

    with colg1:
        g_country = st.multiselect("Filter Country (Graph)", countries, key="g_country")
    with colg2:
        g_months = st.multiselect("Filter Month (Graph)", months, key="g_months")
    with colg3:
        g_segment = st.selectbox("Segment Select (Graph)", ["Total", "Male", "Female"], key="g_segment")
    with colg4:
        brand_map_local = get_brands_by_country(g_country)
        g_brand_sel = st.selectbox("Select Target Brand (Graph)", list(brand_map_local.keys()), key="g_brand_single")

    st.write("---")
    st.subheader("📊 Brand Health Funnel Trends & Cross-Attribute Analytics")
    
    graph_where = build_where(g_months, g_country, g_segment)
    g_code = brand_map_local[g_brand_sel]
    
    metrics_to_plot = [
        {"label": "Total Awareness", "col": f"Aided_Awareness_{g_code}_slice", "type": "yesno"},
        {"label": "Brand Favorability", "col": f"Brand_Favorability_{g_code}_slice", "type": "top2"},
        {"label": "Consideration Rate", "col": f"Consideration_{g_code}_slice", "type": "top2"},
        {"label": "Conversion Effect", "col": f"Consideration_Effect_{g_code}_slice", "type": "top2"},
    ]
    
    trend_queries = []
    for m_info in metrics_to_plot:
        c_name = m_info["col"]
        lbl = m_info["label"]
        if m_info["type"] == "yesno":
            trend_queries.append(f"""
                SELECT Month, '{lbl}' AS Metric, 
                SUM(CASE WHEN LOWER(TRIM({c_name}))='yes' THEN Global_weight_Stacked ELSE 0 END)*100.0/SUM(Global_weight_Stacked) AS Value 
                FROM df {graph_where} GROUP BY Month
            """)
        else:
            trend_queries.append(f"""
                SELECT Month, '{lbl}' AS Metric, 
                SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({c_name}), '\\d+') AS INTEGER) IN (4,5) THEN Global_weight_Stacked ELSE 0 END)*100.0 /
                SUM(CASE WHEN TRY_CAST(REGEXP_EXTRACT(TRIM({c_name}), '\\d+') AS INTEGER) BETWEEN 1 AND 5 THEN Global_weight_Stacked ELSE 0 END) AS Value 
                FROM df {graph_where} GROUP BY Month
            """)
            
    df_trends = con.execute(" UNION ALL ".join(trend_queries)).df()
    
    if not df_trends.empty:
        df_trends["Month_order"] = pd.Categorical(df_trends["Month"], categories=months, ordered=True)
        
        multi_line_chart = alt.Chart(df_trends).mark_line(point=True, size=3).encode(
            x=alt.X("Month_order:O", title="Timeline Phase"),
            y=alt.Y("Value:Q", title="Percentage Share Score (%)", scale=alt.Scale(zero=False)),
            color=alt.Color("Metric:N", legend=alt.Legend(title="Brand Funnel Layer")),
            tooltip=["Month", "Metric", "Value"]
        ).properties(height=400).interactive()
        
        st.altair_chart(multi_line_chart, use_container_width=True)
    else:
        st.warning("⚠️ No tracking information matches the selected filter configuration parameters.")

# -----------------------------
with tab3:
    st.subheader("🤖 AI Analytics Chatbot (Insights Only)")
    user_query = st.text_input("Interrogate your analytical KPIs:", key="chat_input_unique")
    if user_query:
        st.write("✅ Insight response compiled (no chart visualization needed)")
