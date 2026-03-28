import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_theme
st.session_state["_page_key"] = "3_Visualization"
apply_theme()

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io


if "df" not in st.session_state:
    st.session_state.df = None

st.title("📊 Visualization Studio")

if st.session_state.df is None:
    st.warning("Upload data first on the Upload page."); st.stop()

# ── DEDUPLICATE COLUMNS ────────────────────────────────────────────────────────
raw = st.session_state.df.copy()
seen = {}
new_cols = []
for col in raw.columns:
    if col in seen:
        seen[col] += 1
        new_cols.append(f"{col}_{seen[col]}")
    else:
        seen[col] = 0
        new_cols.append(col)
raw.columns = new_cols
df = raw

categorical_cols = df.select_dtypes(include=["object","category"]).columns.tolist()
numeric_cols     = df.select_dtypes(include=np.number).columns.tolist()
all_cols         = df.columns.tolist()

# ── CHART THEME ───────────────────────────────────────────────────────────────
THEME_COLORS = px.colors.qualitative.Bold
LAYOUT_BASE = dict(
    font_family="Inter, sans-serif",
    title_font_size=15,
    title_font_color="#0f172a",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,1)",
    margin=dict(t=50, b=40, l=40, r=20),
    legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor="#e2e8f0", borderwidth=1)
)

CHART_HEIGHT = 420

def style_fig(fig, title="", xlab="", ylab=""):
    fig.update_layout(
        **LAYOUT_BASE,
        title=dict(text=title, x=0.02, xanchor="left"),
        xaxis_title=xlab,
        yaxis_title=ylab,
        height=CHART_HEIGHT,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9", zeroline=False)
    return fig

def chart_download(fig, key):
    export_fig = go.Figure(fig)
    export_fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="#f8fafc",
        font_color="#0f172a",
        title_font_color="#0f172a",
    )
    st.caption("💡 Hover over the chart and click the **📷 camera icon** (top-right) to save as PNG.")

# ── FILTERS ───────────────────────────────────────────────────────────────────
with st.expander("🔎 Filters", expanded=False):
    fc1, fc2 = st.columns(2)
    with fc1:
        if categorical_cols:
            fc = st.selectbox("Filter by category", ["(none)"] + categorical_cols, key="f_cat")
            if fc != "(none)":
                vals = df[fc].astype(str).dropna().unique().tolist()
                sel  = st.multiselect("Keep values", vals, default=vals, key="f_cat_v")
                if sel: df = df[df[fc].astype(str).isin(sel)]
    with fc2:
        if numeric_cols:
            fn = st.selectbox("Filter by range", ["(none)"] + numeric_cols, key="f_num")
            if fn != "(none)":
                mn, mx = float(df[fn].min()), float(df[fn].max())
                rng    = st.slider("Range", mn, mx, (mn, mx), key="f_rng")
                df     = df[df[fn].between(rng[0], rng[1])]

if df.empty:
    st.warning("No data after filtering."); st.stop()
st.caption(f"Working with {len(df):,} rows after filtering.")
st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# ANALYTICAL DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Analytical Dashboard")

r1c1, r1c2 = st.columns(2, gap="medium")
r2c1, r2c2 = st.columns(2, gap="medium")
r3c1, r3c2 = st.columns(2, gap="medium")

with r1c1:
    with st.container(border=True):
        st.markdown("**Distribution (Histogram)**")
        if numeric_cols:
            g1c = st.selectbox("Column", numeric_cols, key="g1c")
            g1b = st.slider("Bins", 5, 80, 20, key="g1b")
            fig = px.histogram(df, x=g1c, nbins=g1b,
                               color_discrete_sequence=[THEME_COLORS[0]],
                               labels={g1c: g1c, "count": "Frequency"})
            fig = style_fig(fig, f"Distribution of {g1c}", g1c, "Frequency")
            st.plotly_chart(fig, use_container_width=True, key="g1")
            chart_download(fig, "g1")

