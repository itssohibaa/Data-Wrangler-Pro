import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_theme
st.session_state["_page_key"] = "6_Dashboard"
apply_theme()

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ── SESSION INIT ──────────────────────────────────────────────────────────────
for k, v in [("df", None), ("dashboard_charts", []), ("_dash_counter", 0)]:
    if k not in st.session_state:
        st.session_state[k] = v

st.title("📋 My Dashboard")
st.caption("Build your own dashboard by adding charts from your data.")

if st.session_state.df is None:
    st.warning("Upload a dataset first on the Upload page.")
    st.page_link("pages/1_Upload.py", label="📂 Go to Upload", use_container_width=False)
    st.stop()

df_full = st.session_state.df.copy()

# deduplicate columns
seen = {}
new_cols = []
for col in df_full.columns:
    if col in seen:
        seen[col] += 1
        new_cols.append(f"{col}_{seen[col]}")
    else:
        seen[col] = 0
        new_cols.append(col)
df_full.columns = new_cols

categorical_cols = df_full.select_dtypes(include=["object", "category"]).columns.tolist()
numeric_cols     = df_full.select_dtypes(include=np.number).columns.tolist()
all_cols         = df_full.columns.tolist()

THEME_COLORS = px.colors.qualitative.Bold
LAYOUT_BASE = dict(
    font_family="Inter, sans-serif",
    title_font_size=14,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,1)",
    margin=dict(t=45, b=35, l=35, r=15),
    legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#e2e8f0", borderwidth=1),
)

