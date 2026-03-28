import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import apply_theme
st.session_state["_page_key"] = "5_AI_Assistant"
apply_theme()

import pandas as pd
import numpy as np
import json
import requests


for k, v in [("df", None), ("log", []), ("history", []), ("ai_messages", []), ("ai_enabled", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

st.title("🤖 AI Assistant")

if st.session_state.df is None:
    st.warning("Please upload a dataset first."); st.stop()

df = st.session_state.df.copy()

# ── AI ENABLE TOGGLE ──────────────────────────────────────────────────────────
col_toggle, col_info = st.columns([1, 3])
with col_toggle:
    ai_enabled = st.toggle("🧠 Enable AI Assistant", value=st.session_state.ai_enabled, key="ai_toggle_widget")
    st.session_state.ai_enabled = ai_enabled

with col_info:
    if ai_enabled:
        st.success("AI Assistant is **enabled**. Requires an Anthropic API key in `.streamlit/secrets.toml`.")
        st.caption("⚠️ **Note:** AI-generated outputs may be imperfect. Always review suggestions before applying them.")
    else:
        st.info("AI Assistant is **disabled**. The app remains fully functional — automatic suggestions are always available below.")

st.markdown("---")

# ── DATASET PROFILE FOR AI CONTEXT ───────────────────────────────────────────
def build_profile(df):
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=["object","category"]).columns.tolist()
    missing  = df.isnull().sum()
    missing_info = {c: int(missing[c]) for c in df.columns if missing[c] > 0}
    profile = {
        "shape": {"rows": df.shape[0], "cols": df.shape[1]},
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "missing_values": missing_info,
        "duplicate_rows": int(df.duplicated().sum()),
        "sample_values": {c: df[c].dropna().head(3).tolist() for c in df.columns[:8]}
    }
    return profile

profile = build_profile(df)
profile_str = json.dumps(profile, indent=2, default=str)

SYSTEM_PROMPT = f"""You are a data science expert assistant built into a data wrangling app called DataWrangler Pro.
The user has uploaded a dataset with the following profile:

{profile_str}

Your job is to:
1. Suggest specific, actionable cleaning steps (missing values, duplicates, outliers, type conversions, standardization).
2. Recommend the best visualization types for their data and explain WHY — mention which columns to use on which axes.
3. Answer general data science questions clearly and concisely.
4. Always be specific — reference actual column names from the profile.
5. Keep responses concise and practical. Use bullet points where helpful.
6. If asked about a chart, suggest which columns to put on X and Y axes.
7. For natural language cleaning commands, describe exactly what transformation to apply and format it as:
   TRANSFORMATION: <description of what to do>
   PANDAS_CODE: <pandas code snippet>

The app has these pages: Upload, Cleaning, Visualization (histogram, bar, scatter, line, box, heatmap, 3D scatter, pie), Export.
When suggesting cleaning or visualization, guide the user to the right page.

IMPORTANT: Your outputs may be imperfect. Always remind the user to review suggestions before applying them."""

def call_claude(messages, max_tokens=1000):
    """Call Claude API; returns (reply_text, error_msg)."""
    api_key = ""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None, "API key not configured. Add `ANTHROPIC_API_KEY` to `.streamlit/secrets.toml`."
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "system": SYSTEM_PROMPT,
                "messages": messages
            },
            timeout=30
        )
        data = resp.json()
        if "content" in data:
            reply = "".join(b["text"] for b in data["content"] if b.get("type") == "text")
            return reply, None
        elif "error" in data:
            return None, f"API error: {data['error'].get('message', 'Unknown error')}"
        return None, "Unexpected API response."
    except Exception as e:
        return None, str(e)

