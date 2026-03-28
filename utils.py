import streamlit as st


# ── LIGHT MODE CSS ────────────────────────────────────────────────────────────
LIGHT_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #e8f0fe 0%, #f0f4ff 40%, #eef2ff 70%, #e8f4f8 100%);
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(circle, #c7d7f7 1px, transparent 1px);
    background-size: 32px 32px;
    opacity: 0.25;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stMain"] { background: transparent; }
/* ── Force readable dark text throughout light mode ── */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4,
[data-testid="stMain"] h5,
[data-testid="stMain"] h6,
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] span,
[data-testid="stMain"] div,
[data-testid="stMain"] .stMarkdown,
[data-testid="stMain"] .stCaption,
[data-testid="stMain"] .stText,
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [class*="caption"],
[data-testid="stMain"] [data-testid="stWidgetLabel"] { color: #1e293b !important; }
[data-testid="stMain"] .stCaption,
[data-testid="stMain"] caption,
[data-testid="stMain"] small { color: #475569 !important; }
[data-testid="stMetric"] { background: #f8fafc; border: 0.5px solid #e2e8f0;
    border-radius: 10px; padding: 12px 16px !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748b !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 600 !important; color: #0f172a !important; }
[data-testid="stExpander"] { border: 0.5px solid #e2e8f0 !important; border-radius: 10px !important;
    background: rgba(255,255,255,0.6) !important; }
[data-testid="stExpander"] summary { color: #1e293b !important; }
/* Fix expander content text in light mode */
[data-testid="stExpander"] [data-testid="stExpanderDetails"] * { color: #1e293b !important; }
/* Fix download button text in export section */
[data-testid="stMain"] [data-testid="stDownloadButton"] button { color: #ffffff !important; }
[data-testid="stMain"] [data-testid="stDownloadButton"] button * { color: #ffffff !important; }
.stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.15s; color: #1e293b !important; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stDownloadButton > button { background: #0f172a !important; color: white !important;
    border: none !important; border-radius: 8px !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 2px 0; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; }
/* Tabs, radios, selects */
[data-testid="stMain"] [data-testid="stSelectbox"] label,
[data-testid="stMain"] [data-testid="stMultiSelect"] label,
[data-testid="stMain"] [data-testid="stRadio"] label,
[data-testid="stMain"] [data-testid="stCheckbox"] label,
[data-testid="stMain"] [data-testid="stSlider"] label { color: #1e293b !important; }
[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab"] { color: #1e293b !important; }
/* Info / warning / success boxes */
[data-testid="stMain"] [data-testid="stAlert"] { color: #1e293b !important; }
[data-testid="stMain"] [data-testid="stAlert"] * { color: #1e293b !important; }
/* Dataframes */
[data-testid="stMain"] [data-testid="stDataFrame"] * { color: #1e293b !important; }
/* JSON viewer */
[data-testid="stMain"] [data-testid="stJson"] * { color: #1e293b !important; }
/* Fix subheader / write text */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] * { color: #1e293b !important; }
</style>
"""

# ── DARK MODE CSS ─────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0f1e 0%, #0f172a 50%, #0d1526 100%) !important;
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(circle, #1e3a5f 1px, transparent 1px);
    background-size: 32px 32px;
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stMain"] { background: transparent !important; }
/* ── Force readable light text throughout dark mode ── */
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4,
[data-testid="stMain"] h5,
[data-testid="stMain"] h6,
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] span,
[data-testid="stMain"] div { color: #e2e8f0 !important; }
[data-testid="stMetric"] { background: #1e293b !important; border: 0.5px solid #334155 !important;
    border-radius: 10px; padding: 12px 16px !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #94a3b8 !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 600 !important; color: #f1f5f9 !important; }
[data-testid="stExpander"] { border: 0.5px solid #334155 !important; border-radius: 10px !important;
    background: #1e293b !important; }
/* Always-visible text inside expanders in dark mode */
[data-testid="stExpander"] [data-testid="stExpanderDetails"] * { color: #e2e8f0 !important; }
[data-testid="stExpander"] summary { color: #e2e8f0 !important; }
.stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.15s; color: #e2e8f0 !important; }
.stButton > button:hover { transform: translateY(-1px); }
.stDownloadButton > button { background: #3b82f6 !important; color: white !important;
    border: none !important; border-radius: 8px !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #020617 0%, #0a0f1e 100%) !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 2px 0; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; }
[data-testid="stAlert"] { background: #1e3a5f !important; color: #e2e8f0 !important; }
[data-testid="stAlert"] * { color: #e2e8f0 !important; }
[data-testid="stMain"] .stMarkdown,
[data-testid="stMain"] .stCaption { color: #94a3b8 !important; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] * { color: #e2e8f0 !important; }
[data-testid="stDataFrame"] { background: #1e293b !important; }
/* Widget labels */
[data-testid="stMain"] [data-testid="stSelectbox"] label,
[data-testid="stMain"] [data-testid="stMultiSelect"] label,
[data-testid="stMain"] [data-testid="stRadio"] label,
[data-testid="stMain"] [data-testid="stCheckbox"] label,
[data-testid="stMain"] [data-testid="stSlider"] label { color: #e2e8f0 !important; }
[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab"] { color: #e2e8f0 !important; }
</style>
"""


def apply_theme():
    """Apply light or dark theme CSS based on session state."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False
    st.markdown(
        DARK_CSS if st.session_state.dark_mode else LIGHT_CSS,
        unsafe_allow_html=True,
    )
