import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_theme
st.session_state["_page_key"] = "1_Upload"
apply_theme()

import pandas as pd
import numpy as np
import io

# ── CACHE ─────────────────────────────────────────────────────────────────────

@st.cache_data
def load_csv(b, name): return pd.read_csv(io.BytesIO(b))
@st.cache_data
def load_excel(b, name): return pd.read_excel(io.BytesIO(b))
@st.cache_data
def load_json(b, name): return pd.read_json(io.BytesIO(b))
@st.cache_data
def load_sheets(url): return pd.read_csv(url)

# ── SESSION INIT ──────────────────────────────────────────────────────────────
for k, v in [("df", None), ("log", []), ("history", []), ("last_file", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── HEADER ────────────────────────────────────────────────────────────────────
col_title, col_reset = st.columns([5, 1])
with col_title:
    st.title("📂 Upload & Data Profile")
with col_reset:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset All", type="secondary", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ── GOOGLE SHEETS ─────────────────────────────────────────────────────────────
with st.expander("🌐 Load from Google Sheets (Optional)", expanded=False):
    st.caption("Sheet must be shared as 'Anyone with the link can view'")
    sheet_url = st.text_input("Paste Google Sheets share link", key="gs_url")
    if st.button("Load Google Sheets") and sheet_url:
        try:
            if "/edit" in sheet_url:
                gid = sheet_url.split("gid=")[-1].split("&")[0].split("#")[0] if "gid=" in sheet_url else "0"
                base = sheet_url.split("/edit")[0]
                csv_url = f"{base}/export?format=csv&gid={gid}"
            else:
                csv_url = sheet_url
            df = load_sheets(csv_url)
            st.session_state.df = df
            st.session_state.history = [df.copy()]
            st.session_state.last_file = "google_sheets"
            st.session_state.log = ["Loaded from Google Sheets"]
            st.success(f"✅ Loaded {df.shape[0]:,} rows x {df.shape[1]} columns from Google Sheets")
        except Exception as e:
            st.error(f"Could not load sheet. Make sure it is publicly accessible. Error: {e}")

# ── SAMPLE DATASETS ───────────────────────────────────────────────────────────
with st.expander("🗂️ Try a Sample Dataset", expanded=False):
    st.markdown("Choose one of our ready-to-use datasets — each has 1,000+ rows, mixed types, coordinates, dates, and missing values.")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown("""
        **🛒 E-Commerce Orders**
        - 1,520 rows · 16 columns
        - Order dates (2022–2024)
        - Countries, categories, payment methods
        - Customer lat/lon coordinates
        - Revenue, discounts, review scores
        - Some missing values in rating & shipping
        - Duplicates
        """)
        if st.button("Load", use_container_width=True, key="sample_ecom"):
            import os
            sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "ecommerce_orders.csv")
            df = pd.read_csv(sample_path)
            st.session_state.df = df
            st.session_state.history = [df.copy()]
            st.session_state.last_file = "ecommerce_orders.csv"
            st.session_state.log = ["Sample dataset loaded: E-Commerce Orders"]
            st.rerun()
    with s2:
        st.markdown("""
        **🌫️ Air Quality Monitoring**
        - 2,100 rows · 15 columns
        - Timestamps every 6 hours (2020)
        - 10 global cities with coordinates
        - PM2.5, PM10, NO₂, O₃, AQI readings
        - Temperature, humidity, wind speed
        - Missing sensor readings
        - Duplicates
        """)
        if st.button("Load", use_container_width=True, key="sample_air"):
            import os
            sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "air_quality_monitoring.csv")
            df = pd.read_csv(sample_path)
            st.session_state.df = df
            st.session_state.history = [df.copy()]
            st.session_state.last_file = "air_quality_monitoring.csv"
            st.session_state.log = ["Sample dataset loaded: Air Quality Monitoring"]
            st.rerun()
    with s3:
        st.markdown("""
        **✈️ Global Flights**
        - 1,826 rows · 18 columns
        - Departure dates (2023–2024)
        - 8 airlines, 10 major airports
        - Origin & destination lat/lon coordinates
        - Prices, delays, passenger counts
        - Missing prices and delay data
        - Duplicates
        """)
        if st.button("Load", use_container_width=True, key="sample_flights"):
            import os
            sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data", "global_flights.csv")
            df = pd.read_csv(sample_path)
            st.session_state.df = df
            st.session_state.history = [df.copy()]
            st.session_state.last_file = "global_flights.csv"
            st.session_state.log = ["Sample dataset loaded: Global Flights"]
            st.rerun()

st.markdown("---")

# ── FILE UPLOAD ───────────────────────────────────────────────────────────────
file = st.file_uploader("📁 Upload your dataset", type=["csv", "xlsx", "json"],
                         help="CSV, Excel (.xlsx), or JSON")