# ══════════════════════════════════════════════════════════════════════════════
# AI FEATURES (only shown when enabled)
# ══════════════════════════════════════════════════════════════════════════════
if ai_enabled:
    mode = st.radio("What do you need help with?", [
        "💬 Free chat",
        "🧹 Natural language cleaning",
        "📊 Chart suggestions",
        "🐍 Code snippet generator",
        "📖 Data dictionary",
        "🔍 Full dataset analysis"
    ], horizontal=True, key="ai_mode")

    st.markdown("---")

    # ── QUICK ACTIONS ────────────────────────────────────────────────────────
    if mode == "🧹 Natural language cleaning":
        st.info("Describe what you want to do in plain English. The AI will suggest transformations for your confirmation before anything is applied.")
        nl_input = st.text_area("Describe the cleaning step:", placeholder="e.g. Replace null values in 'age' with the median. Standardize the 'country' column to title case. Remove rows where 'price' is negative.", key="nl_cleaning_input")
        if st.button("🔍 Suggest Transformation", key="nl_suggest") and nl_input:
            with st.spinner("Thinking…"):
                messages = [{
                    "role": "user",
                    "content": f"The user wants to: {nl_input}\n\nSuggest the exact transformation, reference column names from the dataset profile, and provide a pandas code snippet. Format your response with TRANSFORMATION: and PANDAS_CODE: labels."
                }]
                reply, err = call_claude(messages)
            if err:
                st.error(f"AI error: {err}")
            elif reply:
                st.markdown("**AI Suggestion:**")
                st.markdown(reply)
                st.warning("⚠️ Review the suggestion above carefully. Go to the **Cleaning** page to apply it manually, or use the code in your own environment.")

    elif mode == "📊 Chart suggestions":
        sel_cols = st.multiselect("Select columns to get chart suggestions for:", df.columns.tolist(), key="chart_sug_cols")
        if st.button("✨ Get Chart Suggestions", key="chart_suggest_btn"):
            with st.spinner("Thinking…"):
                col_list = sel_cols if sel_cols else df.columns.tolist()
                messages = [{
                    "role": "user",
                    "content": f"The user wants chart suggestions for these columns: {col_list}. Suggest 3-5 specific charts. For each: chart type, which column on X axis, which column on Y axis (if applicable), what insight it reveals, and how to find it in the Visualization page."
                }]
                reply, err = call_claude(messages)
            if err:
                st.error(f"AI error: {err}")
            elif reply:
                st.markdown(reply)

    elif mode == "🐍 Code snippet generator":
        code_request = st.text_area("What pandas code do you need?", placeholder="e.g. Code to fill missing values, normalize numeric columns, encode categoricals, etc.", key="code_request")
        if st.button("🐍 Generate Code", key="gen_code_btn") and code_request:
            with st.spinner("Generating code…"):
                messages = [{
                    "role": "user",
                    "content": f"Generate pandas code for: {code_request}. Use actual column names from the dataset profile. Include comments explaining each step. Start the variable name as 'df'."
                }]
                reply, err = call_claude(messages, max_tokens=1200)
            if err:
                st.error(f"AI error: {err}")
            elif reply:
                st.markdown(reply)
                st.caption("⚠️ AI-generated code may be imperfect — always test before using in production.")

    elif mode == "📖 Data dictionary":
        if st.button("📖 Generate Data Dictionary", key="data_dict_btn"):
            with st.spinner("Inferring column meanings…"):
                messages = [{
                    "role": "user",
                    "content": "Generate a data dictionary for this dataset. For each column: infer its likely meaning, note its data type, flag potential data quality issues (nulls, unexpected values), and suggest how it might be used in analysis. Format as a table."
                }]
                reply, err = call_claude(messages, max_tokens=1500)
            if err:
                st.error(f"AI error: {err}")
            elif reply:
                st.markdown(reply)
                st.caption("⚠️ Inferred meanings are AI-generated and may not be accurate for your specific dataset.")

    elif mode == "🔍 Full dataset analysis":
        if st.button("✨ Get Full Analysis", key="full_analysis_btn"):
            st.session_state.ai_messages = [{
                "role": "user",
                "content": "Give me a comprehensive analysis of my dataset: data quality issues, interesting patterns to explore, potential correlations, and what questions this data could answer."
            }]
            st.rerun()

    elif mode == "🧹 Suggest cleaning steps":
        if st.button("✨ Generate Cleaning Recommendations", key="clean_recs_btn"):
            st.session_state.ai_messages = [{
                "role": "user",
                "content": "Based on my dataset profile, what are the most important cleaning steps I should take? Be specific about which columns need attention and what method to use."
            }]
            st.rerun()

    # ── CHAT INTERFACE ────────────────────────────────────────────────────────
    if mode in ("💬 Free chat", "🔍 Full dataset analysis", "🧹 Suggest cleaning steps"):
        for msg in st.session_state.ai_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if st.session_state.ai_messages and st.session_state.ai_messages[-1]["role"] == "user":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply, err = call_claude(st.session_state.ai_messages)
                if err:
                    st.error(f"⚠️ {err}")
                    # Fallback suggestions
                    st.markdown("**Automatic suggestions based on your dataset profile:**")
                    missing_info = profile.get("missing_values", {})
                    if missing_info:
                        for col, count in list(missing_info.items())[:5]:
                            col_type = "numeric" if col in profile.get("numeric_columns", []) else "categorical"
                            method   = "mean or median" if col_type == "numeric" else "mode or 'Unknown'"
                            st.markdown(f"- `{col}`: {count} missing → fill with **{method}**")
                    reply = f"Could not connect to AI: {err}"
                else:
                    st.markdown(reply)
                st.session_state.ai_messages.append({"role": "assistant", "content": reply})

        if mode == "💬 Free chat":
            user_input = st.chat_input("Ask anything about your data…")
            if user_input:
                st.session_state.ai_messages.append({"role": "user", "content": user_input})
                st.rerun()

        if st.session_state.ai_messages:
            if st.button("🗑️ Clear conversation", key="clear_chat"):
                st.session_state.ai_messages = []
                st.rerun()

    # ── DATASET PROFILE SUMMARY ────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📋 Dataset Profile (sent to AI)", expanded=False):
        st.json(profile)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# RULE-BASED QUICK SUGGESTIONS (always visible, no AI required)
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("⚡ Quick Automatic Suggestions")
st.caption("These suggestions are generated automatically from your dataset — no AI required.")

