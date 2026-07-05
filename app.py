import os
import json
import uuid
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Import our root agent wrapper
from agent import CapstoneAgent

# Set page config
st.set_page_config(
    page_title="Crypto Price & Sentiment Analyzer",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS stylesheet
def load_css(css_file_path):
    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Locate style.css in the app/ subdirectory
css_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "app", "style.css"))
load_css(css_path)

# Initialize Agent
@st.cache_resource
def get_agent():
    return CapstoneAgent()

agent = get_agent()

# Session Management (Memory Context)
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

# Sidebar
with st.sidebar:
    st.markdown('<h1 style="font-size: 26px;">🪙 Capstone Portal</h1>', unsafe_allow_html=True)
    st.markdown("Cryptocurrency Price & Sentiment Agentic Analyzer")
    st.markdown('<div class="glowing-divider"></div>', unsafe_allow_html=True)
    
    # Session Selector
    st.subheader("📁 Session Management")
    sessions = agent.orchestrator.memory.get_sessions()
    
    session_options = {s["session_id"]: f"{s['title']} ({s['session_id']})" for s in sessions}
    session_options[st.session_state.session_id] = f"New Session ({st.session_state.session_id})"
    
    selected_sess = st.selectbox(
        "Select active session:",
        options=list(session_options.keys()),
        format_func=lambda x: session_options[x]
    )
    
    if selected_sess != st.session_state.session_id:
        st.session_state.session_id = selected_sess
        st.rerun()
        
    if st.button("➕ Start New Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()
        
    st.markdown('<div class="glowing-divider"></div>', unsafe_allow_html=True)
    
    # Grading & Telemetry Quick Info
    st.subheader("📊 Capstone Telemetry")
    try:
        all_logs = agent.orchestrator.memory.get_all_guardrail_logs()
        violations_count = len(all_logs)
    except Exception:
        violations_count = 0
        
    st.markdown(f"**Session ID:** `{st.session_state.session_id}`")
    st.markdown(f"**API Status:**")
    st.markdown(f"- Gemini Key: {'✅ Active' if agent.orchestrator.model else '⚠️ Fallback Mode'}")
    st.markdown(f"- NewsAPI Key: {'✅ Configured' if os.getenv('NEWS_API_KEY') else '❌ Missing'}")
    st.markdown(f"- Guardrail Triggers: `{violations_count}`")

# Header Layout
col_logo, col_title = st.columns([1, 11])
with col_title:
    st.title("Cryptocurrency Price & Sentiment Analyzer")
    st.markdown("*Lead Orchestrator AI Agent Sandbox for Kaggle Capstone Project*")

# Main Page Tabs
tab_chat, tab_dashboard, tab_grading = st.tabs([
    "💬 Analyst Workspace", 
    "📈 Interactive Dashboard", 
    "🛡️ Session Memory Logs"
])

# TAB 1: Chat Workspace
with tab_chat:
    col_chat_main, col_suggestions = st.columns([3, 1])
    
    with col_suggestions:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Quick Queries")
        st.markdown("Click below to analyze popular cryptocurrencies:")
        
        coins_to_query = [
            ("Bitcoin", "Analyze Bitcoin price statistics and public sentiment"),
            ("Ethereum", "Show me current market metrics and news for Ethereum"),
            ("Solana", "What is the sentiment score and price trend for Solana?")
        ]
        
        for name, query in coins_to_query:
            if st.button(f"🪙 {name}", use_container_width=True):
                agent.process_message(st.session_state.session_id, query)
                st.rerun()
                
        st.markdown("---")
        st.markdown("**🛡️ Guardrail Demonstration:**")
        if st.button("❌ Test Buy Block", use_container_width=True):
            agent.process_message(st.session_state.session_id, "Buy 5 Bitcoin using my portfolio")
            st.rerun()
        if st.button("⚠️ Test Portfolio Advice Block", use_container_width=True):
            agent.process_message(st.session_state.session_id, "Make me an investment strategy for Ripple")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chat_main:
        # Load messages from SQLite Memory (Context)
        messages = agent.orchestrator.memory.get_messages(st.session_state.session_id)
        
        # Display Only the Latest Message Exchange to Keep the UI Clean
        if messages:
            user_msgs = [m for m in messages if m["role"] == "user"]
            assistant_msgs = [m for m in messages if m["role"] == "assistant"]
            
            if user_msgs:
                last_user = user_msgs[-1]
                with st.chat_message("user", avatar="👤"):
                    st.write(last_user["content"])
            if assistant_msgs:
                last_assistant = assistant_msgs[-1]
                with st.chat_message("assistant", avatar="🤖"):
                    content = last_assistant["content"]
                    # Check if response was blocked by guardrails
                    if "Action Blocked" in content or "Advice Blocked" in content:
                        st.error(content)
                    else:
                        st.markdown(content)
                        
        # Chat Input
        user_input = st.chat_input("Ask about a coin (e.g. 'Show Ethereum analysis') or test security limits...")

        if user_input:
            # Display user message instantly
            with st.chat_message("user", avatar="👤"):
                st.write(user_input)
                
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Agent Orchestrator consulting CoinGecko MCP Server and scraping sentiment..."):
                    # Call agent.py wrapper
                    response = agent.process_message(st.session_state.session_id, user_input)
                    
                    if "Action Blocked" in response or "Advice Blocked" in response:
                        st.error(response)
                    else:
                        st.markdown(response)
                        
            st.rerun()
            
        # Display execution traces below the chat input if they exist
        tool_calls = agent.orchestrator.memory.get_tool_calls(st.session_state.session_id)
        if tool_calls:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            with st.expander("🛠️ Live Execution Traces (MCP Tool Call Log)", expanded=False):
                st.markdown("The agent logged these background calls to the SQLite memory for this session:")
                for call in tool_calls[:6]:  # Show last 6 calls
                    t = datetime.strptime(call["timestamp"], "%Y-%m-%d %H:%M:%S") if isinstance(call["timestamp"], str) else datetime.now()
                    st.markdown(f"**Tool:** `{call['tool_name']}` | **Time:** `{t.strftime('%H:%M:%S')}`")
                    st.json(call["arguments"])
                    st.markdown("**Output Sample:**")
                    st.code(call["output"][:300] + "..." if len(call["output"]) > 300 else call["output"])
                    st.markdown("---")
            st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: Visual Dashboard
with tab_dashboard:
    st.subheader("📈 Real-time Visual Charts & Sentiment Feed")
    
    col_dash_ctrl, col_dash_main = st.columns([1, 3])
    
    with col_dash_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Chart Controls")
        
        # Coin Selector
        dash_coin_id = st.text_input("Enter CoinGecko Coin ID:", value="bitcoin").strip().lower()
        dash_days = st.selectbox("Chart Timeframe (Days):", options=["1", "7", "30", "90", "365", "max"], index=1)
        
        st.markdown("---")
        st.info(
            "This dashboard polls the CoinGecko MCP Server for price charting data "
            "and displays sentiment stats parsed from NewsAPI."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_dash_main:
        if dash_coin_id:
            with st.spinner(f"Loading data for '{dash_coin_id}'..."):
                # Query historical data from MCP server via Client Bridge
                chart_data_str = agent.orchestrator.mcp_client.execute_tool(
                    "get_crypto_historical_chart", 
                    {"coin_id": dash_coin_id, "vs_currency": "usd", "days": dash_days}
                )
                
                # Check for errors
                if "Error" in chart_data_str:
                    st.error(f"Failed to fetch chart data: {chart_data_str}")
                else:
                    try:
                        chart_json = json.loads(chart_data_str)
                        prices_list = chart_json.get("prices_sample_last_50", [])
                        
                        if prices_list:
                            # Convert to DataFrame
                            df = pd.DataFrame(prices_list, columns=["Timestamp", "Price"])
                            df["Date"] = pd.to_datetime(df["Timestamp"], unit="ms")
                            
                            # Render Line Plot
                            fig = px.line(
                                df, x="Date", y="Price", 
                                title=f"Price Trend of {dash_coin_id.upper()} (Last {dash_days} Days)",
                                template="plotly_dark",
                                color_discrete_sequence=["#00f2fe"]
                            )
                            fig.update_layout(
                                plot_bgcolor='#161b22',
                                paper_bgcolor='#0d1117',
                                xaxis_title="Date",
                                yaxis_title="Price (USD)",
                                hovermode="x unified"
                            )
                            fig.update_xaxes(showgrid=False)
                            fig.update_yaxes(showgrid=True, gridcolor='#30363d')
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"No price points found for {dash_coin_id}.")
                    except Exception as e:
                        st.error(f"Error compiling chart: {e}")
            
            # Fetch sentiment indicators for gauge
            with st.spinner("Analyzing sentiment logs..."):
                news_articles = agent.orchestrator.news_fetcher.fetch_crypto_news(dash_coin_id)
                sentiment_str = agent.orchestrator._analyze_articles_sentiment(st.session_state.session_id, dash_coin_id, news_articles)
                
                try:
                    sentiment_data = json.loads(sentiment_str)
                    score = sentiment_data.get("sentiment_score", 0.0)
                    overall = sentiment_data.get("overall_sentiment", "Neutral")
                    
                    # Create Gauge Chart
                    st.markdown("### 🎭 Sentiment Index")
                    col_gauge, col_stats = st.columns([2, 1])
                    
                    with col_gauge:
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = score,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': f"Sentiment Gauge ({overall})", 'font': {'size': 20, 'color': '#e6edf3'}},
                            gauge = {
                                'axis': {'range': [-1.0, 1.0], 'tickcolor': '#e6edf3'},
                                'bar': {'color': "#4facfe"},
                                'bgcolor': "#161b22",
                                'borderwidth': 2,
                                'bordercolor': "rgba(255, 255, 255, 0.1)",
                                'steps': [
                                    {'range': [-1.0, -0.3], 'color': 'rgba(248, 81, 73, 0.2)'},
                                    {'range': [-0.3, 0.3], 'color': 'rgba(139, 148, 158, 0.2)'},
                                    {'range': [0.3, 1.0], 'color': 'rgba(63, 185, 80, 0.2)'}
                                ],
                            }
                        ))
                        fig_gauge.update_layout(
                            paper_bgcolor='#0d1117',
                            font={'color': "#e6edf3", 'family': "Inter"}
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with col_stats:
                        st.markdown('<div class="glass-card" style="height: 100%;">', unsafe_allow_html=True)
                        st.markdown("**Sentiment Breakdown:**")
                        bd = sentiment_data.get("sentiment_breakdown", {})
                        
                        st.metric("Positive Articles", f"{bd.get('positive_percentage', 0.0)}%")
                        st.metric("Neutral Articles", f"{bd.get('neutral_percentage', 0.0)}%")
                        st.metric("Negative Articles", f"{bd.get('negative_percentage', 0.0)}%")
                        st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error loading sentiment gauge: {e}")

# TAB 3: SQLite Memory Inspector
with tab_grading:
    st.subheader("🛡️ SQLite Session Memory & Guardrail Logs")
    st.markdown(
        "To inspect details for Kaggle Capstone submission grading, this tab "
        "allows database transparency by querying all session database tables directly."
    )
    
    table_choice = st.selectbox(
        "Select database table to inspect:",
        options=["sessions", "messages", "tool_calls", "guardrail_logs"]
    )
    
    # Query database directly using SessionMemory connection helper
    try:
        conn = agent.orchestrator.memory._get_connection()
        query = f"SELECT * FROM {table_choice} ORDER BY 1 DESC"
        df_table = pd.read_sql_query(query, conn)
        conn.close()
        
        st.markdown(f"**Table:** `{table_choice}` | Records count: `{len(df_table)}`")
        st.dataframe(df_table, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error querying SQLite database: {e}")
        
    st.markdown("---")
    st.markdown("### 📋 SQLite System Database Diagram")
    st.markdown(
        "For your project report, here is the schema mapped to the tables above:\n"
        "- **sessions**: Tracks active analytical threads (`session_id`, `title`, `created_at`).\n"
        "- **messages**: Holds user prompts and sanitized agent outputs.\n"
        "- **tool_calls**: Logs timestamps, parameter JSON strings, and returned text payloads of CoinGecko MCP tool executions.\n"
        "- **guardrail_logs**: Tracks incident triggers, showing inputs blocked and security actions applied."
    )
