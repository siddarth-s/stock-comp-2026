import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Market Championship 2026",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

ANCHOR_DATE   = "2026-02-27"   # Prices locked to Feb 27, 2026 (last market close before comp)
COMP_START    = "2026-03-01"   # Official competition start (display reference)
END_DATE      = "2026-12-31"
INITIAL       = 1000  # $ per stock
TOTAL_INV     = 4000  # $ total

HUMAN_PARTICIPANTS = {
    "Singh":  ["MU",   "AAPL", "GLD",  "COST"],
    "Vishal": ["RKLB", "WDC",  "ASML", "GE"],
    "Saurya": ["GME",  "HOOD", "HYMC", "RCAT"],
    "Achu":   ["ASTS", "POET", "META", "SLV"],
    "Pod":    ["NVDA", "AVGO", "SMCI", "SNOW"],
    "Adi":    ["SNDK", "AMZN", "AGI",  "NFLX"],
    "Nikhil": ["SOFI", "MSFT", "PANW", "NVO"],
    "Siddu":  ["PLTR", "COIN", "TSLA", "TSM"],
    "Nari":   ["GOOG", "AMD",  "BABA", "RIVN"],
    "Vikas":  ["MRVL", "FLY",  "INTC", "TMC"],
}

AI_PARTICIPANTS = {
    "Claude":   ["CEG",  "APP",  "AXON", "ARM"],
    "Gemini":   ["KLAC", "VRT",  "CDNS", "DDOG"],
    "DeepSeek": ["UBER", "CELH", "CRWD", "LUNR"],
    "ChatGPT":  ["LLY",  "DELL", "MSTR", "NOW"],
    "Grok":     ["ANET", "BSX",  "V",    "ISRG"],
    "Llama":    ["MDB",  "ZS",   "SNPS", "ADSK"],
    "Mistral":  ["VKTX", "SONY", "ACLX", "USAR"],
}

BENCHMARKS = {
    "S&P 500 (SPY)":    "SPY",
    "Nasdaq (QQQ)":     "QQQ",
    "Bitcoin (BTC)":    "BTC-USD",
    "USD Index (UUP)":  "UUP",
}

ALL_PARTICIPANTS = {**HUMAN_PARTICIPANTS, **AI_PARTICIPANTS}

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1526 50%, #0a1020 100%);
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s, border-color 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(99, 179, 237, 0.3);
}

.metric-rank {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 3px;
    color: #718096;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.metric-name {
    font-size: 22px;
    font-weight: 800;
    color: #e2e8f0;
    margin-bottom: 4px;
}

.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: #63b3ed;
    margin-bottom: 4px;
}

.metric-return {
    font-family: 'Space Mono', monospace;
    font-size: 16px;
    font-weight: 700;
}

