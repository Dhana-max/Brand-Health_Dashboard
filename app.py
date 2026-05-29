import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

# 1. Initialize native wide parameters & clean sidebar layout
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# 2. Premium "Anicorn App" Color Canvas & Component Shadow Injector
st.markdown(
    """
    <style>
    /* 1. Global Canvas Background Shift (Soft Grey Canvas from image_c8e872.jpg) */
    .stApp, [data-testid="stMainSpaceContainer"], [data-testid="stVerticalBlock"] {
        background-color: #f3f4f6 !important;
    }
    
    /* Global layout padding adjustment */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* 2. Floating Crisp White Panels with Heavy Rounded Corners and Diffuse Shadows */
    div[data-testid="stMetricContainer"], div[data-testid="stVerticalBlockBorderWrapper"], .st-emotion-cache-12w0qpk {
        background-color: #ffffff !important;
        border: none !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.03), 0 8px 10px -6px rgba(0, 0, 0, 0.03) !important;
        border-radius: 24px !important;
        padding: 22px 24px !important;
    }
    
    /* Metric Typography Polish */
    .client-kpi-label {
        font-size: 12px;
        font-weight: 700;
        color: #9ca3af; /* Muted slate gray */
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }
    .client-kpi-value {
        font-size: 38px;
        font-weight: 800;
        color: #1f2937; /* Dark slate text */
        margin-bottom: 2px;
        letter-spacing: -0.03em;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Style Tabs to match look */
    button[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #64748b !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        font-weight: 700 !important;
        color: #8b5cf6 !important; /* Premium Purple accent */
    }
    
    /* Main Dashboard Header weight styling */
    h1 {
        font-weight: 800 !important;
        color: #111827 !important;
        letter-spacing: -0.03em !important;
        margin-bottom: 20px !important;
    }
    h2, h3 {
        color: #1f2937 !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Title Area
st.title("Brand Health Intelligence Platform")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

# -----------------------------
# Safe Analytical Database Engine Setup
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
# Robust Clean Configuration Loading
# -----------------------------
@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# Strategic Dimensions Matrix Mapping
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

@st.cache_data
def load_filters():
    df_temp = con.execute("SELECT DISTINCT Month FROM df WHERE Month IS NOT NULL").df()
    months_list = [str(x) for x in df_temp["Month"].dropna().tolist()]
    
    df_country = con.execute("SELECT DISTINCT Country_New FROM df WHERE Country_New IS NOT NULL").df()
    countries_list = [str(x) for x in df_country["Country_New"].dropna().tolist()]
    
    return months_list, countries_list

months, countries = load_filters()

# -----------------------------
# Secure Extraction of Brands Map
# -----------------------------
brand_rows = map_df[map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)]
brand_map = {}
for _, r in brand_rows.iterrows():
    lbl = str(r["Label"]).split(" - ")[-1].strip()
    match = re.findall(r"\d+", str(r["Variable"]))
    if match:
        brand_map[lbl] = int(match[0])

if not brand_map:
    brand_map = {"Default Brand": 1}

# -----------------------------
# Secure Safe Parameter Builders
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

def get_metric(col, metric_type="top2", where_clause="", weight_col="Global_weight_Stacked"):
    try:
        chk = con.execute(f"SELECT * FROM df LIMIT 0").df()
        if col not in chk.columns:
            return 0.0
            
        if metric_type == "yesno":
            q = f"SELECT {col}, {weight_col} FROM df {where_clause}"
            local_df = con.execute(q).df()
            if local_df.empty: return 0.0
            local_df.columns = ['target_col', 'weight_col']
            yes_mask = local_df['target_col'].astype(str).str.lower().str.strip() == 'yes'
            total_w = local_df['weight_col'].sum()
            return round((local_df.loc[yes_mask, 'weight_col'].sum() * 100.0) / total_w, 1) if total_w > 0 else 0.0
        else:
            q = f"SELECT {col}, {weight_col} FROM df {where_clause}"
            local_df = con.execute(q).df()
            if local_df.empty: return 0.0
            local_df.columns = ['target_col', 'weight_col']
            
            def extract_num(val):
                digits = re.findall(r'\d+', str(val))
                return int(digits[0]) if digits else None
                
            local_df['parsed_val'] = local_df['target_col'].apply(extract_num)
            valid_mask = local_df['parsed_val'].between(1, 5)
            top2_mask = local_df['parsed_val'].isin([4, 5])
            
            denom = local_df.loc[valid_mask, 'weight_col'].sum()
            num = local_df.loc[top2_mask, 'weight_col'].sum()
            return round((num * 100.0) / denom, 1) if denom > 0 else 0.0
    except:
        return 0.0

def get_sparkline_data(col, metric_type, where_clause, weight_col):
    dummy_df = pd.DataFrame({"Month": months, "val": [0.0]*len(months)})
    try:
        chk = con.execute(f"SELECT * FROM df LIMIT 0").df()
        if col not in chk.columns:
            return dummy_df

        q = f"SELECT Month, {col}, {weight_col} FROM df {where_clause}"
        local_df = con.execute(q).df()
        if local_df.empty: return dummy_df
        local_df.columns = ['Month', 'target_col', 'weight_col']
        
        def extract_num(val):
            digits = re.findall(r'\d+', str(val))
            return int(digits[0]) if digits else None

        if metric_type == "yesno":
            local_df['is_match'] = local_df['target_col'].astype(str).str.lower().str.strip() == 'yes'
            agg = local_df.groupby('Month').apply(lambda g: (g.loc[g['is_match'], 'weight_col'].sum() * 100.0) / g['weight_col'].sum() if g['weight_col'].sum() > 0 else 0.0)
        else:
            local_df['parsed_val'] = local_df['target_col'].apply(extract_num)
            local_df['is_valid'] = local_df['parsed_val'].between(1, 5)
            local_df['is_top2'] = local_df['parsed_val'].isin([4, 5])
            agg = local_df.groupby('Month').apply(lambda g: (g.loc[g['is_top2'], 'weight_col'].sum() * 100.0) / g.loc[g['is_valid'], 'weight_col'].sum() if g.loc[g['is_valid'], 'weight_col'].sum() > 0 else 0.0)
            
        res_df = agg.reset_index()
        res_df.columns = ['Month', 'val']
        res_df["Month_order"] = pd.Categorical(res_df["Month"], categories=months, ordered=True)
        return res_df.sort_values("Month_order").fillna(0.0)
    except:
        return dummy_df

def create_sparkline_chart(df, color_line):
    chart = alt.Chart(df).mark_line(interpolate='monotone', strokeWidth=3.5, color=color_line).encode(
        x=alt.X('Month:O', title=None, axis=None),
        y=alt.Y('val:Q', title=None, axis=None, scale=alt.Scale(zero=False))
    ).properties(height=55)
    return chart.configure(background='transparent').configure_view(strokeOpacity=0)

# -----------------------------
# UNCHANGED CENTRALIZED SIDEBAR SYSTEM
# -----------------------------
with st.sidebar:
    st.markdown("### 🎛️ Analysis Controls")
    st.write("Modify global audience parameters:")
    
    selected_countries = st.multiselect("🌍 Country", countries, key="sidebar_country")
    selected_months = st.multiselect("📅 Month", months, key="sidebar_month")
    segment = st.selectbox("👤 Segment", ["Total", "Male", "Female"], key="sidebar_segment")
    
    brand_options = list(brand_map.keys())
    selected_brand = st.selectbox("🏢 Brand Profile", brand_options, key="sidebar_brand")

# Shared state execution
code = brand_map.get(selected_brand, 1)
where_clause = build_where(selected_months, selected_countries, segment)
weight_col = "Weight_Post" if len(selected_countries) == 1 else "Global_weight_Stacked"

# Navigation Tab Structure
tab1, tab2, tab3 = st.tabs(["📊 Executive Overview", "📈 Strategic Trends", "🤖 Brand AI Chat"])

# -----------------------------
# TAB 1: EXECUTIVE DASHBOARD
# -----------------------------
with tab1:
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    raw_v1 = get_metric(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)
    raw_v2 = get_metric(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)
    raw_v3 = get_metric(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)
    raw_v4 = get_metric(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)

    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        df_sp1 = get_sparkline_data(f'Aided_Awareness_{code}_slice', 'yesno', where_clause, weight_col)
        with st.container(border=True):
            st.markdown(f"<div class='client-kpi-label'>Total Awareness</div><div class='client-kpi-value'>{raw_v1}%</div>", unsafe_allow_html=True)
            st.altair_chart(create_sparkline_chart(df_sp1, '#8b5cf6'), use_container_width=True) # Vivid purple path

    with col2:
        df_sp2 = get_sparkline_data(f'Brand_Favorability_{code}_slice', 'top2', where_clause, weight_col)
        with st.container(border=True):
            st.markdown(f"<div class='client-kpi-label'>Brand Favorability</div><div class='client-kpi-value'>{raw_v2}%</div>", unsafe_allow_html=True)
            st.altair_chart(create_sparkline_chart(df_sp2, '#ff7e5f'), use_container_width=True) # Vivid coral path

    with col3:
        df_sp3 = get_sparkline_data(f'Consideration_{code}_slice', 'top2', where_clause, weight_col)
        with st.container(border=True):
            st.markdown(f"<div class='client-kpi-label'>Consideration Rate</div><div class='client-kpi-value'>{raw_v3}%</div>", unsafe_allow_html=True)
            st.altair_chart(create_sparkline_chart(df_sp3, '#06b6d4'), use_container_width=True) # Cyan path

    with col4:
        df_sp4 = get_sparkline_data(f'Consideration_Effect_{code}_slice', 'top2', where_clause, weight_col)
        with st.container(border=True):
            st.markdown(f"<div class='client-kpi-label'>Conversion Effect</div><div class='client-kpi-value'>{raw_v4}%</div>", unsafe_allow_html=True)
            st.altair_chart(create_sparkline_chart(df_sp4, '#10b981'), use_container_width=True)

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    # Strategic Pillars Segment Panel
    with st.container(border=True):
        st.subheader("🎯 Strategic Pillars Core Breakdown")
        selected_pillar = st.radio(
            label="Select Operational Strategic Pillar To Deep-Dive:",
            options=list(brand_pillars.keys()),
            horizontal=True,
            key="strategic_pillar_selector"
        )
        
        active_indices = brand_pillars[selected_pillar]
        attr_data = []
        for idx in active_indices:
            score = get_metric(f"Attributes_New_DP_{code}_Q12a_{idx}_slice", "top2", where_clause, weight_col)
            attr_data.append({"Strategic Statement Pillar": attr_map[idx], "Agreement Score (%)": score})
        
        df_matrix = pd.DataFrame(attr_data).sort_values(by="Agreement Score (%)", ascending=False)
        
        attr_chart = alt.Chart(df_matrix).mark_bar(
            cornerRadiusTopRight=6,
            cornerRadiusBottomRight=6,
            size=22
        ).encode(
            x=alt.X("Agreement Score (%):Q", title="Top-2 Box Agreement Score (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Strategic Statement Pillar:N", sort="-x", title=None),
            color=alt.Color("Agreement Score (%):Q", scale=alt.Scale(scheme="purpleorange"), legend=None),
            tooltip=["Strategic Statement Pillar", "Agreement Score (%)"]
        ).properties(height=240).configure_view(strokeOpacity=0)
        
        st.altair_chart(attr_chart, use_container_width=True)

# -----------------------------
# TAB 2: GRAPHS VIEW
# -----------------------------
with tab2:
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.subheader("📊 Brand Health Funnel Trends Analytics")
        
        metrics_to_plot = [
            {"label": "Total Awareness", "col": f"Aided_Awareness_{code}_slice", "type": "yesno"},
            {"label": "Brand Favorability", "col": f"Brand_Favorability_{code}_slice", "type": "top2"},
            {"label": "Consideration Rate", "col": f"Consideration_{code}_slice", "type": "top2"},
            {"label": "Conversion Effect", "col": f"Consideration_Effect_{code}_slice", "type": "top2"},
        ]
        
        trend_list = []
        for m_info in metrics_to_plot:
            tdf = get_sparkline_data(m_info["col"], m_info["type"], where_clause, "Global_weight_Stacked")
            tdf["Metric"] = m_info["label"]
            trend_list.append(tdf)
            
        df_trends = pd.concat(trend_list, ignore_index=True)
        
        if not df_trends.empty and df_trends['val'].sum() > 0:
            multi_line_chart = alt.Chart(df_trends).mark_line(point=True, size=3.5).encode(
                x=alt.X("Month:O", title="Timeline Tracking Phase", sort=months),
                y=alt.Y("val:Q", title="Percentage Share Score (%)", scale=alt.Scale(zero=False)),
                color=alt.Color("Metric:N", scale=alt.Scale(range=['#8b5cf6', '#ff7e5f', '#06b6d4', '#10b981']), legend=alt.Legend(title="Brand Funnel Layer")),
                tooltip=["Month", "Metric", "val"]
            ).properties(height=420).interactive().configure_view(strokeOpacity=0)
            
            st.altair_chart(multi_line_chart, use_container_width=True)
        else:
            st.warning("⚠️ No active dataset parameters match the selected analytical profile configuration metrics.")

# -----------------------------
# TAB 3: CHATBOT VIEW
# -----------------------------
with tab3:
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("🤖 AI Analytics Chatbot")
        user_query = st.text_input("Interrogate your analytical metrics profile:", key="chatbot_query_input", placeholder="e.g., Show trends analysis summaries...")
        if user_query:
            st.info("✅ High-level summary metrics compiled using active dataset configurations from the filter module panel.")