def style_fig(fig, title="", xlab="", ylab="", height=380):
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, x=0.02, xanchor="left"),
        xaxis_title=xlab,
        yaxis_title=ylab,
        height=height,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# CHART BUILDER PANEL
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("➕ Add Chart to Dashboard", expanded=len(st.session_state.dashboard_charts) == 0):
    st.markdown("Configure a chart and click **Add to Dashboard** to pin it.")

    CHART_TYPES = [
        "Histogram", "Bar Chart", "Scatter Plot", "Line Chart",
        "Box Plot", "Correlation Heatmap", "3D Scatter Plot",
        "Pie / Donut Chart", "Area Chart", "Violin Plot",
        "Bubble Chart", "Funnel Chart",
    ]

    cfg_col1, cfg_col2 = st.columns([2, 3])

    with cfg_col1:
        chart_type = st.selectbox("Chart type", CHART_TYPES, key="dash_ctype")
        chart_title = st.text_input("Chart title (optional)", placeholder=f"My {chart_type}", key="dash_title")

    # ── Per-chart config ───────────────────────────────────────────────────────
    fig_preview = None
    chart_cfg   = {}   # store config to replay on render

    with cfg_col2:
        if chart_type == "Histogram":
            if numeric_cols:
                col    = st.selectbox("Column", numeric_cols, key="d_h_col")
                nbins  = st.slider("Bins", 5, 100, 20, key="d_h_bins")
                colby  = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_h_cb")
                ca     = colby if colby != "(none)" else None
                fig_preview = px.histogram(df_full, x=col, nbins=nbins, color=ca,
                                           color_discrete_sequence=THEME_COLORS)
                fig_preview = style_fig(fig_preview, chart_title or f"Distribution of {col}", col, "Frequency")
                chart_cfg = dict(type=chart_type, col=col, nbins=nbins, ca=ca,
                                 title=chart_title or f"Distribution of {col}")

        elif chart_type == "Bar Chart":
            if categorical_cols and numeric_cols:
                cat  = st.selectbox("Category (X)", categorical_cols, key="d_b_cat")
                num  = st.selectbox("Value (Y)", numeric_cols, key="d_b_num")
                agg  = st.selectbox("Aggregation", ["mean","sum","count","median"], key="d_b_agg")
                topn = st.slider("Top N", 3, 30, 10, key="d_b_topn")
                gd   = df_full.groupby(cat)[num].agg(agg).reset_index().nlargest(topn, num)
                fig_preview = px.bar(gd, x=cat, y=num, color=cat,
                                     color_discrete_sequence=THEME_COLORS)
                fig_preview = style_fig(fig_preview,
                                        chart_title or f"{agg.capitalize()} of {num} by {cat}",
                                        cat, f"{agg.capitalize()} of {num}")
                fig_preview.update_layout(showlegend=False)
                chart_cfg = dict(type=chart_type, cat=cat, num=num, agg=agg, topn=topn,
                                 title=chart_title or f"{agg.capitalize()} of {num} by {cat}")

        elif chart_type == "Scatter Plot":
            if len(numeric_cols) >= 2:
                xc    = st.selectbox("X-axis", numeric_cols, key="d_sc_x")
                yc    = st.selectbox("Y-axis", numeric_cols, index=min(1, len(numeric_cols)-1), key="d_sc_y")
                colby = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_sc_cb")
                ca    = colby if colby != "(none)" else None
                trend = st.checkbox("Trendline (OLS)", key="d_sc_trend")
                _df   = df_full[[xc, yc] + ([colby] if ca else [])].dropna()
                fig_preview = px.scatter(_df, x=xc, y=yc, color=ca,
                                         color_discrete_sequence=THEME_COLORS,
                                         trendline="ols" if trend and not ca else None,
                                         opacity=0.65)
                fig_preview = style_fig(fig_preview, chart_title or f"{yc} vs {xc}", xc, yc)
                chart_cfg = dict(type=chart_type, xc=xc, yc=yc, ca=ca, trend=trend,
                                 title=chart_title or f"{yc} vs {xc}")

        elif chart_type == "Line Chart":
            if numeric_cols:
                xc    = st.selectbox("X-axis", all_cols, key="d_ln_x")
                yc    = st.selectbox("Y-axis", numeric_cols, key="d_ln_y")
                colby = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_ln_cb")
                ca    = colby if colby != "(none)" else None
                try:
                    _df = df_full[[xc, yc] + ([colby] if ca else [])].dropna().sort_values(xc)
                    fig_preview = px.line(_df, x=xc, y=yc, color=ca,
                                          color_discrete_sequence=THEME_COLORS, markers=True)
                    fig_preview = style_fig(fig_preview, chart_title or f"{yc} over {xc}", xc, yc)
                    chart_cfg = dict(type=chart_type, xc=xc, yc=yc, ca=ca,
                                     title=chart_title or f"{yc} over {xc}")
                except Exception as e:
                    st.warning(f"Cannot preview: {e}")

        elif chart_type == "Box Plot":
            if numeric_cols:
                yc  = st.selectbox("Value (Y)", numeric_cols, key="d_bx_y")
                xc  = st.selectbox("Group by (X)", ["(none)"] + categorical_cols, key="d_bx_x")
                xa  = xc if xc != "(none)" else None
                fig_preview = px.box(df_full, x=xa, y=yc, color=xa,
                                     color_discrete_sequence=THEME_COLORS, points="outliers")
                fig_preview = style_fig(fig_preview,
                                        chart_title or f"Box Plot of {yc}" + (f" by {xc}" if xa else ""),
                                        xa or "", yc)
                fig_preview.update_layout(showlegend=False)
                chart_cfg = dict(type=chart_type, yc=yc, xa=xa,
                                 title=chart_title or f"Box Plot of {yc}")

        elif chart_type == "Correlation Heatmap":
            if len(numeric_cols) >= 2:
                sel = st.multiselect("Columns", numeric_cols,
                                     default=numeric_cols[:min(8, len(numeric_cols))], key="d_hm_cols")
                if len(sel) >= 2:
                    corr = df_full[sel].corr()
                    fig_preview = px.imshow(corr, color_continuous_scale="RdBu_r",
                                            text_auto=".2f", aspect="equal")
                    fig_preview.update_layout(**LAYOUT_BASE,
                                              title=dict(text=chart_title or "Correlation Matrix", x=0.02),
                                              height=380)
                    chart_cfg = dict(type=chart_type, sel=sel,
                                     title=chart_title or "Correlation Matrix")

        elif chart_type == "3D Scatter Plot":
            if len(numeric_cols) >= 3:
                xc    = st.selectbox("X", numeric_cols, key="d_3d_x")
                yc    = st.selectbox("Y", numeric_cols, index=min(1, len(numeric_cols)-1), key="d_3d_y")
                zc    = st.selectbox("Z", numeric_cols, index=min(2, len(numeric_cols)-1), key="d_3d_z")
                colby = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_3d_cb")
                ca    = colby if colby != "(none)" else None
                fig_preview = px.scatter_3d(df_full.dropna(subset=[xc,yc,zc]),
                                            x=xc, y=yc, z=zc, color=ca,
                                            color_discrete_sequence=THEME_COLORS, opacity=0.75)
                fig_preview.update_layout(font_family="Inter, sans-serif",
                                          paper_bgcolor="rgba(0,0,0,0)",
                                          title=dict(text=chart_title or f"3D: {xc} × {yc} × {zc}", x=0.02),
                                          height=420)
                chart_cfg = dict(type=chart_type, xc=xc, yc=yc, zc=zc, ca=ca,
                                 title=chart_title or f"3D: {xc} × {yc} × {zc}")

        elif chart_type == "Pie / Donut Chart":
            if categorical_cols:
                cat   = st.selectbox("Category", categorical_cols, key="d_pi_cat")
                topn  = st.slider("Top N slices", 3, 15, 7, key="d_pi_topn")
                donut = st.checkbox("Donut style", value=True, key="d_pi_donut")
                counts = df_full[cat].value_counts().reset_index()
                counts.columns = [cat, "count"]
                top = counts.head(topn)
                rest = counts.iloc[topn:]
                if not rest.empty:
                    top = pd.concat([top, pd.DataFrame([{cat: "Other", "count": rest["count"].sum()}])],
                                    ignore_index=True)
                fig_preview = px.pie(top, names=cat, values="count",
                                     color_discrete_sequence=THEME_COLORS,
                                     hole=0.4 if donut else 0)
                fig_preview.update_traces(textposition="outside", textinfo="percent+label")
                fig_preview.update_layout(font_family="Inter, sans-serif",
                                          paper_bgcolor="rgba(0,0,0,0)",
                                          title=dict(text=chart_title or f"Distribution of {cat}", x=0.02),
                                          height=380)
                chart_cfg = dict(type=chart_type, cat=cat, topn=topn, donut=donut,
                                 title=chart_title or f"Distribution of {cat}")

        elif chart_type == "Area Chart":
            if numeric_cols:
                xc    = st.selectbox("X-axis", all_cols, key="d_ar_x")
                yc    = st.selectbox("Y-axis", numeric_cols, key="d_ar_y")
                colby = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_ar_cb")
                ca    = colby if colby != "(none)" else None
                try:
                    _df = df_full[[xc, yc] + ([colby] if ca else [])].dropna().sort_values(xc)
                    fig_preview = px.area(_df, x=xc, y=yc, color=ca,
                                          color_discrete_sequence=THEME_COLORS)
                    fig_preview = style_fig(fig_preview, chart_title or f"{yc} Area Chart", xc, yc)
                    chart_cfg = dict(type=chart_type, xc=xc, yc=yc, ca=ca,
                                     title=chart_title or f"{yc} Area Chart")
                except Exception as e:
                    st.warning(f"Cannot preview: {e}")

        elif chart_type == "Violin Plot":
            if numeric_cols:
                yc  = st.selectbox("Value (Y)", numeric_cols, key="d_vl_y")
                xc  = st.selectbox("Group by (X)", ["(none)"] + categorical_cols, key="d_vl_x")
                xa  = xc if xc != "(none)" else None
                fig_preview = px.violin(df_full, x=xa, y=yc, color=xa,
                                        color_discrete_sequence=THEME_COLORS,
                                        box=True, points="outliers")
                fig_preview = style_fig(fig_preview,
                                        chart_title or f"Violin: {yc}" + (f" by {xc}" if xa else ""),
                                        xa or "", yc)
                chart_cfg = dict(type=chart_type, yc=yc, xa=xa,
                                 title=chart_title or f"Violin: {yc}")

        elif chart_type == "Bubble Chart":
            if len(numeric_cols) >= 3:
                xc    = st.selectbox("X-axis", numeric_cols, key="d_bu_x")
                yc    = st.selectbox("Y-axis", numeric_cols, index=min(1,len(numeric_cols)-1), key="d_bu_y")
                szc   = st.selectbox("Bubble size", numeric_cols, index=min(2,len(numeric_cols)-1), key="d_bu_sz")
                colby = st.selectbox("Color by", ["(none)"] + categorical_cols, key="d_bu_cb")
                ca    = colby if colby != "(none)" else None
                _df   = df_full[[xc, yc, szc] + ([colby] if ca else [])].dropna()
                fig_preview = px.scatter(_df, x=xc, y=yc, size=szc, color=ca,
                                         color_discrete_sequence=THEME_COLORS,
                                         size_max=40, opacity=0.7)
                fig_preview = style_fig(fig_preview,
                                        chart_title or f"Bubble: {yc} vs {xc} (size={szc})", xc, yc)
                chart_cfg = dict(type=chart_type, xc=xc, yc=yc, szc=szc, ca=ca,
                                 title=chart_title or f"Bubble: {yc} vs {xc}")

        elif chart_type == "Funnel Chart":
            if categorical_cols and numeric_cols:
                cat = st.selectbox("Stage (category)", categorical_cols, key="d_fn_cat")
                num = st.selectbox("Value", numeric_cols, key="d_fn_num")
                agg = st.selectbox("Aggregation", ["sum","mean","count"], key="d_fn_agg")
                gd  = df_full.groupby(cat)[num].agg(agg).reset_index().sort_values(num, ascending=False)
                fig_preview = px.funnel(gd, x=num, y=cat, color_discrete_sequence=THEME_COLORS)
                fig_preview.update_layout(**LAYOUT_BASE,
                                          title=dict(text=chart_title or f"Funnel: {agg} {num} by {cat}", x=0.02),
                                          height=380)
                chart_cfg = dict(type=chart_type, cat=cat, num=num, agg=agg,
                                 title=chart_title or f"Funnel: {agg} {num} by {cat}")

    # ── Preview + Add Button ───────────────────────────────────────────────────
    if fig_preview is not None:
        st.markdown("**Preview:**")
        st.plotly_chart(fig_preview, use_container_width=True, key="dash_preview_chart")

    add_col, _ = st.columns([1, 3])
    with add_col:
        if st.button("➕ Add to Dashboard", type="primary", use_container_width=True,
                     disabled=fig_preview is None or not chart_cfg):
            entry_id = st.session_state["_dash_counter"]
            st.session_state["_dash_counter"] += 1
            st.session_state.dashboard_charts.append({
                "id": entry_id,
                "cfg": chart_cfg,
            })
            st.success(f"✅ Chart added! ({len(st.session_state.dashboard_charts)} chart(s) on dashboard)")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD RENDER