with r1c2:
    with st.container(border=True):
        st.markdown("**Comparison (Bar Chart)**")
        if categorical_cols and numeric_cols:
            g2cat = st.selectbox("Category", categorical_cols, key="g2cat")
            g2num = st.selectbox("Value", numeric_cols, key="g2num")
            g2n   = st.slider("Top N", 3, 30, 10, key="g2n")
            g2agg = st.selectbox("Aggregation", ["mean","sum","count","median"], key="g2agg")
            gd    = df.groupby(g2cat)[g2num].agg(g2agg).reset_index().nlargest(g2n, g2num)
            fig   = px.bar(gd, x=g2cat, y=g2num, color=g2cat,
                           color_discrete_sequence=THEME_COLORS,
                           labels={g2cat: g2cat.replace("_"," "),
                                   g2num: g2num.replace("_"," ")})
            fig = style_fig(fig, f"{g2agg.capitalize()} of {g2num} by {g2cat} (Top {g2n})",
                            g2cat.replace("_"," "), f"{g2agg.capitalize()} of {g2num}")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="g2")
            chart_download(fig, "g2")

with r2c1:
    with st.container(border=True):
        st.markdown("**Relationship (Scatter)**")
        if len(numeric_cols) >= 2:
            g3x   = st.selectbox("X-axis", numeric_cols, key="g3x")
            g3y   = st.selectbox("Y-axis", numeric_cols, index=min(1, len(numeric_cols)-1), key="g3y")
            g3col = st.selectbox("Color by", ["(none)"] + categorical_cols, key="g3col")
            ca    = g3col if g3col != "(none)" else None
            _scatter_df = df[[g3x, g3y] + ([g3col] if ca else [])].dropna().copy()
            _scatter_df["_density"] = (
                _scatter_df.groupby([
                    pd.cut(_scatter_df[g3x], bins=40, labels=False),
                    pd.cut(_scatter_df[g3y], bins=40, labels=False)
                ])[g3x].transform("count")
            )
            fig   = px.scatter(_scatter_df, x=g3x, y=g3y, color=ca,
                               color_discrete_sequence=THEME_COLORS,
                               opacity=0.65,
                               labels={g3x: g3x.replace("_"," "), g3y: g3y.replace("_"," ")})
            fig = style_fig(fig, f"{g3y} vs {g3x}", g3x.replace("_"," "), g3y.replace("_"," "))
            st.plotly_chart(fig, use_container_width=True, key="g3")
            chart_download(fig, "g3")

with r2c2:
    with st.container(border=True):
        st.markdown("**Correlation Heatmap**")
        if len(numeric_cols) >= 2:
            # Let user pick a subset so the heatmap stays readable in the dashboard grid
            max_hm = min(12, len(numeric_cols))
            hm_cols = numeric_cols[:max_hm]
            corr = df[hm_cols].corr()
            n    = len(hm_cols)
            # Fixed height that fills the card without overflowing; width comes from use_container_width
            hm_h = max(CHART_HEIGHT, n * 42 + 60)
            fig  = px.imshow(corr, color_continuous_scale="RdBu_r", text_auto=".2f",
                             aspect="auto",          # auto so it fills width, not squares only
                             labels=dict(color="r"))
            fig.update_layout(
                **LAYOUT_BASE,
                title=dict(text="Correlation Matrix", x=0.02, xanchor="left"),
                xaxis_title="", yaxis_title="",
                height=hm_h,
                margin=dict(t=46, b=10, l=10, r=10),
                coloraxis_colorbar=dict(
                    len=0.75,          # shorter bar
                    thickness=10,      # thinner bar
                    title=dict(text="r", side="right"),
                    tickfont=dict(size=10),
                    x=1.01,            # push it flush to the right edge
                ),
            )
            fig.update_xaxes(tickangle=-40, tickfont=dict(size=10), side="bottom")
            fig.update_yaxes(tickfont=dict(size=10))
            st.plotly_chart(fig, use_container_width=True, key="g4")
            chart_download(fig, "g4")

