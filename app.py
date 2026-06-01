import streamlit as st
import duckdb
import pandas as pd
import re
import altair as alt

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #ffffff !important;
    }
    .client-kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .client-kpi-value {
        font-size: 34px;
        font-weight: 700;
        color: #212529;
        margin-bottom: 8px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Consumer Brand Tracker Dashboard")

PARQUET_URL = "https://github.com/Dhana-max/Brand-Health_Dashboard/releases/download/v1/data.parquet"
MAP_FILE = "Map.xlsx"

@st.cache_resource
def get_connection():
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW df AS 
        SELECT * FROM read_parquet('{PARQUET_URL}')
    """)
    return con

con = get_connection()

@st.cache_data
def load_map():
    df = pd.read_excel(MAP_FILE, header=1)
    df.columns = df.columns.astype(str).str.strip()
    return df

map_df = load_map()

# ✅ FIX APPLIED HERE
@st.cache_data
def load_filters():
    # Preserve dataset month order explicitly
    df_temp = con.execute("""
        SELECT DISTINCT Month 
        FROM df 
        WHERE Month IS NOT NULL 
        ORDER BY Month
    """).df()
    months_list = [str(x) for x in df_temp["Month"].tolist()]
    
    df_country = con.execute("""
        SELECT DISTINCT Country_New 
        FROM df 
        WHERE Country_New IS NOT NULL
    """).df()
    countries_list = [str(x) for x in df_country["Country_New"].dropna().tolist()]
    
    return months_list, countries_list

months, countries = load_filters()

brand_rows = map_df[map_df["Variable"].astype(str).str.contains("Aided_Awareness_", na=False)]
brand_map = {}
for _, r in brand_rows.iterrows():
    lbl = str(r["Label"]).split(" - ")[-1].strip()
    match = re.findall(r"\d+", str(r["Variable"]))
    if match:
        brand_map[lbl] = int(match[0])

if not brand_map:
    brand_map = {"Default Brand": 1}

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
            
        q = f"SELECT {col}, {weight_col} FROM df {where_clause}"
        local_df = con.execute(q).df()
        if local_df.empty: return 0.0
        local_df.columns = ['target_col', 'weight_col']
        
        if metric_type == "yesno":
            yes_mask = local_df['target_col'].astype(str).str.lower().str.strip() == 'yes'
            total_w = local_df['weight_col'].sum()
            return round((local_df.loc[yes_mask, 'weight_col'].sum() * 100.0) / total_w, 1) if total_w > 0 else 0.0
        else:
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
            agg = local_df.groupby('Month').apply(
                lambda g: (g.loc[g['is_match'], 'weight_col'].sum() * 100.0) / g['weight_col'].sum()
            )
        else:
            local_df['parsed_val'] = local_df['target_col'].apply(extract_num)
            local_df['is_valid'] = local_df['parsed_val'].between(1, 5)
            local_df['is_top2'] = local_df['parsed_val'].isin([4, 5])
            agg = local_df.groupby('Month').apply(
                lambda g: (g.loc[g['is_top2'], 'weight_col'].sum() * 100.0) /
                          g.loc[g['is_valid'], 'weight_col'].sum()
            )

        res_df = agg.reset_index()
        res_df.columns = ['Month', 'val']

        # ✅ Force ordering
        res_df["Month"] = pd.Categorical(res_df["Month"], categories=months, ordered=True)
        return res_df.sort_values("Month").fillna(0.0)

    except:
        return dummy_df

def create_sparkline_chart(df, color_line):
    return alt.Chart(df).mark_line(
        interpolate='monotone', strokeWidth=3, color=color_line
    ).encode(
        x=alt.X('Month:O', title=None, axis=None, sort=months),  # ✅ enforce order
        y=alt.Y('val:Q', title=None, axis=None, scale=alt.Scale(zero=False))
    ).properties(height=50).configure(background='transparent').configure_view(strokeOpacity=0)

# ✅ remaining code stays EXACTLY SAME (no other change)
