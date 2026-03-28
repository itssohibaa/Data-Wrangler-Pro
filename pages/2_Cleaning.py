import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_theme
st.session_state["_page_key"] = "2_Cleaning"
apply_theme()

import pandas as pd
import numpy as np
import re


for k, v in [("df", None), ("log", []), ("history", []), ("_tx_preview", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── TRANSFORMATION PREVIEW HELPER ─────────────────────────────────────────────
def show_tx_preview(label, before_df, after_df, affected_cols=None):
    st.session_state["_tx_preview"] = {
        "label": label,
        "rows_before": len(before_df),
        "rows_after": len(after_df),
        "missing_before": int(before_df.isnull().sum().sum()),
        "missing_after": int(after_df.isnull().sum().sum()),
        "affected_cols": affected_cols or [],
    }

def render_tx_preview():
    p = st.session_state.get("_tx_preview")
    if not p:
        return
    rows_delta  = p["rows_after"] - p["rows_before"]
    miss_before = p["missing_before"]
    miss_after  = p["missing_after"]
    miss_fixed  = max(0, miss_before - miss_after)
    with st.container(border=True):
        st.markdown("#### 🔍 Transformation Preview")
        c1, c2, c3 = st.columns([3, 3, 2])
        with c1:
            m1, m2 = st.columns(2)
            m1.metric("Rows Before", f"{p['rows_before']:,}")
            m2.metric("Total Missing (Affected)", f"{miss_fixed:,}")
            m3, m4 = st.columns(2)
            m3.metric("Rows After", f"{p['rows_after']:,}",
                      delta=f"{rows_delta:+,}" if rows_delta != 0 else "0",
                      delta_color="inverse" if rows_delta < 0 else "normal")
            m4.metric("Remaining Missing", f"{miss_after:,}",
                      delta=f"{miss_after - miss_before:+,}" if miss_after != miss_before else "0",
                      delta_color="inverse" if miss_after > miss_before else "normal")
        with c3:
            if p["affected_cols"]:
                cols_html = " ".join(f"<code style='background:#dbeafe;padding:2px 6px;border-radius:4px;margin:2px;display:inline-block'>{c}</code>" for c in p["affected_cols"])
                st.markdown(f"<div style='background:#eff6ff;border-radius:8px;padding:10px 14px;border:1px solid #bfdbfe'><b>Affected Columns:</b><br>{cols_html}</div>", unsafe_allow_html=True)
        if st.button("✖ Dismiss", key="_dismiss_preview"):
            st.session_state["_tx_preview"] = None
            st.rerun()
    st.markdown("")

st.title("🧹 Cleaning & Preparation Studio")

if st.session_state.df is None:
    st.warning("Please upload a dataset first."); st.stop()

render_tx_preview()

df = st.session_state.df.copy()

# ── UNDO + STATUS BAR ─────────────────────────────────────────────────────────
c1, c2 = st.columns([1, 4])
with c1:
    if st.button("↩️ Undo Last Step", type="secondary"):
        if len(st.session_state.history) > 1:
            st.session_state.history.pop()
            st.session_state.df = st.session_state.history[-1].copy()
            if st.session_state.log:
                undone = st.session_state.log.pop()
            st.success(f"↩️ Undone! Reverted to previous state.")
            st.rerun()
        else:
            st.warning("Nothing to undo.")
with c2:
    st.caption(f"Steps logged: {len(st.session_state.log)}  |  "
               f"Rows: {df.shape[0]:,}  |  Cols: {df.shape[1]}  |  "
               f"Missing: {int(df.isnull().sum().sum()):,}  |  "
               f"Duplicates: {int(df.duplicated().sum()):,}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. MISSING VALUES
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("🔍 1. Missing Values", expanded=True):
    mv = pd.DataFrame({
        "Missing Count": df.isnull().sum(),
        "Missing %": (df.isnull().sum() / len(df) * 100).round(2)
    })
    mv_f = mv[mv["Missing Count"] > 0]
    if mv_f.empty:
        st.success("No missing values!")
    else:
        st.dataframe(mv_f, use_container_width=True)

        st.markdown("#### Fix a Single Column")
        col = st.selectbox("Column to fix", mv_f.index.tolist(), key="mv_col")
        ctype = df[col].dtype
        st.info(f"`{col}` — type: `{ctype}` — {int(df[col].isnull().sum())} missing")

        _col_is_numeric = pd.api.types.is_numeric_dtype(df[col])
        opts = ["Drop rows", "Mode (most frequent)", "Constant value", "Forward Fill", "Backward Fill"]
        if _col_is_numeric:
            opts = ["Drop rows", "Mean", "Median", "Mode (most frequent)",
                    "Constant value", "Forward Fill", "Backward Fill"]
        method = st.selectbox("Fill method", opts, key="mv_method")
        const_val = st.text_input("Constant value", key="mv_const") if method == "Constant value" else ""

        if st.button("✅ Apply Missing Value Fix", key="mv_apply"):
            before_rows = len(df)
            before_miss = int(df[col].isnull().sum())
            st.session_state.history.append(df.copy())
            try:
                if method == "Drop rows":              df = df.dropna(subset=[col])
                elif method == "Mean":                 df[col] = df[col].fillna(df[col].mean())
                elif method == "Median":               df[col] = df[col].fillna(df[col].median())
                elif method == "Mode (most frequent)": df[col] = df[col].fillna(df[col].mode()[0])
                elif method == "Constant value":
                    try:    fill = float(const_val) if pd.api.types.is_numeric_dtype(df[col]) else const_val
                    except: fill = const_val
                    df[col] = df[col].fillna(fill)
                elif method == "Forward Fill":  df[col] = df[col].ffill()
                elif method == "Backward Fill": df[col] = df[col].bfill()
                after_miss = int(df[col].isnull().sum())
                fixed = before_miss - after_miss
                rows_removed = before_rows - len(df)
                show_tx_preview(f"Fix missing: {col}", st.session_state.history[-1], df, [col])
                st.session_state.df = df
                st.session_state.log.append(f"Missing values in '{col}' handled with {method}")
                if method == "Drop rows":
                    st.success(f"✅ Dropped {rows_removed} rows with missing `{col}`. Dataset now has {len(df):,} rows.")
                else:
                    st.success(f"✅ Filled {fixed} missing values in `{col}` using **{method}**. Remaining missing: {after_miss}.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("---")
        st.markdown("#### Drop Columns with High Missing %")
        thresh_pct = st.slider("Drop columns where missing % exceeds:", 1, 100, 50, key="mv_thresh_drop")
        high_miss_cols = mv_f[mv_f["Missing %"] > thresh_pct].index.tolist()
        if high_miss_cols:
            st.warning(f"{len(high_miss_cols)} column(s) exceed {thresh_pct}% missing: `{'`, `'.join(high_miss_cols)}`")
            if st.button(f"🗑️ Drop {len(high_miss_cols)} Column(s)", key="mv_drop_cols"):
                before_cols = df.shape[1]
                st.session_state.history.append(df.copy())
                df = df.drop(columns=high_miss_cols)
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Dropped {len(high_miss_cols)} high-missing columns: {high_miss_cols}")
                st.success(f"✅ Dropped {len(high_miss_cols)} column(s). Dataset now has {df.shape[1]} columns (was {before_cols}).")
                st.rerun()
        else:
            st.info(f"No columns exceed {thresh_pct}% missing.")

        st.markdown("---")
        st.markdown("#### Drop Rows with Missing Values in Chosen Columns")
        drop_miss_cols = st.multiselect(
            "Drop rows that have missing values in any of these columns:",
            df.columns.tolist(),
            key="mv_drop_rows_cols"
        )
        if drop_miss_cols:
            preview_count = df[drop_miss_cols].isnull().any(axis=1).sum()
            st.caption(f"This will remove **{preview_count:,}** row(s) that have at least one missing value in the selected columns.")
            if st.button("🗑️ Drop Rows with Missing Values", key="mv_drop_rows_apply"):
                if not drop_miss_cols:
                    st.error("Please select at least one column.")
                else:
                    before_rows = len(df)
                    st.session_state.history.append(df.copy())
                    df = df.dropna(subset=drop_miss_cols)
                    show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                    st.session_state.df = df
                    st.session_state.log.append(f"Dropped rows with missing values in columns: {drop_miss_cols}")
                    removed = before_rows - len(df)
                    st.success(f"✅ Dropped {removed:,} row(s). Dataset now has {len(df):,} rows.")
                    st.rerun()

        st.markdown("---")
        st.markdown("#### Bulk Fill — All Missing Columns")
        bulk_numeric = st.selectbox("Fill numeric columns with:", ["(skip)", "mean", "median", "mode"], key="bulk_num")
        bulk_categ   = st.selectbox("Fill categorical columns with:", ["(skip)", "most frequent"], key="bulk_cat")
        if st.button("✅ Apply Bulk Fill", key="mv_bulk"):
            st.session_state.history.append(df.copy())
            changed = []
            for c in mv_f.index.tolist():
                if pd.api.types.is_numeric_dtype(df[c]) and bulk_numeric != "(skip)":
                    n_before = int(df[c].isnull().sum())
                    if bulk_numeric == "mean":   df[c] = df[c].fillna(df[c].mean())
                    elif bulk_numeric == "median": df[c] = df[c].fillna(df[c].median())
                    elif bulk_numeric == "mode":   df[c] = df[c].fillna(df[c].mode()[0])
                    changed.append(f"`{c}` ({n_before} → {int(df[c].isnull().sum())} missing)")
                elif not pd.api.types.is_numeric_dtype(df[c]) and bulk_categ != "(skip)":
                    n_before = int(df[c].isnull().sum())
                    df[c] = df[c].fillna(df[c].mode()[0] if len(df[c].mode()) > 0 else "Unknown")
                    changed.append(f"`{c}` ({n_before} → {int(df[c].isnull().sum())} missing)")
            show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
            st.session_state.df = df
            st.session_state.log.append(f"Bulk missing fill — numeric: {bulk_numeric}, categorical: {bulk_categ}")
            if changed:
                st.success(f"✅ Filled missing values in {len(changed)} column(s): {', '.join(changed)}")
            else:
                st.info("No columns were changed (check fill method selections).")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# 2. DUPLICATES
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("🔁 2. Duplicate Detection & Treatment", expanded=False):
    total_d = int(df.duplicated().sum())
    st.metric("Full-row duplicates", total_d)

    dup_mode = st.radio("Detect by", ["Full row", "Subset of columns"], horizontal=True, key="dup_mode")
    subset = None
    if dup_mode == "Subset of columns":
        subset = st.multiselect("Key columns", df.columns.tolist(), key="dup_subset")

    check_subset = subset if (dup_mode == "Subset of columns" and subset) else None
    n_d = int(df.duplicated(subset=check_subset).sum())
    st.info(f"Found **{n_d}** duplicate(s) with current selection.")

    action = st.selectbox("Action", [
        "Show duplicate groups",
        "Remove duplicates (keep first)",
        "Remove duplicates (keep last)"
    ], key="dup_action")

    if st.button("✅ Apply", key="dup_apply"):
        st.session_state.history.append(df.copy())
        try:
            if action == "Show duplicate groups":
                mask = df.duplicated(subset=check_subset, keep=False)
                g = df[mask]
                st.write(f"{len(g)} rows involved:"); st.dataframe(g.head(100), use_container_width=True)
            else:
                keep = "first" if "first" in action else "last"
                before = len(df)
                df = df.drop_duplicates(subset=check_subset, keep=keep)
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Removed duplicates ({keep}) — subset: {check_subset or 'all'}")
                st.success(f"✅ Removed {before - len(df)} duplicate rows. Dataset now has {len(df):,} rows.")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. DATA TYPES & PARSING
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("🔢 3. Data Types & Parsing", expanded=False):
    dtype_op = st.selectbox("Operation", [
        "Convert column type",
        "Parse datetime (custom format or auto)",
        "Clean dirty numeric strings"
    ], key="dtype_op")

    if dtype_op == "Convert column type":
        type_col = st.selectbox("Column", df.columns.tolist(), key="type_col")
        tgt_type = st.selectbox("Convert to", ["numeric", "string", "datetime", "category"], key="tgt_type")
        st.caption(f"Current type: `{df[type_col].dtype}` | Sample: {df[type_col].dropna().iloc[:3].tolist() if not df[type_col].dropna().empty else 'N/A'}")
        if st.button("✅ Convert Type", key="type_apply"):
            st.session_state.history.append(df.copy())
            try:
                old_dtype = str(df[type_col].dtype)
                if tgt_type == "numeric":    df[type_col] = pd.to_numeric(df[type_col], errors="coerce")
                elif tgt_type == "string":   df[type_col] = df[type_col].astype(str)
                elif tgt_type == "datetime": df[type_col] = pd.to_datetime(df[type_col], errors="coerce")
                elif tgt_type == "category": df[type_col] = df[type_col].astype("category")
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Converted '{type_col}' from {old_dtype} to {tgt_type}")
                st.success(f"✅ Column `{type_col}` converted from `{old_dtype}` → `{tgt_type}` successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    elif dtype_op == "Parse datetime (custom format or auto)":
        dt_col = st.selectbox("Column to parse as datetime", df.columns.tolist(), key="dt_col")
        dt_fmt = st.text_input("Format string (leave blank for auto)", placeholder="%Y-%m-%d or %d/%m/%Y", key="dt_fmt")
        st.caption("Examples: `%Y-%m-%d`, `%d/%m/%Y`, `%m-%d-%Y %H:%M`. Blank = automatic (may be slower).")
        if st.button("✅ Parse Datetime", key="dt_apply"):
            st.session_state.history.append(df.copy())
            try:
                before_null = int(df[dt_col].isnull().sum())
                if dt_fmt.strip():
                    df[dt_col] = pd.to_datetime(df[dt_col], format=dt_fmt.strip(), errors="coerce")
                else:
                    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
                after_null = int(df[dt_col].isnull().sum())
                coerced = after_null - before_null
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Parsed '{dt_col}' as datetime (fmt: '{dt_fmt or 'auto'}')")
                msg = f"✅ `{dt_col}` parsed as datetime."
                if coerced > 0:
                    msg += f" **{coerced} value(s)** could not be parsed and were set to NaT."
                st.success(msg)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    elif dtype_op == "Clean dirty numeric strings":
        st.caption("Removes commas, currency symbols ($ £ € ¥), % signs, and extra spaces before converting to numeric.")
        dirty_col = st.selectbox("Column", df.select_dtypes(include="object").columns.tolist() or df.columns.tolist(), key="dirty_col")
        sample_vals = df[dirty_col].dropna().head(5).tolist()
        st.caption(f"Sample values: {sample_vals}")
        if st.button("✅ Clean & Convert to Numeric", key="dirty_apply"):
            st.session_state.history.append(df.copy())
            try:
                cleaned = (
                    df[dirty_col].astype(str)
                    .str.replace(r"[$£€¥₹,\s%]", "", regex=True)
                    .str.replace(r"\((.+)\)", r"-\1", regex=True)  # (123) -> -123 for accounting format
                )
                result = pd.to_numeric(cleaned, errors="coerce")
                n_ok   = result.notna().sum()
                n_fail = result.isna().sum() - int(df[dirty_col].isnull().sum())
                df[dirty_col] = result
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Cleaned dirty numeric strings in '{dirty_col}'")
                st.success(f"✅ Cleaned `{dirty_col}`: {n_ok} values converted successfully, {max(0, n_fail)} could not be parsed (set to NaN).")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. CATEGORICAL TOOLS
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("🏷️ 4. Categorical Tools", expanded=False):
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if not cat_cols:
        st.info("No categorical columns found.")
    else:
        cat_op = st.selectbox("Operation", [
            "Standardize casing / trim whitespace",
            "Map / replace values",
            "Group rare categories into 'Other'",
            "One-hot encoding"
        ], key="cat_op")
        cat_col = st.selectbox("Column", cat_cols, key="cat_col")

        if cat_op == "Standardize casing / trim whitespace":
            casing = st.selectbox("Apply", ["Trim whitespace only", "lowercase", "UPPERCASE", "Title Case"], key="cat_case")
            if st.button("✅ Apply Standardization", key="cat_std"):
                st.session_state.history.append(df.copy())
                df[cat_col] = df[cat_col].astype(str).str.strip()
                if casing == "lowercase":     df[cat_col] = df[cat_col].str.lower()
                elif casing == "UPPERCASE":   df[cat_col] = df[cat_col].str.upper()
                elif casing == "Title Case":  df[cat_col] = df[cat_col].str.title()
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Standardized casing of '{cat_col}': {casing}")
                st.success(f"✅ Applied **{casing}** to `{cat_col}`."); st.rerun()

        elif cat_op == "Map / replace values":
            unique_vals = df[cat_col].dropna().unique().tolist()
            st.caption(f"Unique values in `{cat_col}`: {unique_vals[:20]}")
            from_val = st.selectbox("Replace this value", unique_vals, key="map_from")
            to_val   = st.text_input("With this value", key="map_to")
            if st.button("✅ Apply Mapping", key="cat_map") and to_val:
                st.session_state.history.append(df.copy())
                df[cat_col] = df[cat_col].replace({from_val: to_val})
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Mapped '{from_val}' → '{to_val}' in '{cat_col}'")
                st.success(f"✅ Replaced `{from_val}` → `{to_val}` in `{cat_col}`."); st.rerun()

        elif cat_op == "Group rare categories into 'Other'":
            freq_thresh = st.slider("Group categories appearing less than N times", 1, 100, 10, key="rare_thresh")
            counts = df[cat_col].value_counts()
            rare = counts[counts < freq_thresh].index.tolist()
            st.info(f"{len(rare)} rare categories will be grouped: {rare[:10]}")
            if st.button("✅ Apply Rare Grouping", key="cat_rare"):
                st.session_state.history.append(df.copy())
                df[cat_col] = df[cat_col].apply(lambda x: "Other" if x in rare else x)
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Grouped {len(rare)} rare categories in '{cat_col}' into 'Other'")
                st.success(f"✅ Grouped {len(rare)} rare categories into 'Other' in `{cat_col}`."); st.rerun()

        elif cat_op == "One-hot encoding":
            st.info(f"Will create binary columns for each unique value in `{cat_col}`.")
            drop_orig = st.checkbox("Drop original column after encoding", value=True, key="ohe_drop")
            if st.button("✅ Apply One-Hot Encoding", key="cat_ohe"):
                st.session_state.history.append(df.copy())
                dummies = pd.get_dummies(df[cat_col], prefix=cat_col, dtype=int)
                df = pd.concat([df, dummies], axis=1)
                if drop_orig: df = df.drop(columns=[cat_col])
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"One-hot encoded '{cat_col}' — {len(dummies.columns)} new columns")
                st.success(f"✅ Created {len(dummies.columns)} new binary column(s) from `{cat_col}`."); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# 5. OUTLIER DETECTION & TREATMENT
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📦 5. Outlier Detection & Treatment", expanded=False):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not num_cols:
        st.info("No numeric columns.")
    else:
        out_col    = st.selectbox("Column", num_cols, key="out_col")
        out_method = st.radio("Detection method", ["IQR (1.5×)", "Z-score (threshold 3)"], horizontal=True, key="out_method")
        series     = df[out_col].dropna()

        if out_method == "IQR (1.5×)":
            Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
            IQR = Q3 - Q1
            mask = (df[out_col] < Q1 - 1.5*IQR) | (df[out_col] > Q3 + 1.5*IQR)
            lower, upper = Q1 - 1.5*IQR, Q3 + 1.5*IQR
        else:
            z = (df[out_col] - series.mean()) / series.std()
            mask = z.abs() > 3
            lower, upper = series.mean() - 3*series.std(), series.mean() + 3*series.std()

        n_out = int(mask.sum())
        st.metric("Outliers detected", n_out)
        st.caption(f"Valid range: {lower:.2f} → {upper:.2f}")

        action = st.selectbox("Action", [
            "Do nothing (just view)",
            "Remove outlier rows",
            "Cap (winsorize) to boundary values"
        ], key="out_action")

        if st.button("✅ Apply Outlier Action", key="out_apply"):
            st.session_state.history.append(df.copy())
            if action == "Remove outlier rows":
                before = len(df)
                df = df[~mask]
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Removed {n_out} outlier rows from '{out_col}'")
                st.success(f"✅ Removed {n_out} outlier rows from `{out_col}`. Dataset now has {len(df):,} rows."); st.rerun()
            elif action == "Cap (winsorize) to boundary values":
                df[out_col] = df[out_col].clip(lower=lower, upper=upper)
                st.session_state.df = df
                st.session_state.log.append(f"Winsorized '{out_col}' to [{lower:.2f}, {upper:.2f}]")
                st.success(f"✅ Capped {n_out} outlier values in `{out_col}` to range [{lower:.2f}, {upper:.2f}]."); st.rerun()
            else:
                st.info("No changes made.")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. SCALING / NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📐 6. Scaling & Normalization", expanded=False):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not num_cols:
        st.info("No numeric columns.")
    else:
        scale_cols   = st.multiselect("Columns to scale", num_cols, key="scale_cols")
        scale_method = st.selectbox("Method", ["Min-Max (0–1)", "Z-score standardization"], key="scale_method")

        if scale_cols:
            # Validate — only numeric columns
            non_numeric = [c for c in scale_cols if c not in num_cols]
            if non_numeric:
                st.error(f"❌ The following columns are not numeric and cannot be scaled: `{'`, `'.join(non_numeric)}`")
                scale_cols = []
            else:
                st.write("**Before:**")
                st.dataframe(df[scale_cols].describe().T[["mean","std","min","max"]], use_container_width=True)

        if st.button("✅ Apply Scaling", key="scale_apply") and scale_cols:
            st.session_state.history.append(df.copy())
            for c in scale_cols:
                if scale_method == "Min-Max (0–1)":
                    mn, mx = df[c].min(), df[c].max()
                    df[c] = (df[c] - mn) / (mx - mn) if mx != mn else 0
                else:
                    df[c] = (df[c] - df[c].mean()) / df[c].std()
            show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
            st.session_state.df = df
            st.session_state.log.append(f"Scaled {scale_cols} using {scale_method}")
            st.success(f"✅ Scaled {len(scale_cols)} column(s) using **{scale_method}**.")
            st.write("**After:**")
            st.dataframe(df[scale_cols].describe().T[["mean","std","min","max"]], use_container_width=True)
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# 7. COLUMN OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("🔧 7. Column Operations", expanded=False):
    col_op = st.selectbox("Operation", [
        "Rename column",
        "Drop column(s)",
        "Create new column (formula)",
        "Bin numeric column into categories"
    ], key="col_op")

    if col_op == "Rename column":
        old = st.selectbox("Column to rename", df.columns.tolist(), key="ren_old")
        new = st.text_input("New name", key="ren_new")
        if st.button("✅ Rename", key="ren_apply") and new:
            st.session_state.history.append(df.copy())
            df = df.rename(columns={old: new})
            show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
            st.session_state.df = df
            st.session_state.log.append(f"Renamed '{old}' → '{new}'")
            st.success(f"✅ Renamed `{old}` → `{new}`."); st.rerun()

    elif col_op == "Drop column(s)":
        drop_cols = st.multiselect("Columns to drop", df.columns.tolist(), key="drop_cols")
        if st.button("✅ Drop", key="drop_apply") and drop_cols:
            st.session_state.history.append(df.copy())
            df = df.drop(columns=drop_cols)
            show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
            st.session_state.df = df
            st.session_state.log.append(f"Dropped columns: {drop_cols}")
            st.success(f"✅ Dropped {len(drop_cols)} column(s): `{'`, `'.join(drop_cols)}`."); st.rerun()

    elif col_op == "Create new column (formula)":
        st.caption("Use column names as variables. Examples: `salary / age`, `log(salary)`, `salary - salary.mean()`")
        new_col_name = st.text_input("New column name", key="new_col_name")
        formula      = st.text_input("Formula (use column names directly)", key="formula")
        if st.button("✅ Create Column", key="new_col_apply") and new_col_name and formula:
            st.session_state.history.append(df.copy())
            try:
                local_vars = {c: df[c] for c in df.columns}
                import math
                local_vars.update({"log": np.log, "sqrt": np.sqrt, "abs": np.abs,
                                   "exp": np.exp, "mean": np.mean})
                df[new_col_name] = eval(formula, {"__builtins__": {}}, local_vars)
                show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                st.session_state.df = df
                st.session_state.log.append(f"Created column '{new_col_name}' = {formula}")
                st.success(f"✅ Column `{new_col_name}` created successfully from formula: `{formula}`."); st.rerun()
            except Exception as e:
                st.error(f"Formula error: {e}")

    elif col_op == "Bin numeric column into categories":
        num_cols_bin = df.select_dtypes(include=np.number).columns.tolist()
        if not num_cols_bin:
            st.info("No numeric columns.")
        else:
            bin_col   = st.selectbox("Column to bin", num_cols_bin, key="bin_col")
            bin_n     = st.slider("Number of bins", 2, 20, 5, key="bin_n")
            bin_strat = st.radio("Strategy", ["Equal-width bins", "Quantile bins (equal-frequency)"],
                                 horizontal=True, key="bin_strat")
            bin_labels = st.text_input("Custom labels (comma-separated, optional)", key="bin_labels")
            new_bin_col = st.text_input("New column name", value=f"{bin_col}_binned", key="bin_new_col")

            if st.button("✅ Apply Binning", key="bin_apply"):
                st.session_state.history.append(df.copy())
                try:
                    labels = [l.strip() for l in bin_labels.split(",")] if bin_labels else None
                    if labels and len(labels) != bin_n:
                        st.error(f"Need exactly {bin_n} labels, got {len(labels)}.")
                    else:
                        if bin_strat == "Equal-width bins":
                            df[new_bin_col] = pd.cut(df[bin_col], bins=bin_n, labels=labels)
                        else:
                            df[new_bin_col] = pd.qcut(df[bin_col], q=bin_n, labels=labels, duplicates="drop")
                        show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                        st.session_state.df = df
                        st.session_state.log.append(f"Binned '{bin_col}' into '{new_bin_col}' ({bin_strat})")
                        st.success(f"✅ Created `{new_bin_col}` with {bin_n} bins from `{bin_col}`."); st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 7b. DATE RANGE SPLITTER
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📅 7b. Date Range Splitter", expanded=False):
    st.caption("Split a column that contains date ranges (e.g. '2020-01-01 - 2020-12-31') into two separate date columns.")

    text_cols_dr = df.select_dtypes(include=["object"]).columns.tolist()
    if not text_cols_dr:
        st.info("No text columns available for date range splitting.")
    else:
        dr_col = st.selectbox("Column containing date ranges", text_cols_dr, key="dr_col")
        sample_vals_dr = df[dr_col].dropna().head(5).tolist()
        st.caption(f"Sample values: {sample_vals_dr}")

        dr_sep = st.selectbox(
            "Separator between the two dates",
            [" - ", " – ", "-", "_", ":", " to ", "/", " / "],
            key="dr_sep",
            help="Choose the symbol that divides the start date from the end date in the range."
        )
        # Allow custom separator too
        custom_sep = st.text_input("Or enter a custom separator:", key="dr_custom_sep", placeholder="e.g.  |  or  ~")
        if custom_sep.strip():
            dr_sep = custom_sep

        c1, c2 = st.columns(2)
        dr_col1_name = c1.text_input("New column name — START date", value=f"{dr_col}_start", key="dr_col1_name")
        dr_col2_name = c2.text_input("New column name — END date",   value=f"{dr_col}_end",   key="dr_col2_name")

        if not dr_col1_name.strip() or not dr_col2_name.strip():
            st.warning("Please enter names for both new columns.")
        elif dr_col1_name.strip() == dr_col2_name.strip():
            st.error("Start and end column names must be different.")
        else:
            # Preview
            try:
                _preview = df[dr_col].dropna().head(3).apply(
                    lambda v: v.split(dr_sep, 1) if dr_sep in str(v) else [str(v), ""]
                )
                st.caption(f"Preview (first 3 rows): {_preview.tolist()}")
            except Exception:
                pass

            if st.button("✅ Split Date Range Column", key="dr_apply"):
                if dr_col1_name.strip() == dr_col or dr_col2_name.strip() == dr_col:
                    st.error("New column names must differ from the source column name.")
                else:
                    st.session_state.history.append(df.copy())
                    try:
                        def _split_range(val):
                            s = str(val) if pd.notna(val) else ""
                            parts = s.split(dr_sep, 1)
                            if len(parts) == 2:
                                return parts[0].strip(), parts[1].strip()
                            return s.strip(), ""

                        split_result = df[dr_col].apply(_split_range)
                        df[dr_col1_name.strip()] = split_result.apply(lambda x: x[0])
                        df[dr_col2_name.strip()] = split_result.apply(lambda x: x[1])

                        # Replace empty strings with NaN for cleanliness
                        df[dr_col1_name.strip()] = df[dr_col1_name.strip()].replace("", pd.NA)
                        df[dr_col2_name.strip()] = df[dr_col2_name.strip()].replace("", pd.NA)

                        n_ok = split_result.apply(lambda x: x[1] != "").sum()
                        n_fail = len(df) - n_ok

                        show_tx_preview('Transformation', st.session_state.history[-1] if st.session_state.history else df, df)
                        st.session_state.df = df
                        st.session_state.log.append(
                            f"Split '{dr_col}' by '{dr_sep}' → '{dr_col1_name.strip()}', '{dr_col2_name.strip()}'"
                        )
                        msg = f"✅ Created `{dr_col1_name.strip()}` and `{dr_col2_name.strip()}` from `{dr_col}`."
                        if n_fail > 0:
                            msg += f" **{n_fail}** row(s) did not contain the separator and were left with an empty end date."
                        st.success(msg)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error splitting column: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. DATA VALIDATION RULES
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("✅ 8. Data Validation Rules", expanded=False):
    val_type = st.selectbox("Validation type", [
        "Numeric range check (min / max)",
        "Allowed categories list",
        "Non-null constraint",
        "Regex pattern check"
    ], key="val_type")

    if val_type == "Numeric range check (min / max)":
        num_cols_v = df.select_dtypes(include=np.number).columns.tolist()
        if not num_cols_v:
            st.info("No numeric columns.")
        else:
            val_col  = st.selectbox("Column", num_cols_v, key="val_num_col")
            val_min  = st.number_input("Minimum allowed value", value=float(df[val_col].min()), key="val_min")
            val_max  = st.number_input("Maximum allowed value", value=float(df[val_col].max()), key="val_max")
            if st.button("🔍 Run Validation", key="val_num_run"):
                violations = df[(df[val_col] < val_min) | (df[val_col] > val_max)]
                st.metric("Violations found", len(violations))
                if not violations.empty:
                    st.warning(f"⚠️ {len(violations)} rows violate the range [{val_min}, {val_max}] for `{val_col}`.")
                    st.dataframe(violations, use_container_width=True)
                    viol_csv = violations.to_csv(index=False).encode()
                    st.download_button("⬇️ Download violations", viol_csv, "violations.csv", mime="text/csv")
                else:
                    st.success("✅ All values are within the specified range!")

    elif val_type == "Allowed categories list":
        cat_cols_v = df.select_dtypes(include=["object","category"]).columns.tolist()
        if not cat_cols_v:
            st.info("No categorical columns.")
        else:
            val_col   = st.selectbox("Column", cat_cols_v, key="val_cat_col")
            unique_v  = df[val_col].dropna().unique().tolist()
            allowed   = st.multiselect("Allowed values", unique_v, default=unique_v, key="val_allowed")
            if st.button("🔍 Run Validation", key="val_cat_run"):
                violations = df[~df[val_col].isin(allowed) & df[val_col].notna()]
                st.metric("Violations found", len(violations))
                if not violations.empty:
                    st.warning(f"⚠️ {len(violations)} rows have values not in the allowed list.")
                    st.dataframe(violations, use_container_width=True)
                    viol_csv = violations.to_csv(index=False).encode()
                    st.download_button("⬇️ Download violations", viol_csv, "violations.csv", mime="text/csv")
                else:
                    st.success("✅ All values are in the allowed list!")

    elif val_type == "Non-null constraint":
        nn_cols = st.multiselect("Columns that must not be null", df.columns.tolist(), key="val_nn_cols")
        if st.button("🔍 Run Validation", key="val_nn_run") and nn_cols:
            results = {c: int(df[c].isnull().sum()) for c in nn_cols}
            total_viol = sum(results.values())
            st.metric("Total null violations", total_viol)
            viol_rows = df[df[nn_cols].isnull().any(axis=1)]
            for c, n in results.items():
                if n > 0:
                    st.warning(f"`{c}`: {n} null values")
                else:
                    st.success(f"`{c}`: OK")
            if not viol_rows.empty:
                st.dataframe(viol_rows, use_container_width=True)
                viol_csv = viol_rows.to_csv(index=False).encode()
                st.download_button("⬇️ Download violations", viol_csv, "null_violations.csv", mime="text/csv")

    elif val_type == "Regex pattern check":
        cat_cols_rx = df.select_dtypes(include=["object"]).columns.tolist()
        if not cat_cols_rx:
            st.info("No text columns for regex check.")
        else:
            rx_col = st.selectbox("Column", cat_cols_rx, key="val_rx_col")
            rx_pat = st.text_input("Regex pattern (values must match)", placeholder=r"^\d{4}-\d{2}-\d{2}$", key="val_rx_pat")
            if rx_pat and st.button("🔍 Run Validation", key="val_rx_run"):
                try:
                    mask_match = df[rx_col].astype(str).str.match(rx_pat)
                    violations = df[~mask_match & df[rx_col].notna()]
                    st.metric("Violations found", len(violations))
                    if not violations.empty:
                        st.warning(f"⚠️ {len(violations)} values in `{rx_col}` do not match pattern `{rx_pat}`.")
                        st.dataframe(violations, use_container_width=True)
                        viol_csv = violations.to_csv(index=False).encode()
                        st.download_button("⬇️ Download violations", viol_csv, "regex_violations.csv", mime="text/csv")
                    else:
                        st.success(f"✅ All non-null values in `{rx_col}` match the pattern!")
                except re.error as e:
                    st.error(f"Invalid regex: {e}")

st.markdown("---")
st.subheader("✅ Current Dataset")
st.dataframe(st.session_state.df.head(10), use_container_width=True)

if st.session_state.log:
    with st.expander("📝 Transformation Log"):
        for i, s in enumerate(st.session_state.log, 1):
            st.write(f"{i}. {s}")
