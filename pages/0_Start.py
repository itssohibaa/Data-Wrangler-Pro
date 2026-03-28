import streamlit as st
import time

st.set_page_config(
    page_title="DataWrangler Pro",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SESSION INIT ──────────────────────────────────────────────────────────────
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False
if "history" not in st.session_state:
    st.session_state.history = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

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
[data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
[data-testid="stMain"] h4, [data-testid="stMain"] h5, [data-testid="stMain"] h6,
[data-testid="stMain"] p, [data-testid="stMain"] label, [data-testid="stMain"] span,
[data-testid="stMain"] .stMarkdown, [data-testid="stMain"] [data-testid="stWidgetLabel"],
[data-testid="stMain"] [data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stMain"] [data-testid="stAlert"] { color: #1e293b !important; }
[data-testid="stMain"] .stCaption, [data-testid="stMain"] small,
[data-testid="stMain"] [data-testid="stCaptionContainer"] { color: #475569 !important; }
[data-testid="stMetric"] { background: #f8fafc; border: 0.5px solid #e2e8f0;
    border-radius: 10px; padding: 12px 16px !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748b !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 600 !important; color: #0f172a !important; }
[data-testid="stExpander"] { border: 0.5px solid #e2e8f0 !important; border-radius: 10px !important;
    background: rgba(255,255,255,0.6) !important; }
[data-testid="stExpander"] summary { color: #1e293b !important; }
.stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.15s; color: #1e293b !important; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.stDownloadButton > button { background: #0f172a !important; color: white !important;
    border: none !important; border-radius: 8px !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 2px 0; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; }
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
h1, h2, h3, h4, h5, p { color: #e2e8f0 !important; }
[data-testid="stMetric"] { background: #1e293b !important; border: 0.5px solid #334155 !important;
    border-radius: 10px; padding: 12px 16px !important; }
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #94a3b8 !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 600 !important; color: #f1f5f9 !important; }
[data-testid="stExpander"] { border: 0.5px solid #334155 !important; border-radius: 10px !important;
    background: #1e293b !important; }
.stButton > button { border-radius: 8px; font-weight: 500; transition: all 0.15s; }
.stButton > button:hover { transform: translateY(-1px); }
.stDownloadButton > button { background: #3b82f6 !important; color: white !important;
    border: none !important; border-radius: 8px !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #020617 0%, #0a0f1e 100%) !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebarNav"] a { border-radius: 8px; margin: 2px 0; }
[data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.08) !important; }
[data-testid="stAlert"] { background: #1e3a5f !important; }
.stMarkdown, .stCaption { color: #94a3b8 !important; }
[data-testid="stDataFrame"] { background: #1e293b !important; }
</style>
"""

st.markdown(DARK_CSS if st.session_state.dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# ── SIDEBAR DARK MODE TOGGLE ──────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] [data-testid="stButton"] > button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #94a3b8 !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    padding: 6px 12px !important;
    height: auto !important;
    min-height: unset !important;
    line-height: 1.5 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    width: 100% !important;
    border-radius: 6px !important;
    margin-top: 4px !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #e2e8f0 !important;
    transform: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    dm_label = "☀️  Light mode" if st.session_state.dark_mode else "🌙  Dark mode"
    if st.button(dm_label, key="dm_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# ── INTRO (once per session) ──────────────────────────────────────────────────
if not st.session_state.intro_done:
    st.markdown("""
    <style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .intro-wrap  { text-align:center; padding:5rem 2rem 3rem; animation:fadeIn 0.8s ease forwards; }
    .intro-icon  { font-size:64px; margin-bottom:1.25rem; }
    .intro-title { font-size:2.6rem; font-weight:700; color:#0f172a; margin-bottom:0.4rem; }
    .intro-sub   { font-size:1.05rem; color:#64748b; margin-bottom:2.5rem; }
    .intro-steps { display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-bottom:2rem; }
    .intro-step  { font-size:0.9rem; color:#475569; background:rgba(255,255,255,0.75);
                   padding:8px 18px; border-radius:20px; border:0.5px solid #cbd5e1; }
    </style>
    <div class="intro-wrap">
      <div class="intro-icon">🔬</div>
      <div class="intro-title">DataWrangler Pro</div>
      <div class="intro-sub">Your AI-powered data preparation workspace</div>
      <div class="intro-steps">
        <span class="intro-step">📂 Upload</span>
        <span class="intro-step">🤖 AI Assistant</span>
        <span class="intro-step">🧹 Clean</span>
        <span class="intro-step">📊 Visualize</span>
        <span class="intro-step">📤 Export</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    bar = st.progress(0, text="Initialising workspace…")
    for pct, label in [(20, "Loading modules…"), (50, "Preparing components…"),
                       (80, "Almost ready…"), (100, "✓ Ready")]:
        time.sleep(0.5)
        bar.progress(pct, text=label)
    time.sleep(0.3)
    bar.empty()
    st.session_state.intro_done = True
    st.rerun()

# ── LANDING ───────────────────────────────────────────────────────────────────
title_color = "#e2e8f0" if st.session_state.dark_mode else "#0f172a"
sub_color   = "#94a3b8" if st.session_state.dark_mode else "#64748b"

st.markdown(f"""
<div style="padding: 1rem 0 0.5rem;">
  <h1 style="font-size:2rem; font-weight:700; margin-bottom:0.25rem; color:{title_color};">
    🔬 DataWrangler Pro
  </h1>
  <p style="color:{sub_color}; font-size:1rem; margin:0;">
    Your AI-powered data preparation & visualization workspace
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── SECTION CARDS (clickable) ─────────────────────────────────────────────────
if st.session_state.dark_mode:
    cards = [
        ("#1e3a5f", "#93c5fd", "#60a5fa", "📂", "Upload & Profile",  "CSV · Excel · JSON · Sheets",    "pages/1_Upload.py"),
        ("#1a1a2e", "#c4b5fd", "#a78bfa", "🤖", "AI Assistant",      "Ask questions about your data",  "pages/2_AI_Assistant.py"),
        ("#14532d", "#86efac", "#4ade80", "🧹", "Clean & Prepare",   "Missing · Duplicates · Scale",   "pages/3_Cleaning.py"),
        ("#3b0764", "#d8b4fe", "#c084fc", "📊", "Visualize",         "8 chart types · 3D · Download",  "pages/4_Visualization.py"),
        ("#431407", "#fdba74", "#fb923c", "📤", "Export",            "CSV · Excel · Report · Recipe",  "pages/5_Export.py"),
    ]
else:
    cards = [
        ("#eff6ff", "#1e40af", "#3b82f6", "📂", "Upload & Profile",  "CSV · Excel · JSON · Sheets",    "pages/1_Upload.py"),
        ("#f5f3ff", "#5b21b6", "#7c3aed", "🤖", "AI Assistant",      "Ask questions about your data",  "pages/2_AI_Assistant.py"),
        ("#f0fdf4", "#166534", "#16a34a", "🧹", "Clean & Prepare",   "Missing · Duplicates · Scale",   "pages/3_Cleaning.py"),
        ("#fdf4ff", "#6b21a8", "#9333ea", "📊", "Visualize",         "8 chart types · 3D · Download",  "pages/4_Visualization.py"),
        ("#fff7ed", "#9a3412", "#ea580c", "📤", "Export",            "CSV · Excel · Report · Recipe",  "pages/5_Export.py"),
    ]

cols = st.columns(5)
for col, (bg, title_c, sub_c, icon, title, sub, page) in zip(cols, cards):
    with col:
        st.markdown(f"""
          <div style="background:{bg};border-radius:12px;padding:1.25rem 1.25rem 1rem;
                      border:0.5px solid {sub_c}55;
                      transition: transform 0.15s, box-shadow 0.15s;"
               onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 8px 24px rgba(0,0,0,0.13)'"
               onmouseout="this.style.transform='';this.style.boxShadow=''">
            <div style="font-size:28px">{icon}</div>
            <div style="font-weight:600;margin-top:8px;color:{title_c}">{title}</div>
            <div style="font-size:13px;color:{sub_c};margin-top:4px">{sub}</div>
          </div>""", unsafe_allow_html=True)
        if st.button(f"Open {title}", key=f"card_{page}", use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Use the sidebar to navigate, or click any section card above. Start with **Upload & Profile**, then clean and visualize your data!")
st.markdown("---")
st.caption("DataWrangler Pro · Coursework Project — Data Wrangling & Visualization · IDs: 00017592 & 00018555")