with r3c1:
    with st.container(border=True):
        st.markdown("**Distribution (Box Plot)**")
        if numeric_cols:
            g5y = st.selectbox("Value (Y-axis)", numeric_cols, key="g5y")
            g5x = st.selectbox("Group by (X-axis)", ["(none)"] + categorical_cols, key="g5x")
            xa  = g5x if g5x != "(none)" else None
            fig = px.box(df, x=xa, y=g5y, color=xa,
                         color_discrete_sequence=THEME_COLORS,
                         labels={g5y: g5y.replace("_"," ")})
            xtitle = g5x.replace("_"," ") if xa else ""
            fig = style_fig(fig, f"Box Plot of {g5y}" + (f" by {g5x}" if xa else ""),
                            xtitle, g5y.replace("_"," "))
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="g5")
            chart_download(fig, "g5")

with r3c2:
    with st.container(border=True):
        st.markdown("**Trend (Line Chart)**")
        if numeric_cols:
            g6x   = st.selectbox("X-axis", all_cols, key="g6x")
            g6y   = st.selectbox("Y-axis", numeric_cols, key="g6y")
            g6col = st.selectbox("Color by", ["(none)"] + categorical_cols, key="g6col")
            ca6   = g6col if g6col != "(none)" else None
            try:
                cols_needed = [g6x, g6y] + ([g6col] if ca6 else [])
                pld = df[cols_needed].dropna().reset_index(drop=True)
                pld = pld.sort_values(pld.columns[0])
                fig = px.line(pld, x=g6x, y=g6y, color=ca6,
                              color_discrete_sequence=THEME_COLORS,
                              labels={g6x: g6x.replace("_"," "), g6y: g6y.replace("_"," ")})
                fig = style_fig(fig, f"{g6y} over {g6x}", g6x.replace("_"," "), g6y.replace("_"," "))
                st.plotly_chart(fig, use_container_width=True, key="g6")
                chart_download(fig, "g6")
            except Exception as e:
                st.warning(f"Could not render line chart: {e}")

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# CUSTOM CHART BUILDER (enhanced)
# ════════════════════════════════════════════════════════════════════════════════
st.subheader("🔧 Custom Chart Builder")

CHART_TYPES = ["Histogram", "Bar Chart", "Scatter Plot", "Line Chart",
               "Box Plot", "Correlation Heatmap", "3D Scatter Plot", "Pie / Donut Chart"]

chart_type = st.selectbox("Chart type", CHART_TYPES, key="ctype")
fig = None
fig_mpl = None  # matplotlib fallback

# ── Per-chart type options with X + Y axis selection ──────────────────────────

