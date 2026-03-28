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

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Rows",          f"{df.shape[0]:,}")
m2.metric("Columns",       df.shape[1])
m3.metric("Duplicates",    f"{dupes:,} ({dupes_pct:.2f}%)")
m4.metric("Missing Cells", f"{total_missing:,}")
m5.metric("Missing %",     f"{missing_pct:.2f}%")

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

# ── DATE RANGE COLUMN SPLITTER ────────────────────────────────────────────────
import re as _re

def _looks_like_date_range(series):
    """Return True if >50% of non-null values look like 'date – date' or 'date - date'."""
    sample = series.dropna().astype(str).head(20)
    if len(sample) == 0:
        return False
    hits = sample.str.contains(r'\d{4}[-/]\d{2}[-/]\d{2}\s*[-–—]\s*\d{4}[-/]\d{2}[-/]\d{2}', regex=True)
    return hits.mean() > 0.5

date_range_cols = [c for c in df.columns if _looks_like_date_range(df[c])]

if date_range_cols:
    st.markdown("---")
    st.write("### 📅 Date Range Column Splitting")
    st.caption(
        "The following columns appear to contain date ranges (e.g. `2024-03-12 – 2024-03-18`). "
        "You can split them into separate *start* and *end* date columns."
    )

    for col in date_range_cols:
        with st.expander(f"Split `{col}`", expanded=True):
            start_name = st.text_input(
                "Start date column name", value=f"{col}_start", key=f"split_start_{col}"
            )
            end_name = st.text_input(
                "End date column name",   value=f"{col}_end",   key=f"split_end_{col}"
            )
            if st.button(f"✂️ Split `{col}`", key=f"split_btn_{col}"):
                try:
                    sep_pattern = r'\s*[-–—]\s*'
                    split_df = df[col].astype(str).str.split(sep_pattern, n=1, expand=True)
                    df[start_name] = pd.to_datetime(split_df[0].str.strip(), errors="coerce")
                    df[end_name]   = pd.to_datetime(split_df[1].str.strip(), errors="coerce")
                    st.session_state.df = df
                    if "log" in st.session_state:
                        st.session_state.log.append(
                            f"Split date range column '{col}' → '{start_name}', '{end_name}'"
                        )
                    st.success(
                        f"✅ Created **`{start_name}`** and **`{end_name}`** "
                        f"(original `{col}` kept). Refresh the page to see updated column list."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not split column: {e}")

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