.positive { color: #68d391; }
.negative { color: #fc8181; }

.gold   { border-top: 3px solid #F6D860; }
.silver { border-top: 3px solid #C0C0C0; }
.bronze { border-top: 3px solid #CD7F32; }

/* Section headers */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #4a5568;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(10,14,26,0.95);
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
}

.winner-badge {
    background: linear-gradient(135deg, #F6D860, #f6ad55);
    color: #1a202c;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px;
    display: inline-block;
}

.stDataFrame { border-radius: 12px; overflow: hidden; }

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices(tickers: list, start: str, end: str):
    today = date.today().isoformat()
    actual_end = min(end, today)

    # Clamp start — if start is in the future, pull back to today so we at least get something
    if start > today:
        start = today

    missing = []
    frames = {}

    # Download all tickers at once for efficiency, fall back to individual if needed
    try:
        raw = yf.download(
            tickers,
            start=start,
            end=actual_end,
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as e:
        raw = pd.DataFrame()

    if not raw.empty:
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    series = raw["Close"]
                else:
                    if ticker in raw.columns.get_level_values(0):
                        series = raw[ticker]["Close"]
                    else:
                        missing.append(ticker)
                        continue

                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                series = series.dropna()
                if len(series) < 2:
                    missing.append(ticker)
                    continue
                series.name = ticker
                frames[ticker] = series
            except Exception:
                missing.append(ticker)
    else:
        missing = list(tickers)

    # For any that failed in bulk, try individually
    retry_missing = []
    for ticker in missing:
        try:
            data = yf.download(ticker, start=start, end=actual_end,
                               auto_adjust=True, progress=False)
            if data.empty or len(data) < 2:
                retry_missing.append(ticker)
                continue
            close = data["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            close = close.dropna()
            if len(close) < 2:
                retry_missing.append(ticker)
                continue
            close.name = ticker
            frames[ticker] = close
        except Exception:
            retry_missing.append(ticker)

    if not frames:
        return pd.DataFrame(), list(tickers)

    prices = pd.DataFrame(frames)
    prices.index = pd.to_datetime(prices.index)
    prices.sort_index(inplace=True)

    if retry_missing:
        st.sidebar.warning(f"⚠️ Missing tickers (0% return assumed): {', '.join(retry_missing)}")

    return prices, retry_missing


def compute_portfolio_values(prices: pd.DataFrame, participants: dict, missing_tickers: list, anchor_date: str = COMP_START) -> pd.DataFrame:
    portfolios = {}

    # Find the actual anchor — first index on or after anchor_date
    anchor_ts = pd.Timestamp(anchor_date)
    available_dates = prices.index[prices.index >= anchor_ts]
    if len(available_dates) == 0:
        # Fallback: use first available date in data (preview mode before comp starts)
        available_dates = prices.index
    actual_anchor = available_dates[0]

    for name, tickers in participants.items():
        total = pd.Series(0.0, index=prices.index)
        for ticker in tickers:
            if ticker in prices.columns and ticker not in missing_tickers:
                series = prices[ticker].ffill()
                anchor_price = series.get(actual_anchor, None)
                if anchor_price is None or pd.isna(anchor_price):
                    # find nearest valid price
                    valid = series.dropna()
                    if valid.empty:
                        total += INITIAL
                        continue
                    anchor_price = valid.iloc[0]
                ratio = series / anchor_price
                total += ratio * INITIAL
            else:
                total += INITIAL  # 0% return assumption
        portfolios[name] = total

    df = pd.DataFrame(portfolios)
    # Only show data from anchor date onward in charts
    return df[df.index >= actual_anchor]


def compute_benchmark_values(prices: pd.DataFrame, missing_tickers: list, anchor_date: str = COMP_START) -> pd.DataFrame:
    anchor_ts = pd.Timestamp(anchor_date)
    available_dates = prices.index[prices.index >= anchor_ts]
    if len(available_dates) == 0:
        available_dates = prices.index
    actual_anchor = available_dates[0]

    benchmarks = {}
    for label, ticker in BENCHMARKS.items():
        if ticker in prices.columns and ticker not in missing_tickers:
            series = prices[ticker].ffill()
            anchor_price = series.get(actual_anchor, None)
            if anchor_price is None or pd.isna(anchor_price):
                valid = series.dropna()
                if valid.empty:
                    continue
                anchor_price = valid.iloc[0]
            ratio = series / anchor_price
            benchmarks[label] = ratio * TOTAL_INV
    df = pd.DataFrame(benchmarks)
    return df[df.index >= actual_anchor]


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 Championship 2026")
    st.markdown('<p style="color:#4a5568;font-size:12px;font-family:\'Space Mono\',monospace;">MAR 01 – DEC 31, 2026</p>', unsafe_allow_html=True)
    st.divider()
    
    filter_opt = st.radio(
        "**Participant Filter**",
        ["All Participants", "Human Only", "AI Only"],
        index=0,
    )
    
    st.divider()
    st.markdown('<p style="color:#4a5568;font-size:11px;">Initial investment: $1,000 per stock<br>Total per portfolio: $4,000</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FILTER PARTICIPANTS
# ─────────────────────────────────────────────
if filter_opt == "Human Only":
    active_participants = HUMAN_PARTICIPANTS
elif filter_opt == "AI Only":
    active_participants = AI_PARTICIPANTS
else:
    active_participants = ALL_PARTICIPANTS


# ─────────────────────────────────────────────
# FETCH DATA
# ─────────────────────────────────────────────
all_tickers = list(set(
    t for p in ALL_PARTICIPANTS.values() for t in p
)) + list(BENCHMARKS.values())

with st.spinner("📡 Fetching market data..."):
    prices, missing_tickers = fetch_prices(all_tickers, ANCHOR_DATE, END_DATE)

if prices.empty:
    st.error("Could not fetch any price data. Please check your internet connection.")
    st.stop()

# ─────────────────────────────────────────────
# COMPUTE
# ─────────────────────────────────────────────
today_str = date.today().isoformat()

# All returns are anchored to Feb 27, 2026 close prices (locked pre-competition baseline)
anchor = ANCHOR_DATE

portfolio_df   = compute_portfolio_values(prices, active_participants, missing_tickers, anchor_date=anchor)
benchmark_df   = compute_benchmark_values(prices, missing_tickers, anchor_date=anchor)
all_portfolio  = compute_portfolio_values(prices, ALL_PARTICIPANTS, missing_tickers, anchor_date=anchor)

if portfolio_df.empty:
    st.error("No portfolio data could be computed.")
    st.stop()

# Latest values & returns
latest         = portfolio_df.iloc[-1]
returns_pct    = ((latest - TOTAL_INV) / TOTAL_INV * 100).round(2)
leaderboard    = pd.DataFrame({
    "Participant":    latest.index,
    "Portfolio ($)":  latest.values,
    "Return (%)":     returns_pct.values,
}).sort_values("Portfolio ($)", ascending=False).reset_index(drop=True)
leaderboard.index += 1
leaderboard["Rank"] = leaderboard.index
leaderboard["Type"] = leaderboard["Participant"].apply(
    lambda x: "🤖 AI" if x in AI_PARTICIPANTS else "👤 Human"
)

# Color palette
N      = len(active_participants)
colors = px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.Alphabet
colors = colors[:N]

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 32px 0 16px 0;">
    <h1 style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;
               background:linear-gradient(135deg,#e2e8f0,#63b3ed);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin:0;line-height:1.1;">
        Stock Market<br>Championship 2026
    </h1>
    <p style="color:#4a5568;font-family:'Space Mono',monospace;font-size:12px;
              letter-spacing:3px;margin-top:8px;">
        LIVE COMPETITION TRACKER · BASELINE: FEB 27, 2026
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆  Leaderboard",
    "📊  Benchmarks",
    "📅  Monthly Breakdown",
    "🔍  Deep Dive",
])

# ══════════════════════════════════════════════
# TAB 1: LEADERBOARD
# ══════════════════════════════════════════════
with tab1:
    # Top 3 metric cards
    top3     = leaderboard.head(3)
    medals   = ["gold", "silver", "bronze"]
    medal_lbl = ["🥇 1ST PLACE", "🥈 2ND PLACE", "🥉 3RD PLACE"]
    
    cols = st.columns(3)
    for i, (col, (_, row)) in enumerate(zip(cols, top3.iterrows())):
        ret_color = "positive" if row["Return (%)"] >= 0 else "negative"
        ret_sign  = "+" if row["Return (%)"] >= 0 else ""
        with col:
            st.markdown(f"""
            <div class="metric-card {medals[i]}">
                <div class="metric-rank">{medal_lbl[i]}</div>
                <div class="metric-name">{row['Participant']}</div>
                <div class="metric-value">${row['Portfolio ($)']:,.2f}</div>
                <div class="metric-return {ret_color}">{ret_sign}{row['Return (%)']:.2f}%</div>
                <div style="font-size:11px;color:#4a5568;margin-top:4px;">{row['Type']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Full Leaderboard</div>', unsafe_allow_html=True)
    
    # Table
    display_lb = leaderboard[["Rank","Type","Participant","Portfolio ($)","Return (%)"]].copy()
    display_lb["Portfolio ($)"] = display_lb["Portfolio ($)"].map("${:,.2f}".format)
    display_lb["Return (%)"]    = display_lb["Return (%)"].map("{:+.2f}%".format)
    
    st.dataframe(
        display_lb,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank":          st.column_config.NumberColumn("Rank", width="small"),
            "Type":          st.column_config.TextColumn("Type", width="small"),
            "Participant":   st.column_config.TextColumn("Participant"),
            "Portfolio ($)": st.column_config.TextColumn("Portfolio Value"),
            "Return (%)":    st.column_config.TextColumn("Total Return"),
        }
    )
    
    st.markdown('<div class="section-header">Portfolio Value Over Time</div>', unsafe_allow_html=True)
    
    # Line chart
    fig = go.Figure()
    for i, col_name in enumerate(portfolio_df.columns):
        fig.add_trace(go.Scatter(
            x=portfolio_df.index,
            y=portfolio_df[col_name],
            name=col_name,
            line=dict(width=2, color=colors[i % len(colors)]),
            hovertemplate=f"<b>{col_name}</b><br>Date: %{{x|%b %d}}<br>Value: $%{{y:,.2f}}<extra></extra>"
        ))
    
    fig.add_hline(y=TOTAL_INV, line_dash="dot", line_color="rgba(255,255,255,0.2)",
                  annotation_text="Initial $4,000", annotation_position="bottom right")
    
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0aec0", family="Space Mono"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", showgrid=True),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", showgrid=True, tickprefix="$", tickformat=",.0f"),
        hovermode="x unified",
        height=500,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2: BENCHMARKS
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Portfolio vs Benchmarks</div>', unsafe_allow_html=True)
    
    avg_portfolio = portfolio_df.mean(axis=1)
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=avg_portfolio.index, y=avg_portfolio,
        name=f"Avg Portfolio ({filter_opt})",
        line=dict(width=3, color="#63b3ed"),
        fill="tozeroy", fillcolor="rgba(99,179,237,0.05)",
        hovertemplate="<b>Avg Portfolio</b><br>$%{y:,.2f}<extra></extra>"
    ))
    
    bm_colors = ["#F6D860","#68d391","#fc8181","#b794f4"]
    for i, col_name in enumerate(benchmark_df.columns):
        fig2.add_trace(go.Scatter(
            x=benchmark_df.index, y=benchmark_df[col_name],
            name=col_name,
            line=dict(width=2, color=bm_colors[i % len(bm_colors)], dash="dash"),
            hovertemplate=f"<b>{col_name}</b><br>$%{{y:,.2f}}<extra></extra>"
        ))
    
    fig2.add_hline(y=TOTAL_INV, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0aec0", family="Space Mono"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=",.0f"),
        hovermode="x unified",
        height=500,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Benchmark stats
    if not benchmark_df.empty:
        st.markdown('<div class="section-header">Benchmark Performance</div>', unsafe_allow_html=True)
        bm_latest = benchmark_df.iloc[-1]
        bm_return = ((bm_latest - TOTAL_INV) / TOTAL_INV * 100).round(2)
        bm_df = pd.DataFrame({
            "Benchmark": bm_latest.index,
            "Current Value": bm_latest.map("${:,.2f}".format),
            "Return": bm_return.map("{:+.2f}%".format),
        })
        st.dataframe(bm_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# TAB 3: MONTHLY BREAKDOWN
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Monthly Performance</div>', unsafe_allow_html=True)
    
    # Resample to month-end
    monthly = portfolio_df.resample("ME").last()
    
    # Dollar change per month
    prev = monthly.shift(1)
    prev.iloc[0] = TOTAL_INV  # first month compared to initial
    monthly_gain = monthly - prev
    monthly_pct  = (monthly_gain / prev * 100).round(2)
    
    if not monthly_gain.empty:
        # Heatmap of % returns
        months_fmt = monthly_pct.index.strftime("%b %Y")
        
        fig3 = go.Figure(data=go.Heatmap(
            z=monthly_pct.T.values,
            x=months_fmt,
            y=monthly_pct.columns.tolist(),
            colorscale=[
                [0.0,  "#7b2d2d"],
                [0.4,  "#2d3748"],
                [0.5,  "#2d3748"],
                [0.6,  "#2d3748"],
                [1.0,  "#276749"],
            ],
            zmid=0,
            text=monthly_pct.T.values,
            texttemplate="%{text:.1f}%",
            textfont=dict(size=11, family="Space Mono"),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Return: %{z:.2f}%<extra></extra>",
            colorbar=dict(
                tickformat=".1f",
                ticksuffix="%",
                outlinewidth=0,
                bgcolor="rgba(0,0,0,0)",
            )
        ))
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a0aec0", family="Space Mono", size=12),
            height=max(400, 30 * len(portfolio_df.columns) + 80),
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(side="top"),
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        # Month winners
        st.markdown('<div class="section-header">Monthly Winners</div>', unsafe_allow_html=True)
        
        completed_months = monthly_gain.index[monthly_gain.index < pd.Timestamp(date.today())]
        
        if len(completed_months) > 0:
            winner_data = []
            for m in completed_months:
                row   = monthly_gain.loc[m]
                winner = row.idxmax()
                gain   = row.max()
                ret    = monthly_pct.loc[m, winner]
                winner_data.append({
                    "Month":        m.strftime("%B %Y"),
                    "Winner":       winner,
                    "Dollar Gain":  f"+${gain:,.2f}",
                    "Monthly Return": f"+{ret:.2f}%",
                    "Type":         "🤖 AI" if winner in AI_PARTICIPANTS else "👤 Human"
                })
            
            wdf = pd.DataFrame(winner_data)
            st.dataframe(wdf, use_container_width=True, hide_index=True)
        else:
            st.info("No completed months yet — check back after March 31, 2026.")
    else:
        st.info("Not enough data for monthly breakdown yet.")


# ══════════════════════════════════════════════
# TAB 4: INDIVIDUAL DEEP DIVE
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Individual Portfolio Analysis</div>', unsafe_allow_html=True)
    
    participant_names = list(active_participants.keys())
    selected = st.selectbox("Select Participant", participant_names, key="deep_dive")
    
    if selected:
        tickers = active_participants[selected]
        part_type = "🤖 AI" if selected in AI_PARTICIPANTS else "👤 Human"
        
        # Individual stock values — anchored same as main portfolio
        anchor_ts_dd = pd.Timestamp(anchor)
        avail_dd = prices.index[prices.index >= anchor_ts_dd]
        actual_anchor_dd = avail_dd[0] if len(avail_dd) > 0 else prices.index[0]

        stock_vals = {}
        for ticker in tickers:
            if ticker in prices.columns and ticker not in missing_tickers:
                series = prices[ticker].ffill()
                ap = series.get(actual_anchor_dd) if actual_anchor_dd in series.index else None
                if ap is None or pd.isna(ap):
                    valid = series.dropna()
                    ap = valid.iloc[0] if not valid.empty else None
                if ap:
                    stock_vals[ticker] = (series / ap) * INITIAL
                else:
                    stock_vals[ticker] = pd.Series(INITIAL, index=prices.index)
            else:
                stock_vals[ticker] = pd.Series(INITIAL, index=prices.index)

        stock_df = pd.DataFrame(stock_vals)
        stock_df = stock_df[stock_df.index >= actual_anchor_dd]
        
        # Summary metrics
        s_latest = stock_df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        stock_colors_ind = ["#63b3ed","#68d391","#F6D860","#fc8181"]
        
        for i, (col, ticker) in enumerate(zip([col1,col2,col3,col4], tickers)):
            val = s_latest.get(ticker, INITIAL)
            ret = (val - INITIAL) / INITIAL * 100
            ret_str = f"{ret:+.2f}%"
            with col:
                color = "#68d391" if ret >= 0 else "#fc8181"
                st.markdown(f"""
                <div class="metric-card" style="border-top:3px solid {stock_colors_ind[i]};">
                    <div class="metric-rank">{ticker}</div>
                    <div class="metric-value" style="font-size:20px;">${val:,.2f}</div>
                    <div class="metric-return" style="color:{color};">{ret_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Total
        total_val = s_latest.sum()
        total_ret = (total_val - TOTAL_INV) / TOTAL_INV * 100
        
        st.markdown(f"""
        <div style="text-align:center;margin:16px 0;padding:16px;
                    background:rgba(99,179,237,0.05);border-radius:12px;
                    border:1px solid rgba(99,179,237,0.15);">
            <span style="font-family:'Space Mono',monospace;color:#718096;font-size:12px;">
                {selected} {part_type} — Total Portfolio
            </span><br>
            <span style="font-family:'Space Mono',monospace;font-size:32px;
                         font-weight:700;color:#63b3ed;">${total_val:,.2f}</span>
            <span style="font-family:'Space Mono',monospace;font-size:18px;
                         color:{'#68d391' if total_ret >= 0 else '#fc8181'};
                         margin-left:12px;">{total_ret:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Individual stock chart
        fig4 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_df.columns:
                fig4.add_trace(go.Scatter(
                    x=stock_df.index,
                    y=stock_df[ticker],
                    name=ticker,
                    line=dict(width=2.5, color=stock_colors_ind[i]),
                    hovertemplate=f"<b>{ticker}</b><br>$%{{y:,.2f}}<extra></extra>"
                ))
        
        fig4.add_hline(y=INITIAL, line_dash="dot", line_color="rgba(255,255,255,0.2)",
                       annotation_text="Initial $1,000")
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a0aec0", family="Space Mono"),
            legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=",.0f"),
            hovermode="x unified",
            height=420,
            margin=dict(l=0, r=0, t=20, b=0),
            title=dict(
                text=f"{selected}'s Portfolio — Individual Stock Performance",
                font=dict(size=14, color="#718096"),
                x=0,
            )
        )
        st.plotly_chart(fig4, use_container_width=True)
        
        # Relative % return chart
        stock_pct = ((stock_df - INITIAL) / INITIAL * 100)
        fig5 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_pct.columns:
                fig5.add_trace(go.Scatter(
                    x=stock_pct.index,
                    y=stock_pct[ticker],
                    name=ticker,
                    line=dict(width=2, color=stock_colors_ind[i], dash="dot"),
                    hovertemplate=f"<b>{ticker}</b><br>%{{y:+.2f}}%<extra></extra>"
                ))
        
        fig5.add_hline(y=0, line_color="rgba(255,255,255,0.2)")
        fig5.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#a0aec0", family="Space Mono"),
            legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
            xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%"),
            hovermode="x unified",
            height=350,
            margin=dict(l=0, r=0, t=20, b=0),
            title=dict(
                text="Percentage Return by Stock",
                font=dict(size=14, color="#718096"),
                x=0,
            )
        )
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="text-align:center;color:#2d3748;font-family:'Space Mono',monospace;font-size:11px;letter-spacing:2px;">
    STOCK MARKET CHAMPIONSHIP 2026 · DATA VIA YAHOO FINANCE · REFRESHES HOURLY
</p>
""", unsafe_allow_html=True)