if file is not None:
    try:
        b = file.read()
        if file.name.endswith(".csv"):    df = load_csv(b, file.name)
        elif file.name.endswith(".xlsx"): df = load_excel(b, file.name)
        elif file.name.endswith(".json"): df = load_json(b, file.name)
        else:
            st.error("Unsupported file type"); st.stop()

        if st.session_state.last_file != file.name or st.session_state.df is None:
            st.session_state.df = df
            st.session_state.history = [df.copy()]
            st.session_state.last_file = file.name
            st.session_state.log = [f"Dataset uploaded: {file.name}"]

        st.success(f"✅ **{file.name}** — {df.shape[0]:,} rows x {df.shape[1]} columns")
    except Exception as e:
        st.error(f"Error loading file: {e}"); st.stop()

if st.session_state.df is None:
    st.info("💡 Upload a file above or try one of the sample datasets from the `sample_data/` folder.")
    st.stop()

# ── OVERVIEW ──────────────────────────────────────────────────────────────────
df = st.session_state.df
st.subheader("📊 Dataset Overview")

total_missing = int(df.isnull().sum().sum())
total_cells   = df.shape[0] * df.shape[1]
missing_pct   = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0
dupes         = int(df.duplicated().sum())
dupes_pct     = round(dupes / df.shape[0] * 100, 2) if df.shape[0] > 0 else 0

# Separate metrics: Duplicates count and Duplicates % are now individual cards
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Rows",          f"{df.shape[0]:,}")
m2.metric("Columns",       df.shape[1])
m3.metric("Duplicates",    f"{dupes:,}")
m4.metric("Duplicates %",  f"{dupes_pct:.2f}%")
m5.metric("Missing Cells", f"{total_missing:,}")
m6.metric("Missing %",     f"{missing_pct:.2f}%")

st.markdown("---")
st.write("### Missing Values by Column")
mv = pd.DataFrame({
    "Missing Count": df.isnull().sum(),
    "Missing %": (df.isnull().sum() / len(df) * 100)
})
mv["Missing %"] = mv["Missing %"].map(lambda x: round(x, 2))
mv_f = mv[mv["Missing Count"] > 0]
if mv_f.empty:
    st.success("No missing values found!")
else:
    st.dataframe(mv_f.style.background_gradient(cmap="Reds", subset=["Missing %"])
                 .format({"Missing %": "{:.2f}"}),
                 use_container_width=True)

# ── DUPLICATES OVERVIEW TABLE ─────────────────────────────────────────────────
st.markdown("---")
st.write("### Duplicate Rows Overview")
if dupes == 0:
    st.success("No duplicate rows found!")
else:
    dup_mask = df.duplicated(keep=False)
    dup_df   = df[dup_mask].copy()
    # Add a group identifier for side-by-side comparison
    dup_df.insert(0, "_dup_group", df[dup_mask].apply(tuple, axis=1).rank(method="dense").astype(int))
    dup_df = dup_df.sort_values("_dup_group").reset_index(drop=False)
    dup_df = dup_df.rename(columns={"index": "_original_row"})
    st.info(f"Found **{dupes}** duplicate rows across **{dup_df['_dup_group'].nunique()}** groups. "
            "Rows in the same group are identical — review below before removing.")
    st.dataframe(dup_df, use_container_width=True)

st.markdown("---")
st.write("### Column Info")
info_df = pd.DataFrame({
    "Column":   df.columns,
    "Type":     df.dtypes.astype(str).values,
    "Non-Null": df.notnull().sum().values,
    "Unique":   [df[c].nunique() for c in df.columns],
    "Sample":   [str(df[c].dropna().iloc[0]) if not df[c].dropna().empty else "N/A" for c in df.columns]
}).reset_index(drop=True)
st.dataframe(info_df, use_container_width=True)

st.markdown("---")
st.write("### Summary Statistics")
# Numeric stats
num_cols_list = df.select_dtypes(include=np.number).columns.tolist()
cat_cols_list = df.select_dtypes(include=["object","category"]).columns.tolist()

if num_cols_list:
    st.markdown("**Numeric Columns**")
    num_desc = df[num_cols_list].describe().T
    num_desc.insert(0, "unique", [df[c].nunique() for c in num_cols_list])
    num_desc.insert(0, "missing", [int(df[c].isnull().sum()) for c in num_cols_list])
    st.dataframe(num_desc.style.format(precision=4), use_container_width=True)

if cat_cols_list:
    st.markdown("**Categorical Columns**")
    cat_rows = []
    for c in cat_cols_list:
        vc = df[c].value_counts()
        cat_rows.append({
            "column": c,
            "count": int(df[c].notnull().sum()),
            "missing": int(df[c].isnull().sum()),
            "unique": int(df[c].nunique()),
            "top": str(vc.index[0]) if len(vc) > 0 else "N/A",
            "freq": int(vc.iloc[0]) if len(vc) > 0 else 0,
            "freq %": round(vc.iloc[0] / len(df) * 100, 2) if len(vc) > 0 else 0,
        })
    st.dataframe(pd.DataFrame(cat_rows).set_index("column"), use_container_width=True)

st.markdown("---")
st.write("### Data Preview")
n_rows = st.slider("Rows to preview", 5, 50, 10)
st.dataframe(df.head(n_rows), use_container_width=True)