# ═══════════════════════════════════════════════════════════════════════════════
charts = st.session_state.dashboard_charts

if not charts:
    st.info("📊 Your dashboard is empty — add charts using the panel above.")
    st.stop()

st.markdown("---")

# Dashboard controls
ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1])
with ctrl1:
    layout_cols = st.radio("Layout", ["1 column", "2 columns", "3 columns"],
                            horizontal=True, index=1, key="dash_layout")
    n_cols = int(layout_cols[0])
with ctrl3:
    if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
        st.session_state.dashboard_charts = []
        st.rerun()

st.markdown(f"**{len(charts)} chart(s)** on your dashboard")
st.markdown("---")


def build_fig(cfg, df):
    """Rebuild a plotly figure from a stored config dict."""
    t = cfg["type"]
    fig = None

    if t == "Histogram":
        col, nbins, ca = cfg["col"], cfg["nbins"], cfg.get("ca")
        fig = px.histogram(df, x=col, nbins=nbins, color=ca,
                           color_discrete_sequence=THEME_COLORS)
        fig = style_fig(fig, cfg["title"], col, "Frequency")

    elif t == "Bar Chart":
        cat, num, agg, topn = cfg["cat"], cfg["num"], cfg["agg"], cfg["topn"]
        gd = df.groupby(cat)[num].agg(agg).reset_index().nlargest(topn, num)
        fig = px.bar(gd, x=cat, y=num, color=cat, color_discrete_sequence=THEME_COLORS)
        fig = style_fig(fig, cfg["title"], cat, f"{agg.capitalize()} of {num}")
        fig.update_layout(showlegend=False)

    elif t == "Scatter Plot":
        xc, yc, ca = cfg["xc"], cfg["yc"], cfg.get("ca")
        trend = cfg.get("trend", False)
        _df = df[[xc, yc] + ([ca] if ca else [])].dropna()
        fig = px.scatter(_df, x=xc, y=yc, color=ca,
                         color_discrete_sequence=THEME_COLORS,
                         trendline="ols" if trend and not ca else None, opacity=0.65)
        fig = style_fig(fig, cfg["title"], xc, yc)

    elif t == "Line Chart":
        xc, yc, ca = cfg["xc"], cfg["yc"], cfg.get("ca")
        _df = df[[xc, yc] + ([ca] if ca else [])].dropna().sort_values(xc)
        fig = px.line(_df, x=xc, y=yc, color=ca,
                      color_discrete_sequence=THEME_COLORS, markers=True)
        fig = style_fig(fig, cfg["title"], xc, yc)

    elif t == "Box Plot":
        yc, xa = cfg["yc"], cfg.get("xa")
        fig = px.box(df, x=xa, y=yc, color=xa,
                     color_discrete_sequence=THEME_COLORS, points="outliers")
        fig = style_fig(fig, cfg["title"], xa or "", yc)
        fig.update_layout(showlegend=False)

    elif t == "Correlation Heatmap":
        sel = cfg["sel"]
        sel = [c for c in sel if c in df.columns]
        if len(sel) >= 2:
            corr = df[sel].corr()
            fig = px.imshow(corr, color_continuous_scale="RdBu_r",
                            text_auto=".2f", aspect="equal")
            fig.update_layout(**LAYOUT_BASE, title=dict(text=cfg["title"], x=0.02), height=380)

    elif t == "3D Scatter Plot":
        xc, yc, zc, ca = cfg["xc"], cfg["yc"], cfg["zc"], cfg.get("ca")
        fig = px.scatter_3d(df.dropna(subset=[xc,yc,zc]), x=xc, y=yc, z=zc, color=ca,
                            color_discrete_sequence=THEME_COLORS, opacity=0.75)
        fig.update_layout(font_family="Inter, sans-serif", paper_bgcolor="rgba(0,0,0,0)",
                          title=dict(text=cfg["title"], x=0.02), height=420)

    elif t == "Pie / Donut Chart":
        cat, topn, donut = cfg["cat"], cfg["topn"], cfg.get("donut", True)
        counts = df[cat].value_counts().reset_index()
        counts.columns = [cat, "count"]
        top = counts.head(topn)
        rest = counts.iloc[topn:]
        if not rest.empty:
            top = pd.concat([top, pd.DataFrame([{cat: "Other", "count": rest["count"].sum()}])],
                            ignore_index=True)
        fig = px.pie(top, names=cat, values="count",
                     color_discrete_sequence=THEME_COLORS, hole=0.4 if donut else 0)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(font_family="Inter, sans-serif", paper_bgcolor="rgba(0,0,0,0)",
                          title=dict(text=cfg["title"], x=0.02), height=380)

    elif t == "Area Chart":
        xc, yc, ca = cfg["xc"], cfg["yc"], cfg.get("ca")
        _df = df[[xc, yc] + ([ca] if ca else [])].dropna().sort_values(xc)
        fig = px.area(_df, x=xc, y=yc, color=ca, color_discrete_sequence=THEME_COLORS)
        fig = style_fig(fig, cfg["title"], xc, yc)

    elif t == "Violin Plot":
        yc, xa = cfg["yc"], cfg.get("xa")
        fig = px.violin(df, x=xa, y=yc, color=xa,
                        color_discrete_sequence=THEME_COLORS, box=True, points="outliers")
        fig = style_fig(fig, cfg["title"], xa or "", yc)

    elif t == "Bubble Chart":
        xc, yc, szc, ca = cfg["xc"], cfg["yc"], cfg["szc"], cfg.get("ca")
        _df = df[[xc, yc, szc] + ([ca] if ca else [])].dropna()
        fig = px.scatter(_df, x=xc, y=yc, size=szc, color=ca,
                         color_discrete_sequence=THEME_COLORS, size_max=40, opacity=0.7)
        fig = style_fig(fig, cfg["title"], xc, yc)

    elif t == "Funnel Chart":
        cat, num, agg = cfg["cat"], cfg["num"], cfg["agg"]
        gd = df.groupby(cat)[num].agg(agg).reset_index().sort_values(num, ascending=False)
        fig = px.funnel(gd, x=num, y=cat, color_discrete_sequence=THEME_COLORS)
        fig.update_layout(**LAYOUT_BASE, title=dict(text=cfg["title"], x=0.02), height=380)

    return fig


# Render charts in grid
chart_rows = [charts[i:i+n_cols] for i in range(0, len(charts), n_cols)]

for row in chart_rows:
    cols = st.columns(n_cols)
    for col_widget, chart_entry in zip(cols, row):
        with col_widget:
            with st.container(border=True):
                cfg = chart_entry["cfg"]
                cid = chart_entry["id"]

                # Title row with remove button
                th, rb = st.columns([4, 1])
                with th:
                    st.markdown(f"**{cfg['title']}**")
                with rb:
                    if st.button("✖", key=f"del_{cid}", help="Remove this chart"):
                        st.session_state.dashboard_charts = [
                            c for c in st.session_state.dashboard_charts if c["id"] != cid
                        ]
                        st.rerun()

                try:
                    fig = build_fig(cfg, df_full)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"dash_fig_{cid}")
                    else:
                        st.warning("Could not render chart — data may have changed.")
                except Exception as e:
                    st.error(f"Render error: {e}")

    # Fill empty slots in last row
    if len(row) < n_cols:
        for _ in range(n_cols - len(row)):
            with cols[len(row) + _]:
                pass

st.markdown("---")
st.caption(f"Dashboard · {len(charts)} chart(s) · DataWrangler Pro")