if chart_type == "Histogram":
    if not numeric_cols: st.warning("No numeric columns."); st.stop()

    c1, c2, c3, c4 = st.columns(4)
    col   = c1.selectbox("X-axis (column)", numeric_cols, key="h_col")
    nbins = c2.slider("Bins", 5, 100, 20, key="h_bins")
    colby = c3.selectbox("Color/group by", ["(none)"] + categorical_cols, key="h_col2")
    ca    = colby if colby != "(none)" else None

    # Filters
    with st.expander("🔎 Chart Filters", expanded=False):
        f1, f2 = st.columns(2)
        if categorical_cols:
            fc = f1.selectbox("Filter category", ["(none)"] + categorical_cols, key="h_fc")
            if fc != "(none)":
                fvals = df[fc].astype(str).dropna().unique().tolist()
                fsel  = f2.multiselect("Keep", fvals, default=fvals, key="h_fv")
                if fsel: df = df[df[fc].astype(str).isin(fsel)]

    fig = px.histogram(df, x=col, nbins=nbins, color=ca,
                       color_discrete_sequence=THEME_COLORS,
                       labels={col: col.replace("_"," "), "count": "Frequency"})
    fig = style_fig(fig, f"Distribution of {col}", col.replace("_"," "), "Frequency")

    # Matplotlib version
    fig_mpl, ax = plt.subplots(figsize=(10, 4))
    if ca:
        for grp, gdf in df.groupby(ca):
            ax.hist(gdf[col].dropna(), bins=nbins, alpha=0.7, label=str(grp), edgecolor="white")
        ax.legend(title=ca)
    else:
        ax.hist(df[col].dropna(), bins=nbins, color="#4f46e5", edgecolor="white", alpha=0.85)
    ax.set_xlabel(col.replace("_"," ")); ax.set_ylabel("Frequency")
    ax.set_title(f"Distribution of {col}", fontsize=14, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f8fafc"); fig_mpl.patch.set_facecolor("white")

elif chart_type == "Bar Chart":
    if not (categorical_cols and numeric_cols):
        st.warning("Need categorical + numeric columns."); st.stop()

    c1, c2, c3, c4, c5 = st.columns(5)
    cat  = c1.selectbox("X-axis (category)", categorical_cols, key="b_cat")
    num  = c2.selectbox("Y-axis (value)", numeric_cols, key="b_num")
    agg  = c3.selectbox("Aggregation", ["mean","sum","count","median"], key="b_agg")
    topn = c4.slider("Top N categories", 3, 50, 15, key="b_topn")
    colby = c5.selectbox("Color/group by", ["(none)", cat] + [c for c in categorical_cols if c != cat], key="b_colby")
    ca    = colby if colby != "(none)" else None

    # Filters
    with st.expander("🔎 Chart Filters", expanded=False):
        f1, f2 = st.columns(2)
        fcat = f1.selectbox("Filter category", ["(none)"] + categorical_cols, key="b_fc")
        if fcat != "(none)":
            fvals = df[fcat].astype(str).dropna().unique().tolist()
            fsel  = f2.multiselect("Keep", fvals, default=fvals, key="b_fv")
            if fsel: df = df[df[fcat].astype(str).isin(fsel)]
        if numeric_cols:
            fn = f1.selectbox("Filter numeric range", ["(none)"] + numeric_cols, key="b_fn")
            if fn != "(none)":
                mn, mx = float(df[fn].min()), float(df[fn].max())
                rng = f2.slider("Range", mn, mx, (mn, mx), key="b_frng")
                df = df[df[fn].between(rng[0], rng[1])]

    gd   = df.groupby(cat)[num].agg(agg).reset_index().nlargest(topn, num)
    fig  = px.bar(gd, x=cat, y=num, color=ca if ca else cat,
                  color_discrete_sequence=THEME_COLORS,
                  labels={cat: cat.replace("_"," "),
                          num: f"{agg} of {num.replace('_',' ')}"})
    fig = style_fig(fig, f"{agg.capitalize()} of {num} by {cat} (Top {topn})",
                    cat.replace("_"," "), f"{agg.capitalize()} of {num.replace('_',' ')}")
    if not ca: fig.update_layout(showlegend=False)

    # Matplotlib version
    fig_mpl, ax = plt.subplots(figsize=(10, 4))
    colors = plt.cm.tab10.colors[:len(gd)]
    ax.bar(gd[cat].astype(str), gd[num], color=colors, edgecolor="white", alpha=0.9)
    ax.set_xlabel(cat.replace("_"," ")); ax.set_ylabel(f"{agg.capitalize()} of {num}")
    ax.set_title(f"{agg.capitalize()} of {num} by {cat} (Top {topn})", fontsize=14, fontweight="bold", pad=12)
    plt.xticks(rotation=45, ha="right")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f8fafc"); fig_mpl.patch.set_facecolor("white")
    plt.tight_layout()

elif chart_type == "Scatter Plot":
    if len(numeric_cols) < 2: st.warning("Need ≥2 numeric columns."); st.stop()
    c1, c2, c3, c4 = st.columns(4)
    xc    = c1.selectbox("X-axis", numeric_cols, key="sc_x")
    yc    = c2.selectbox("Y-axis", numeric_cols, index=min(1,len(numeric_cols)-1), key="sc_y")
    colby = c3.selectbox("Color/group by", ["(none)"] + categorical_cols, key="sc_col")
    trend = c4.checkbox("Trendline (OLS)", key="sc_trend")
    ca    = colby if colby != "(none)" else None

    # Filters
    with st.expander("🔎 Chart Filters", expanded=False):
        f1, f2 = st.columns(2)
        fcat = f1.selectbox("Filter category", ["(none)"] + categorical_cols, key="sc_fc")
        if fcat != "(none)":
            fvals = df[fcat].astype(str).dropna().unique().tolist()
            fsel  = f2.multiselect("Keep", fvals, default=fvals, key="sc_fv")
            if fsel: df = df[df[fcat].astype(str).isin(fsel)]

    _sc_df = df[[xc, yc] + ([colby] if ca else [])].dropna().copy()
    _sc_df["_density"] = (
        _sc_df.groupby([
            pd.cut(_sc_df[xc], bins=40, labels=False),
            pd.cut(_sc_df[yc], bins=40, labels=False)
        ])[xc].transform("count")
    )
    fig   = px.scatter(_sc_df, x=xc, y=yc, color=ca, color_discrete_sequence=THEME_COLORS,
                       trendline="ols" if (trend and not ca) else None,
                       opacity=0.65,
                       labels={xc: xc.replace("_"," "), yc: yc.replace("_"," ")})
    fig = style_fig(fig, f"Relationship: {yc} vs {xc}", xc.replace("_"," "), yc.replace("_"," "))

    # Matplotlib version
    fig_mpl, ax = plt.subplots(figsize=(10, 4))
    if ca:
        for grp, gdf in _sc_df.groupby(ca):
            ax.scatter(gdf[xc], gdf[yc], alpha=0.6, s=20, label=str(grp))
        ax.legend(title=ca)
    else:
        ax.scatter(_sc_df[xc], _sc_df[yc], alpha=0.6, color="#4f46e5", s=20)
    ax.set_xlabel(xc.replace("_"," ")); ax.set_ylabel(yc.replace("_"," "))
    ax.set_title(f"{yc} vs {xc}", fontsize=14, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f8fafc"); fig_mpl.patch.set_facecolor("white")

elif chart_type == "Line Chart":
    if not numeric_cols: st.warning("No numeric columns."); st.stop()
    c1, c2, c3 = st.columns(3)
    xc    = c1.selectbox("X-axis", all_cols, key="ln_x")
    yc    = c2.selectbox("Y-axis", numeric_cols, key="ln_y")
    colby = c3.selectbox("Color/group by", ["(none)"] + categorical_cols, key="ln_col")
    ca    = colby if colby != "(none)" else None
    try:
        cols_needed = [xc, yc] + ([colby] if ca else [])
        pld = df[cols_needed].dropna().reset_index(drop=True).sort_values(xc)
        fig = px.line(pld, x=xc, y=yc, color=ca, color_discrete_sequence=THEME_COLORS,
                      labels={xc: xc.replace("_"," "), yc: yc.replace("_"," ")}, markers=True)
        fig = style_fig(fig, f"{yc} over {xc}", xc.replace("_"," "), yc.replace("_"," "))
        # Matplotlib version
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        if ca:
            for grp, gdf in pld.groupby(ca):
                ax.plot(gdf[xc], gdf[yc], marker="o", ms=3, label=str(grp))
            ax.legend(title=ca)
        else:
            ax.plot(pld[xc], pld[yc], color="#4f46e5", marker="o", ms=3)
        ax.set_xlabel(xc.replace("_"," ")); ax.set_ylabel(yc.replace("_"," "))
        ax.set_title(f"{yc} over {xc}", fontsize=14, fontweight="bold", pad=12)
        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.set_facecolor("#f8fafc"); fig_mpl.patch.set_facecolor("white")
        plt.xticks(rotation=30, ha="right"); plt.tight_layout()
    except Exception as e:
        st.warning(f"Could not render line chart: {e}")

elif chart_type == "Box Plot":
    if not numeric_cols: st.warning("No numeric columns."); st.stop()
    c1, c2 = st.columns(2)
    yc  = c1.selectbox("Y-axis (value)", numeric_cols, key="bx_y")
    xc  = c2.selectbox("X-axis / group by", ["(none)"] + categorical_cols, key="bx_x")
    xa  = xc if xc != "(none)" else None
    fig = px.box(df, x=xa, y=yc, color=xa, color_discrete_sequence=THEME_COLORS,
                 points="outliers", labels={yc: yc.replace("_"," ")})
    xtitle = xc.replace("_"," ") if xa else ""
    fig = style_fig(fig, f"Box Plot of {yc}" + (f" grouped by {xc}" if xa else ""),
                    xtitle, yc.replace("_"," "))
    fig.update_layout(showlegend=False)

    # Matplotlib version
    fig_mpl, ax = plt.subplots(figsize=(10, 4))
    if xa:
        groups = [gdf[yc].dropna().values for _, gdf in df.groupby(xa)]
        labels = [str(g) for g in df[xa].dropna().unique()]
        ax.boxplot(groups, labels=labels, patch_artist=True,
                   boxprops=dict(facecolor="#c7d2fe"), medianprops=dict(color="#4f46e5", linewidth=2))
        plt.xticks(rotation=30, ha="right")
    else:
        ax.boxplot(df[yc].dropna().values, patch_artist=True,
                   boxprops=dict(facecolor="#c7d2fe"), medianprops=dict(color="#4f46e5", linewidth=2))
    ax.set_ylabel(yc.replace("_"," "))
    ax.set_title(f"Box Plot of {yc}", fontsize=14, fontweight="bold", pad=12)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_facecolor("#f8fafc"); fig_mpl.patch.set_facecolor("white")
    plt.tight_layout()

elif chart_type == "Correlation Heatmap":
    if len(numeric_cols) < 2: st.warning("Need ≥2 numeric columns."); st.stop()
    sel_cols = st.multiselect("Columns to include", numeric_cols,
                               default=numeric_cols[:min(10,len(numeric_cols))], key="hm_cols")
    if len(sel_cols) >= 2:
        corr = df[sel_cols].corr()
        n_hm = len(sel_cols)
        hm_h_custom = max(500, n_hm * 42 + 80)
        fig  = px.imshow(corr, color_continuous_scale="RdBu_r", text_auto=".2f",
                         aspect="equal", labels=dict(color="r"))
        fig.update_layout(
            **LAYOUT_BASE,
            title=dict(text="Correlation Matrix", x=0.02, xanchor="left"),
            xaxis_title="", yaxis_title="",
            height=hm_h_custom,
            coloraxis_colorbar=dict(len=0.6, thickness=12, title="r"),
        )
        fig.update_xaxes(tickangle=-35, tickfont=dict(size=11))
        fig.update_yaxes(tickfont=dict(size=11))

elif chart_type == "3D Scatter Plot":
    if len(numeric_cols) < 3: st.warning("Need ≥3 numeric columns for 3D."); st.stop()
    c1, c2, c3, c4 = st.columns(4)
    xc    = c1.selectbox("X-axis", numeric_cols, key="3d_x")
    yc    = c2.selectbox("Y-axis", numeric_cols, index=min(1,len(numeric_cols)-1), key="3d_y")
    zc    = c3.selectbox("Z-axis", numeric_cols, index=min(2,len(numeric_cols)-1), key="3d_z")
    colby = c4.selectbox("Color by", ["(none)"] + categorical_cols + numeric_cols, key="3d_col")
    ca    = colby if colby != "(none)" else None
    fig   = px.scatter_3d(df.dropna(subset=[xc,yc,zc]), x=xc, y=yc, z=zc, color=ca,
                          color_discrete_sequence=THEME_COLORS, opacity=0.75,
                          labels={xc: xc.replace("_"," "),
                                  yc: yc.replace("_"," "),
                                  zc: zc.replace("_"," ")})
    fig.update_layout(
        title=dict(text=f"3D Scatter: {xc} × {yc} × {zc}", x=0.02),
        font_family="Inter, sans-serif",
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(xaxis_title=xc.replace("_"," "),
                   yaxis_title=yc.replace("_"," "),
                   zaxis_title=zc.replace("_"," "),
                   bgcolor="rgba(248,250,252,1)")
    )

elif chart_type == "Pie / Donut Chart":
    if not categorical_cols: st.warning("No categorical columns."); st.stop()
    c1, c2, c3 = st.columns(3)
    cat   = c1.selectbox("Category", categorical_cols, key="pi_cat")
    topn  = c2.slider("Top N slices", 3, 20, 8, key="pi_topn")
    donut = c3.checkbox("Donut style", value=True, key="pi_donut")
    counts = df[cat].value_counts().reset_index()
    counts.columns = [cat, "count"]
    top   = counts.head(topn)
    other = counts.iloc[topn:]
    if not other.empty:
        top = pd.concat([top, pd.DataFrame([{cat: "Other", "count": other["count"].sum()}])],
                        ignore_index=True)
    fig = px.pie(top, names=cat, values="count",
                 color_discrete_sequence=THEME_COLORS, hole=0.4 if donut else 0)
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(title=dict(text=f"Distribution of {cat}", x=0.02),
                      font_family="Inter, sans-serif",
                      paper_bgcolor="rgba(0,0,0,0)",
                      legend_title=cat.replace("_"," "))

    # Matplotlib version
    fig_mpl, ax = plt.subplots(figsize=(7, 7))
    mpl_colors = [plt.cm.tab10(i / 10) for i in range(min(len(top), 10))]
    wedge_kw = {"width": 0.5} if donut else {}
    ax.pie(
        top["count"].values,
        labels=top[cat].astype(str).tolist(),
        autopct="%1.1f%%",
        colors=mpl_colors,
        wedgeprops=wedge_kw,
        startangle=140,
        pctdistance=0.75 if donut else 0.85,
    )
    ax.set_title(f"Distribution of {cat}", fontsize=14, fontweight="bold", pad=12)
    fig_mpl.patch.set_facecolor("white")
    plt.tight_layout()

# ── RENDER PLOTLY + MATPLOTLIB SIDE BY SIDE ───────────────────────────────────
if fig is not None:
    st.plotly_chart(fig, use_container_width=True, key="custom_chart")
    chart_download(fig, "custom")

# Matplotlib panel below (always shown when available)
if fig_mpl is not None:
    with st.expander("📉 Matplotlib Version (static, downloadable)", expanded=False):
        st.pyplot(fig_mpl)
        buf = io.BytesIO()
        fig_mpl.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        st.download_button("⬇️ Download PNG", buf.getvalue(),
                           f"chart_{chart_type.lower().replace(' ','_')}.png",
                           mime="image/png", key="custom_mpl_dl")
        plt.close(fig_mpl)

st.markdown("---")

# ════════════════════════════════════════════════════════════════════════════════
# MAP VISUALIZATION
# ════════════════════════════════════════════════════════════════════════════════
_lat_candidates = [c for c in df.columns if any(k in c.lower() for k in ["lat", "latitude"])]
_lon_candidates = [c for c in df.columns if any(k in c.lower() for k in ["lon", "lng", "longitude"])]
_has_coords = len(_lat_candidates) > 0 and len(_lon_candidates) > 0

map_header = "🗺️ Map Visualization" + (" *(coordinate columns detected)*" if _has_coords else "")
with st.expander(map_header, expanded=_has_coords):
    _map_num_cols = df.select_dtypes(include=np.number).columns.tolist()
    if len(_map_num_cols) < 2:
        st.info("No numeric columns available for mapping.")
    else:
        mc1, mc2, mc3, mc4 = st.columns(4)
        lat_col  = mc1.selectbox("Latitude column",  _map_num_cols,
                                  index=_map_num_cols.index(_lat_candidates[0]) if _lat_candidates else 0,
                                  key="map_lat")
        lon_col  = mc2.selectbox("Longitude column", _map_num_cols,
                                  index=_map_num_cols.index(_lon_candidates[0]) if _lon_candidates else min(1,len(_map_num_cols)-1),
                                  key="map_lon")
        size_col = mc3.selectbox("Size by (optional)", ["(none)"] + _map_num_cols, key="map_size")
        color_col= mc4.selectbox("Color by (optional)", ["(none)"] + categorical_cols + _map_num_cols, key="map_color")

        map_df = df[[lat_col, lon_col] +
                    ([size_col] if size_col != "(none)" else []) +
                    ([color_col] if color_col != "(none)" else [])
                   ].dropna()

        if map_df.empty:
            st.warning("No rows with valid coordinates after dropping nulls.")
        else:
            _lat_range = map_df[lat_col].between(-90, 90)
            _lon_range = map_df[lon_col].between(-180, 180)
            map_df = map_df[_lat_range & _lon_range]
            if map_df.empty:
                st.warning("No rows with coordinates in valid geographic range (lat ±90, lon ±180).")
            else:
                st.caption(f"Plotting {len(map_df):,} points on the map.")
                _sz  = size_col  if size_col  != "(none)" else None
                _col = color_col if color_col != "(none)" else None
                map_fig = px.scatter_mapbox(
                    map_df, lat=lat_col, lon=lon_col,
                    size=_sz, color=_col,
                    color_discrete_sequence=THEME_COLORS,
                    size_max=18, zoom=2, opacity=0.7,
                    mapbox_style="carto-positron",
                    labels={lat_col: "Lat", lon_col: "Lon"},
                    height=520,
                )
                map_fig.update_layout(
                    margin=dict(t=30, b=0, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(map_fig, use_container_width=True, key="map_chart")
                chart_download(map_fig, "map")

st.markdown("---")

# ── SMART INTERPRETATION ──────────────────────────────────────────────────────
st.subheader("🧠 Smart Interpretation")
if numeric_cols:
    ic = st.selectbox("Select column", numeric_cols, key="interp_col")
    s  = df[ic].dropna()
    if not s.empty:
        Q1, Q3 = s.quantile(0.25), s.quantile(0.75)
        IQR    = Q3 - Q1
        n_out  = int(((s < Q1 - 1.5*IQR) | (s > Q3 + 1.5*IQR)).sum())
        skew   = s.skew()
        parts  = [f"**`{ic}`** — "]
        if   skew > 1:  parts.append("Strongly **right-skewed** (long tail on the right). ")
        elif skew < -1: parts.append("Strongly **left-skewed** (long tail on the left). ")
        else:           parts.append("Roughly **symmetric** distribution. ")
        if   s.mean() > s.median(): parts.append("Mean > Median — possible high-value outliers. ")
        elif s.mean() < s.median(): parts.append("Median > Mean — possible low-value outliers. ")
        parts.append(f"Detected **{n_out} potential outliers** using IQR method.")
        st.info("".join(parts))

st.markdown("---")

# ── STANDALONE MATPLOTLIB CHART ───────────────────────────────────────────────
st.subheader("📉 Matplotlib Chart")
if numeric_cols:
    mpl_col  = st.selectbox("Column", numeric_cols, key="mpl_col")
    mpl_type = st.radio("Chart type", ["Histogram", "KDE (density)"],
                        horizontal=True, key="mpl_type")
    clean_data = df[mpl_col].dropna()
    if not clean_data.empty:
        fig_mpl2, ax = plt.subplots(figsize=(10, 4))
        if mpl_type == "Histogram":
            ax.hist(clean_data, bins=30, color="#4f46e5", edgecolor="white", alpha=0.85)
            ax.set_ylabel("Frequency")
        else:
            clean_data.plot.density(ax=ax, color="#4f46e5", linewidth=2)
            ax.set_ylabel("Density")
        ax.set_title(f"{mpl_type} of {mpl_col}", fontsize=14, fontweight="bold", pad=12)
        ax.set_xlabel(mpl_col.replace("_", " "))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_facecolor("#f8fafc")
        fig_mpl2.patch.set_facecolor("white")
        st.pyplot(fig_mpl2)
        buf = io.BytesIO()
        fig_mpl2.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        st.download_button("⬇️ Download PNG", buf.getvalue(),
                           f"matplotlib_{mpl_col}.png", mime="image/png", key="mpl_dl")
        plt.close(fig_mpl2)
