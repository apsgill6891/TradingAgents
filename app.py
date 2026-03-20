import streamlit as st
from datetime import date, timedelta
import sys
import os

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Fix broken SSL_CERT_FILE path in conda environments
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create required directories
os.makedirs("./results", exist_ok=True)
os.makedirs("./tradingagents/dataflows/data_cache", exist_ok=True)

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TradingAgents AI",
    page_icon="📈",
    layout="wide"
)

st.title("📈 TradingAgents — AI Stock Analysis")
st.caption("Multi-agent LLM framework: analysts → debate → risk team → decision")
st.divider()

# ── Sidebar: Settings ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")

    provider = st.selectbox(
        "LLM Provider",
        ["openai", "anthropic", "google", "xai", "openrouter", "ollama"],
        index=0,
        help="Choose which AI provider to use"
    )

    # Sensible model defaults per provider
    default_quick = {
        "openai":      "gpt-4o-mini",
        "anthropic":   "claude-haiku-4-5",
        "google":      "gemini-2.5-flash",
        "xai":         "grok-3-mini",
        "openrouter":  "openai/gpt-4o-mini",
        "ollama":      "llama3.2",
    }
    default_deep = {
        "openai":      "gpt-4o",
        "anthropic":   "claude-opus-4-5",
        "google":      "gemini-2.5-pro",
        "xai":         "grok-3",
        "openrouter":  "openai/gpt-4o",
        "ollama":      "llama3.1",
    }

    quick_model = st.text_input(
        "Quick-Thinking Model",
        value=default_quick.get(provider, "gpt-4o-mini"),
        help="Used for fast reasoning steps"
    )
    deep_model = st.text_input(
        "Deep-Thinking Model",
        value=default_deep.get(provider, "gpt-4o"),
        help="Used for complex analysis steps"
    )

    st.divider()

    depth = st.select_slider(
        "Research Depth",
        options=[1, 3, 5],
        value=1,
        format_func=lambda x: {1: "🔹 Shallow (fast)", 3: "🔸 Medium", 5: "🔴 Deep (slow)"}[x],
        help="More rounds = more thorough but slower & costlier"
    )

    st.divider()

    st.subheader("🧑‍💼 Analysts Team")
    use_market       = st.checkbox("📊 Market / Technical", value=True)
    use_news         = st.checkbox("📰 News",               value=True)
    use_social       = st.checkbox("💬 Social Media",       value=True)
    use_fundamentals = st.checkbox("📋 Fundamentals",       value=True)

# ── Main: Inputs ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input(
        "🔎 Stock Ticker",
        value="NVDA",
        placeholder="e.g. AAPL, TSLA, NVDA, SPY"
    ).upper().strip()

with col2:
    analysis_date = st.date_input(
        "📅 Analysis Date",
        value=date.today() - timedelta(days=1),
        max_value=date.today() - timedelta(days=1),
        help="Date to run the analysis for (must be a past trading day)"
    )

run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# ── Run ───────────────────────────────────────────────────────────────────────
if run_btn:
    analysts = []
    if use_market:       analysts.append("market")
    if use_news:         analysts.append("news")
    if use_social:       analysts.append("social")
    if use_fundamentals: analysts.append("fundamentals")

    if not ticker:
        st.error("⚠️ Please enter a stock ticker.")
    elif not analysts:
        st.error("⚠️ Please select at least one analyst.")
    else:
        st.info(f"Running **{len(analysts)} analysts** on **{ticker}** for **{analysis_date}** using **{provider} / {deep_model}** …")

        with st.spinner("⏳ Agents are working… this can take 1–5 minutes depending on depth and model."):
            try:
                config = DEFAULT_CONFIG.copy()
                config["llm_provider"]          = provider
                config["quick_think_llm"]        = quick_model
                config["deep_think_llm"]         = deep_model
                config["max_debate_rounds"]      = depth
                config["max_risk_discuss_rounds"]= depth

                ta = TradingAgentsGraph(
                    selected_analysts=analysts,
                    debug=False,
                    config=config
                )

                state, decision = ta.propagate(ticker, str(analysis_date))

                st.success("✅ Analysis complete!")
                st.divider()

                # ── Decision banner ───────────────────────────────────────────
                decision_str = str(decision).upper()
                if "BUY" in decision_str:
                    st.success(f"# 📈 Decision: {decision}")
                elif "SELL" in decision_str:
                    st.error(f"# 📉 Decision: {decision}")
                else:
                    st.warning(f"# ⏸️ Decision: {decision}")

                st.divider()

                # ── Full report ───────────────────────────────────────────────
                if state.get("final_trade_decision"):
                    with st.expander("📄 Full Trading Report", expanded=True):
                        st.markdown(state["final_trade_decision"])

                # ── Individual analyst reports ────────────────────────────────
                report_map = {
                    "market_report":       "📊 Market / Technical Analysis",
                    "sentiment_report":    "💬 Social Sentiment Analysis",
                    "news_report":         "📰 News Analysis",
                    "fundamentals_report": "📋 Fundamentals Analysis",
                }

                for key, label in report_map.items():
                    if state.get(key):
                        with st.expander(label):
                            st.markdown(state[key])

            except Exception as e:
                import traceback
                st.error(f"❌ Error: {e}")
                st.code(traceback.format_exc(), language="python")
                st.info("💡 Check that your API keys are correctly set in the `.env` file and the model name is valid for your chosen provider.")