tab1, tab2 = st.tabs(["🧹 Cleaning", "📊 Visualization"])

with tab1:
    missing_info = profile.get("missing_values", {})
    if not missing_info:
        st.success("No missing values detected!")
    else:
        for col, count in missing_info.items():
            pct      = round(count / df.shape[0] * 100, 1)
            col_type = "numeric" if col in profile.get("numeric_columns", []) else "categorical"
            if pct > 30:
                st.warning(f"**`{col}`** — {count} missing ({pct}%) — consider **dropping this column** (>30% missing)")
            elif col_type == "numeric":
                st.info(f"**`{col}`** — {count} missing ({pct}%) — fill with **mean** or **median**")
            else:
                st.info(f"**`{col}`** — {count} missing ({pct}%) — fill with **mode** (most frequent value)")

    dupes = profile.get("duplicate_rows", 0)
    if dupes > 0:
        st.warning(f"**{dupes} duplicate rows** detected — remove on the Cleaning page (keep first recommended)")

with tab2:
    num_cols = profile.get("numeric_columns", [])
    cat_cols = profile.get("categorical_columns", [])

    if num_cols:
        st.success(f"**Histogram** — explore distribution of `{num_cols[0]}`")
    if len(num_cols) >= 2:
        st.success(f"**Scatter plot** — look for relationship between `{num_cols[0]}` (X) and `{num_cols[1]}` (Y)")
    if len(num_cols) >= 2:
        st.success(f"**Correlation heatmap** — identify which numeric columns are correlated")
    if cat_cols and num_cols:
        st.success(f"**Bar chart** — compare average `{num_cols[0]}` across `{cat_cols[0]}` categories")
    if len(num_cols) >= 3:
        st.success(f"**3D Scatter** — visualize three variables at once: `{num_cols[0]}`, `{num_cols[1]}`, `{num_cols[2]}`")
    if cat_cols:
        st.success(f"**Pie chart** — see proportions of `{cat_cols[0]}`")
