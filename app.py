import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
    "Claude":   ["CEG",  "APP",  "AXON", "CRM"],
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

section[data-testid="stSidebar"] {
    background: rgba(10,14,26,0.95);
    border-right: 1px solid rgba(255,255,255,0.06);
}

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
# BASELINE PRICES
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_baseline() -> dict:
    import json
    from pathlib import Path
    baseline_path = Path(__file__).parent / "baseline_prices.json"
    if not baseline_path.exists():
        return {}
    with open(baseline_path) as f:
        data = json.load(f)
    return {k: v for k, v in data.get("prices", {}).items() if v is not None}

# ─────────────────────────────────────────────
# LIVE PRICE FETCHING
# ─────────────────────────────────────────────
@st.cache_data(ttl=900, show_spinner=False)
def fetch_daily_history(tickers: tuple, start: str, end: str, _cache_bucket: int = 0):
    today = date.today().isoformat()
    actual_end = min(end, today)
    if start > today:
        start = today

    frames = {}
    missing = []

    try:
        raw = yf.download(
            tickers, start=start, end=actual_end, auto_adjust=True,
            progress=False, group_by="ticker", threads=True, prepost=False,
        )
    except Exception:
        raw = pd.DataFrame()

    for ticker in tickers:
        try:
            if raw.empty: raise ValueError("empty")
            if len(tickers) == 1:
                series = raw["Close"]
            else:
                if ticker not in raw.columns.get_level_values(0): raise ValueError("missing")
                series = raw[ticker]["Close"]
            if isinstance(series, pd.DataFrame): series = series.iloc[:, 0]
            series = series.dropna()
            if len(series) < 1: raise ValueError("too short")
            series.name = ticker
            frames[ticker] = series
        except Exception:
            try:
                df2 = yf.download(ticker, start=start, end=actual_end, auto_adjust=True, progress=False, prepost=False)
                if df2.empty: raise ValueError("empty fallback")
                c = df2["Close"]
                if isinstance(c, pd.DataFrame): c = c.iloc[:, 0]
                c = c.dropna()
                c.name = ticker
                frames[ticker] = c
            except Exception:
                missing.append(ticker)

    if not frames:
        return pd.DataFrame(), list(tickers)

    prices = pd.DataFrame(frames)
    prices.index = pd.to_datetime(prices.index)
    prices.sort_index(inplace=True)
    return prices, missing

# Added cache here so Deep Dive loads instantly
@st.cache_data(ttl=300, show_spinner=False)
def _do_fetch_latest_prices(tickers: tuple) -> tuple[dict, dict]:
    import pytz
    et_tz = pytz.timezone("US/Eastern")
    current_prices: dict = {}
    price_times:    dict = {}

    def _unix_to_label(ts_unix) -> str:
        if not ts_unix: return ""
        dt_utc = datetime.fromtimestamp(float(ts_unix), tz=pytz.utc)
        return dt_utc.astimezone(et_tz).strftime("%b %d, %Y %I:%M %p ET")

    def _parse_history_latest(df) -> tuple:
        if df is None or df.empty: raise ValueError("empty")
        close = df["Close"]
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        close = close.dropna()
        if close.empty: raise ValueError("all NaN")
        price = float(close.iloc[-1])
        ts = close.index[-1]
        ts = pd.Timestamp(ts)
        if ts.tzinfo is None: ts = ts.tz_localize("UTC")
        unix_ts = ts.timestamp()
        label = ts.astimezone(et_tz).strftime("%b %d, %Y %I:%M %p ET")
        return price, unix_ts, label

    for ticker in tickers:
        price, label = None, "unavailable"
        t = yf.Ticker(ticker)
        try:
            info = t.info
            candidates = []
            for p_key, t_key, suffix in [("postMarketPrice", "postMarketTime", "after-hours"),
                                         ("preMarketPrice", "preMarketTime", "pre-market"),
                                         ("currentPrice", "regularMarketTime", "")]:
                p, tm = info.get(p_key), info.get(t_key)
                if not p: p = info.get("regularMarketPrice") if p_key == "currentPrice" else None
                if p and float(p) > 0 and tm: candidates.append((float(p), float(tm), suffix))
            
            if candidates:
                best = max(candidates, key=lambda x: x[1])
                price = best[0]
                suffix = f" ({best[2]})" if best[2] else ""
                label = _unix_to_label(best[1]) + suffix
        except Exception: pass

        if price is None:
            try:
                fi = t.fast_info
                reg_p, reg_t = getattr(fi, "last_price", None), getattr(fi, "regular_market_time", None)
                if reg_p and float(reg_p) > 0 and reg_t:
                    price, label = float(reg_p), _unix_to_label(float(reg_t))
            except Exception: pass

        if price is None:
            try:
                h = t.history(period="5d", interval="1m", prepost=True, auto_adjust=True)
                price, _, label = _parse_history_latest(h)
            except Exception: pass

        if price is None:
            try:
                h = t.history(period="10d", interval="1d", prepost=False, auto_adjust=True)
                price, _, label = _parse_history_latest(h)
                label = label.replace(" ET", " ET (close)")
            except Exception: pass

        current_prices[ticker] = price
        price_times[ticker]    = label if price is not None else "unavailable"

    return current_prices, price_times

# ─────────────────────────────────────────────
# PORTFOLIO COMPUTATION
# ─────────────────────────────────────────────
def compute_portfolio_history(daily_prices: pd.DataFrame, participants: dict, baseline: dict, missing_tickers: list) -> pd.DataFrame:
    portfolios = {}
    for name, tickers in participants.items():
        total = pd.Series(0.0, index=daily_prices.index)
        for ticker in tickers:
            base = baseline.get(ticker)
            if base and base > 0 and ticker in daily_prices.columns and ticker not in missing_tickers:
                series = daily_prices[ticker].ffill()
                total += (series / base) * INITIAL
            else:
                total += INITIAL
        portfolios[name] = total
    return pd.DataFrame(portfolios)

def compute_current_portfolio(current_prices: dict, participants: dict, baseline: dict) -> pd.Series:
    values = {}
    for name, tickers in participants.items():
        total = 0.0
        for ticker in tickers:
            base = baseline.get(ticker)
            current = current_prices.get(ticker)
            if base and base > 0 and current and current > 0: total += (current / base) * INITIAL
            else: total += INITIAL
        values[name] = total
    return pd.Series(values)

def compute_benchmark_history(daily_prices: pd.DataFrame, baseline: dict, missing_tickers: list) -> pd.DataFrame:
    benchmarks = {}
    for label, ticker in BENCHMARKS.items():
        base = baseline.get(ticker)
        if base and base > 0 and ticker in daily_prices.columns and ticker not in missing_tickers:
            series = daily_prices[ticker].ffill()
            benchmarks[label] = (series / base) * TOTAL_INV
    return pd.DataFrame(benchmarks)

def compute_current_benchmarks(current_prices: dict, baseline: dict) -> pd.Series:
    vals = {}
    for label, ticker in BENCHMARKS.items():
        base = baseline.get(ticker)
        current = current_prices.get(ticker)
        if base and base > 0 and current and current > 0: vals[label] = (current / base) * TOTAL_INV
        else: vals[label] = TOTAL_INV
    return pd.Series(vals)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 Championship 2026")
    st.markdown('<p style="color:#4a5568;font-size:12px;font-family:\'Space Mono\',monospace;">MAR 01 – DEC 31, 2026</p>', unsafe_allow_html=True)
    st.divider()

    filter_opt = st.radio("**Participant Filter**", ["All Participants", "Human Only", "AI Only"], index=0)
    st.divider()
    st.markdown('<p style="color:#4a5568;font-size:11px;">Initial investment: $1,000 per stock<br>Total per portfolio: $4,000<br><br>Baseline: Feb 27, 2026 close<br>Live prices include after-hours</p>', unsafe_allow_html=True)

if filter_opt == "Human Only": active_participants = HUMAN_PARTICIPANTS
elif filter_opt == "AI Only": active_participants = AI_PARTICIPANTS
else: active_participants = ALL_PARTICIPANTS

all_tickers = sorted(set(t for p in ALL_PARTICIPANTS.values() for t in p) | set(BENCHMARKS.values()))
_tickers_tuple = tuple(all_tickers)

baseline = load_baseline()
if not baseline:
    st.error("**baseline_prices.json not found or empty.**")
    st.stop()

missing_from_baseline = [t for t in all_tickers if t not in baseline]
if missing_from_baseline: st.sidebar.warning(f"⚠️ No baseline price for: {', '.join(missing_from_baseline)}")

_bucket_15min = int(datetime.now().timestamp() // 900)

with st.spinner("📡 Fetching market data..."):
    daily_prices, missing_tickers = fetch_daily_history(_tickers_tuple, ANCHOR_DATE, END_DATE, _cache_bucket=_bucket_15min)
    current_prices, price_times = _do_fetch_latest_prices(_tickers_tuple)

if daily_prices.empty:
    st.error("Could not fetch daily price history. Please check your internet connection.")
    st.stop()

def _parse_label_dt(label: str):
    try:
        clean = label.split(" ET")[0].strip()
        return datetime.strptime(clean, "%b %d, %Y %I:%M %p")
    except Exception: return datetime.min

_valid_times = {tk: lbl for tk, lbl in price_times.items() if lbl not in ("unavailable", "", None)}
last_updated = max(_valid_times.values(), key=_parse_label_dt) if _valid_times else "unavailable"

portfolio_df  = compute_portfolio_history(daily_prices, active_participants, baseline, missing_tickers)
benchmark_df  = compute_benchmark_history(daily_prices, baseline, missing_tickers)
current_portfolio  = compute_current_portfolio(current_prices, active_participants, baseline)
current_benchmarks = compute_current_benchmarks(current_prices, baseline)

# Force live values into the historical dataframe to guarantee latest movement on charts
live_timestamp = pd.Timestamp(datetime.now().replace(microsecond=0))
chart_df = portfolio_df.copy()
chart_df.loc[live_timestamp] = current_portfolio

returns_pct = ((current_portfolio - TOTAL_INV) / TOTAL_INV * 100).round(2)
leaderboard = pd.DataFrame({
    "Participant":   current_portfolio.index,
    "Portfolio ($)": current_portfolio.values,
    "Return (%)":    returns_pct.values,
}).sort_values("Portfolio ($)", ascending=False).reset_index(drop=True)
leaderboard.index += 1
leaderboard["Rank"] = leaderboard.index
leaderboard["Type"] = leaderboard["Participant"].apply(lambda x: "🤖 AI" if x in AI_PARTICIPANTS else "👤 Human")

N = len(active_participants)
colors = px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.Alphabet
colors = colors[:N]

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 32px 0 8px 0;">
    <h1 style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;
               background:linear-gradient(135deg,#e2e8f0,#63b3ed);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin:0;line-height:1.1;">
        Stock Market<br>Championship 2026
    </h1>
    <p style="color:#4a5568;font-family:'Space Mono',monospace;font-size:12px;
              letter-spacing:3px;margin-top:8px;">
        LIVE COMPETITION TRACKER · BASELINE: FEB 27, 2026 CLOSE
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f"""<div style="display:inline-flex;align-items:center;gap:8px;
                    background:rgba(99,179,237,0.07);border:1px solid rgba(99,179,237,0.15);
                    border-radius:8px;padding:6px 14px;margin-bottom:4px;">
        <span style="font-size:14px;">🕐</span>
        <span style="font-family:'Space Mono',monospace;font-size:11px;color:#63b3ed;letter-spacing:1px;">
            LATEST AVAILABLE PRICE: <strong>{last_updated}</strong>
        </span>
    </div>""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Overall Leaderboard",
    "📈 Daily Leaderboard",
    "📅 Monthly Leaderboard",
    "📊 Benchmarks",
    "📆 Monthly Breakdown",
    "🔍 Deep Dive",
])

# ══════════════════════════════════════════════
# TAB 1: OVERALL LEADERBOARD
# ══════════════════════════════════════════════
with tab1:
    top3 = leaderboard.head(3)
    medals = ["gold", "silver", "bronze"]
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
            
    # Overall Heatmap (Request 1)
    st.markdown('<div class="section-header">Overall Performance</div>', unsafe_allow_html=True)
    sorted_overall = leaderboard.set_index("Participant")["Return (%)"].sort_values(ascending=False)
    hm_vals_ov = sorted_overall.values.reshape(1, -1)
    hm_names_ov = sorted_overall.index.tolist()
    hm_text_ov = [[f"{v:+.2f}%" for v in sorted_overall.values]]

    fig_hm_ov = go.Figure(data=go.Heatmap(
        z=hm_vals_ov, x=hm_names_ov, y=["Overall Return"],
        colorscale=[[0.0, "#7b2d2d"], [0.35, "#2d3748"], [0.5, "#1e2a3a"], [0.65, "#2d3748"], [1.0, "#1a4731"]],
        zmid=0, text=hm_text_ov, texttemplate="%{text}",
        textfont=dict(size=13, family="Space Mono", color="rgba(255,255,255,0.9)"),
        hovertemplate="<b>%{x}</b><br>Overall: %{z:+.3f}%<extra></extra>",
        showscale=True,
        colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_ov.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0aec0", family="Space Mono", size=12),
        height=160, margin=dict(l=0, r=0, t=12, b=0),
        xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_hm_ov, use_container_width=True)

    st.markdown('<div class="section-header">Full Leaderboard</div>', unsafe_allow_html=True)
    rows_html = ""
    for _, row in leaderboard[["Rank", "Participant", "Portfolio ($)", "Return (%)", "Type"]].iterrows():
        port_fmt = f"${row['Portfolio ($)']:,.2f}"
        ret_fmt  = f"{row['Return (%)']:+.2f}%"
        rc       = "#68d391" if row["Return (%)"] >= 0 else "#fc8181"
        rows_html += f"""<tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="width:36px;text-align:center;padding:10px 4px;color:#4a5568;">{int(row['Rank'])}</td>
            <td style="padding:10px 12px;font-weight:600;color:#e2e8f0;">{row['Participant']}</td>
            <td style="padding:10px 12px;font-family:'Space Mono',monospace;color:#63b3ed;">{port_fmt}</td>
            <td style="padding:10px 12px;font-family:'Space Mono',monospace;color:{rc};font-weight:700;">{ret_fmt}</td>
            <td style="padding:10px 12px;color:#718096;font-size:12px;">{row['Type']}</td>
        </tr>"""

    st.markdown(f"""
    <div style="border:1px solid rgba(255,255,255,0.07);border-radius:12px;overflow:hidden;margin-bottom:8px;">
    <table style="width:100%;border-collapse:collapse;font-family:'Syne',sans-serif;font-size:14px;">
        <thead>
            <tr style="background:rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.08);">
                <th style="width:36px;text-align:center;padding:10px 4px;color:#4a5568;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;font-weight:400;">#</th>
                <th style="text-align:left;padding:10px 12px;color:#4a5568;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;font-weight:400;">PARTICIPANT</th>
                <th style="text-align:left;padding:10px 12px;color:#4a5568;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;font-weight:400;">PORTFOLIO VALUE</th>
                <th style="text-align:left;padding:10px 12px;color:#4a5568;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;font-weight:400;">TOTAL RETURN</th>
                <th style="text-align:left;padding:10px 12px;color:#4a5568;font-family:'Space Mono',monospace;font-size:10px;letter-spacing:2px;font-weight:400;">TYPE</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Portfolio Value Over Time (Request 1 logic fix: use chart_df which forces recent data inclusion)
    st.markdown('<div class="section-header">Portfolio Value Over Time</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for i, col_name in enumerate(chart_df.columns):
        fig.add_trace(go.Scatter(
            x=chart_df.index, y=chart_df[col_name], name=col_name,
            line=dict(width=2, color=colors[i % len(colors)]),
            hovertemplate=f"<b>{col_name}</b><br>Date: %{{x|%b %d}}<br>Value: $%{{y:,.2f}}<extra></extra>"
        ))
    fig.add_hline(y=TOTAL_INV, line_dash="dot", line_color="rgba(255,255,255,0.2)", annotation_text="Initial $4,000")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0aec0", family="Space Mono"), legend=dict(bgcolor="rgba(0,0,0,0.3)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"), yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$"),
        hovermode="x unified", height=450, margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Cumulative Return Over Time Plot (Moved here, driven by chart_df)
    st.markdown('<div class="section-header">Total Return % Over Time</div>', unsafe_allow_html=True)
    ret_df = ((chart_df - TOTAL_INV) / TOTAL_INV * 100).round(3)
    fig_ret = go.Figure()
    for i, col_name in enumerate(ret_df.columns):
        fig_ret.add_trace(go.Scatter(
            x=ret_df.index, y=ret_df[col_name], name=col_name,
            line=dict(width=2, color=colors[i % len(colors)]),
            hovertemplate=f"<b>{col_name}</b><br>%{{x|%b %d}}<br>Return: %{{y:+.2f}}%<extra></extra>",
        ))
    fig_ret.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.18)", annotation_text="Baseline")
    fig_ret.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0aec0", family="Space Mono"),
        legend=dict(bgcolor="rgba(0,0,0,0.3)", orientation="v", x=1.01, y=1),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", ticksuffix="%"),
        hovermode="x unified", height=450, margin=dict(l=0, r=120, t=20, b=0),
    )
    st.plotly_chart(fig_ret, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2: DAILY LEADERBOARD
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Today\'s Performance</div>', unsafe_allow_html=True)
    if len(portfolio_df) >= 2:
        yesterday_close = portfolio_df.iloc[-1]
        live_total_ret_pct = ((current_portfolio - TOTAL_INV) / TOTAL_INV * 100)
        yest_total_ret_pct = ((yesterday_close - TOTAL_INV) / TOTAL_INV * 100)
        todays_gain_pct    = (live_total_ret_pct - yest_total_ret_pct).round(3)
    else:
        todays_gain_pct = ((current_portfolio - TOTAL_INV) / TOTAL_INV * 100).round(3)

    todays_winner = todays_gain_pct.idxmax()
    todays_winner_val = todays_gain_pct.max()
    todays_winner_type = "🤖 AI" if todays_winner in AI_PARTICIPANTS else "👤 Human"

    w_col, spacer = st.columns([1, 2])
    with w_col:
        w_color = "#68d391" if todays_winner_val >= 0 else "#fc8181"
        st.markdown(f"""
        <div class="metric-card gold" style="text-align:center;">
            <div class="metric-rank">🏅 TODAY'S LEADER</div>
            <div class="metric-name">{todays_winner}</div>
            <div class="metric-return" style="color:{w_color};font-size:26px;">{todays_winner_val:+.2f}%</div>
            <div style="font-size:11px;color:#718096;margin-top:4px;">{todays_winner_type} · vs yesterday's close</div>
        </div>
        """, unsafe_allow_html=True)

    sorted_today = todays_gain_pct.sort_values(ascending=False)
    hm_vals = sorted_today.values.reshape(1, -1)
    fig_hm_daily = go.Figure(data=go.Heatmap(
        z=hm_vals, x=sorted_today.index.tolist(), y=["Today's Return"],
        colorscale=[[0.0, "#7b2d2d"], [0.35, "#2d3748"], [0.5, "#1e2a3a"], [0.65, "#2d3748"], [1.0, "#1a4731"]], zmid=0,
        text=[[f"{v:+.2f}%" for v in sorted_today.values]], texttemplate="%{text}",
        textfont=dict(size=13, family="Space Mono", color="rgba(255,255,255,0.9)"),
        hovertemplate="<b>%{x}</b><br>Today: %{z:+.3f}%<extra></extra>", showscale=True,
        colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_daily.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=160, margin=dict(l=0, r=0, t=12, b=0), xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False))
    st.plotly_chart(fig_hm_daily, use_container_width=True)

    st.markdown('<div class="section-header">Full Today\'s Ranking</div>', unsafe_allow_html=True)
    today_df = pd.DataFrame({
        "Rank": range(1, len(sorted_today) + 1),
        "Participant": sorted_today.index,
        "Today's Return": sorted_today.map("{:+.2f}%".format),
        "Live Portfolio": current_portfolio[sorted_today.index].map("${:,.2f}".format),
        "Type": [("🤖 AI" if p in AI_PARTICIPANTS else "👤 Human") for p in sorted_today.index],
    }).set_index("Rank")
    st.table(today_df)


# ══════════════════════════════════════════════
# TAB 3: MONTHLY LEADERBOARD (Request 3)
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Current Month Performance</div>', unsafe_allow_html=True)
    
    curr_mth_start = pd.Timestamp(date.today().replace(day=1))
    # Grab the closest row before current month started to act as the base
    hist_before_mth = portfolio_df[portfolio_df.index < curr_mth_start]
    
    if len(hist_before_mth) > 0:
        prev_month_close = hist_before_mth.iloc[-1]
    else:
        prev_month_close = pd.Series(TOTAL_INV, index=current_portfolio.index)

    live_total_ret_pct = ((current_portfolio - TOTAL_INV) / TOTAL_INV * 100)
    prev_mth_ret_pct = ((prev_month_close - TOTAL_INV) / TOTAL_INV * 100)
    mtd_gain_pct = (live_total_ret_pct - prev_mth_ret_pct).round(3)

    mtd_winner = mtd_gain_pct.idxmax()
    mtd_winner_val = mtd_gain_pct.max()
    mtd_winner_type = "🤖 AI" if mtd_winner in AI_PARTICIPANTS else "👤 Human"

    m_col, spacer = st.columns([1, 2])
    with m_col:
        m_color = "#68d391" if mtd_winner_val >= 0 else "#fc8181"
        st.markdown(f"""
        <div class="metric-card gold" style="text-align:center;">
            <div class="metric-rank">🏅 MONTH'S LEADER</div>
            <div class="metric-name">{mtd_winner}</div>
            <div class="metric-return" style="color:{m_color};font-size:26px;">{mtd_winner_val:+.2f}%</div>
            <div style="font-size:11px;color:#718096;margin-top:4px;">{mtd_winner_type} · Month-To-Date</div>
        </div>
        """, unsafe_allow_html=True)

    sorted_mtd = mtd_gain_pct.sort_values(ascending=False)
    hm_vals_mtd = sorted_mtd.values.reshape(1, -1)
    fig_hm_mtd = go.Figure(data=go.Heatmap(
        z=hm_vals_mtd, x=sorted_mtd.index.tolist(), y=["MTD Return"],
        colorscale=[[0.0, "#7b2d2d"], [0.35, "#2d3748"], [0.5, "#1e2a3a"], [0.65, "#2d3748"], [1.0, "#1a4731"]], zmid=0,
        text=[[f"{v:+.2f}%" for v in sorted_mtd.values]], texttemplate="%{text}",
        textfont=dict(size=13, family="Space Mono", color="rgba(255,255,255,0.9)"),
        hovertemplate="<b>%{x}</b><br>MTD: %{z:+.3f}%<extra></extra>", showscale=True,
        colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_mtd.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=160, margin=dict(l=0, r=0, t=12, b=0), xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False))
    st.plotly_chart(fig_hm_mtd, use_container_width=True)

    st.markdown('<div class="section-header">Full MTD Ranking</div>', unsafe_allow_html=True)
    mtd_df = pd.DataFrame({
        "Rank": range(1, len(sorted_mtd) + 1),
        "Participant": sorted_mtd.index,
        "MTD Return": sorted_mtd.map("{:+.2f}%".format),
        "Live Portfolio": current_portfolio[sorted_mtd.index].map("${:,.2f}".format),
        "Type": [("🤖 AI" if p in AI_PARTICIPANTS else "👤 Human") for p in sorted_mtd.index],
    }).set_index("Rank")
    st.table(mtd_df)


# ══════════════════════════════════════════════
# TAB 4: BENCHMARKS
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Portfolio vs Benchmarks (% Return)</div>', unsafe_allow_html=True)
    avg_portfolio = chart_df.mean(axis=1) # using the chart_df that includes current live prices
    
    # Transform to percentage for better visibility (Request 4)
    avg_portfolio_pct = ((avg_portfolio - TOTAL_INV) / TOTAL_INV * 100).round(2)
    benchmark_df_live = compute_benchmark_history(daily_prices, baseline, missing_tickers)
    benchmark_df_live.loc[live_timestamp] = current_benchmarks
    benchmark_pct = ((benchmark_df_live - TOTAL_INV) / TOTAL_INV * 100).round(2)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=avg_portfolio_pct.index, y=avg_portfolio_pct, name=f"Avg Portfolio ({filter_opt})",
        line=dict(width=3, color="#63b3ed"), fill="tozeroy", fillcolor="rgba(99,179,237,0.05)",
        hovertemplate="<b>Avg Portfolio</b><br>%{y:+.2f}%<extra></extra>"
    ))
    
    bm_colors = ["#F6D860","#68d391","#fc8181","#b794f4"]
    for i, col_name in enumerate(benchmark_pct.columns):
        fig2.add_trace(go.Scatter(
            x=benchmark_pct.index, y=benchmark_pct[col_name], name=col_name,
            line=dict(width=2, color=bm_colors[i % len(bm_colors)], dash="dash"),
            hovertemplate=f"<b>{col_name}</b><br>%{{y:+.2f}}%<extra></extra>"
        ))
    
    fig2.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0aec0", family="Space Mono"), legend=dict(bgcolor="rgba(0,0,0,0.3)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)"), yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%"),
        hovermode="x unified", height=500, margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    if len(current_benchmarks) > 0:
        st.markdown('<div class="section-header">Benchmark Performance (Live)</div>', unsafe_allow_html=True)
        bm_return = ((current_benchmarks - TOTAL_INV) / TOTAL_INV * 100).round(2)
        avg_port_live = avg_portfolio.iloc[-1]
        avg_port_ret  = ((avg_port_live - TOTAL_INV) / TOTAL_INV * 100).round(2)
        
        bm_table = pd.DataFrame({
            "Entity": list(current_benchmarks.index) + [f"Average Portfolio ({filter_opt})"],
            "Current Value": [f"${v:,.2f}" for v in current_benchmarks.values] + [f"${avg_port_live:,.2f}"],
            "Return": [f"{v:+.2f}%" for v in bm_return.values] + [f"{avg_port_ret:+.2f}%"],
        })
        st.dataframe(bm_table, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# TAB 5: MONTHLY BREAKDOWN
# ══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Monthly Performance</div>', unsafe_allow_html=True)
    
    # Monthly breakdown logic fixed (Request 5)
    full_history = pd.concat([portfolio_df, pd.DataFrame([current_portfolio.values], columns=current_portfolio.index, index=[pd.Timestamp(datetime.now())])])
    monthly = full_history.resample("ME").last()
    
    # We drop any index before March 1 since the competition didn't exist officially then 
    # (Feb 27 is the baseline acting as Day 0, thus diffs starting March represent actual monthly gains)
    monthly_gain = monthly.diff().dropna() 
    monthly_pct  = (monthly_gain / monthly.shift(1).dropna() * 100).round(2)
    
    # Only keep March onward
    monthly_pct = monthly_pct[monthly_pct.index >= pd.Timestamp("2026-03-01")]
    monthly_gain = monthly_gain[monthly_gain.index >= pd.Timestamp("2026-03-01")]
    
    if not monthly_gain.empty:
        months_fmt = monthly_pct.index.strftime("%b %Y")
        fig3 = go.Figure(data=go.Heatmap(
            z=monthly_pct.T.values, x=months_fmt, y=monthly_pct.columns.tolist(),
            colorscale=[[0.0, "#7b2d2d"], [0.4, "#2d3748"], [0.5, "#2d3748"], [0.6, "#2d3748"], [1.0, "#276749"]], zmid=0,
            text=monthly_pct.T.values, texttemplate="%{text:.1f}%", textfont=dict(size=11, family="Space Mono"),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Return: %{z:.2f}%<extra></extra>",
            colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)")
        ))
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0aec0", family="Space Mono", size=12),
            height=max(400, 30 * len(portfolio_df.columns) + 80), margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(side="top"),
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown('<div class="section-header">Monthly Winners</div>', unsafe_allow_html=True)
        completed_months = monthly_gain.index[monthly_gain.index <= pd.Timestamp(date.today() + pd.offsets.MonthEnd(0))]
        if len(completed_months) > 0:
            winner_data = []
            for m in completed_months:
                row   = monthly_gain.loc[m]
                winner = row.idxmax()
                gain   = row.max()
                ret    = monthly_pct.loc[m, winner]
                winner_data.append({
                    "Month": m.strftime("%B %Y"), "Winner": winner, "Dollar Gain": f"+${gain:,.2f}",
                    "Monthly Return": f"+{ret:.2f}%", "Type": "🤖 AI" if winner in AI_PARTICIPANTS else "👤 Human"
                })
            wdf = pd.DataFrame(winner_data)
            st.dataframe(wdf, use_container_width=True, hide_index=True)
    else:
        st.info("Not enough data for monthly breakdown yet.")


# ══════════════════════════════════════════════
# TAB 6: INDIVIDUAL DEEP DIVE
# ══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Individual Portfolio Analysis</div>', unsafe_allow_html=True)
    participant_names = list(active_participants.keys())
    selected = st.selectbox("Select Participant", participant_names, key="deep_dive")

    if selected:
        tickers   = active_participants[selected]
        part_type = "🤖 AI" if selected in AI_PARTICIPANTS else "👤 Human"

        stock_hist = {}
        for ticker in tickers:
            base = baseline.get(ticker)
            if base and base > 0 and ticker in daily_prices.columns:
                series = daily_prices[ticker].ffill()
                stock_hist[ticker] = (series / base) * INITIAL
            else:
                stock_hist[ticker] = pd.Series(INITIAL, index=daily_prices.index)
        stock_df = pd.DataFrame(stock_hist)
        # Push live price into stock_df for deep dive charting
        live_hist_row = {}
        for tk in tickers:
            cp, bp = current_prices.get(tk), baseline.get(tk)
            live_hist_row[tk] = (cp / bp) * INITIAL if (cp and bp) else INITIAL
        stock_df.loc[live_timestamp] = live_hist_row

        stock_colors_ind = ["#63b3ed", "#68d391", "#F6D860", "#fc8181"]
        col1, col2, col3, col4 = st.columns(4)

        live_stock_vals = live_hist_row
        for i, (col, ticker) in enumerate(zip([col1, col2, col3, col4], tickers)):
            val      = live_stock_vals[ticker]
            ret      = (val - INITIAL) / INITIAL * 100
            ts       = price_times.get(ticker, "—")
            base_px  = baseline.get(ticker)
            curr_px  = current_prices.get(ticker)
            with col:
                color = "#68d391" if ret >= 0 else "#fc8181"
                base_str = f"${base_px:,.2f}" if base_px else "N/A"
                curr_str = f"${curr_px:,.4f}" if curr_px else "N/A"
                st.markdown(f"""
                <div class="metric-card" style="border-top:3px solid {stock_colors_ind[i]};">
                    <div class="metric-rank">{ticker}</div>
                    <div class="metric-value" style="font-size:20px;">${val:,.2f}</div>
                    <div class="metric-return" style="color:{color};">{ret:+.2f}%</div>
                    <div style="margin-top:10px;font-family:'Space Mono',monospace;font-size:11px;color:#cbd5e0;line-height:2.0;">
                        <span style="color:#718096;">BASE</span>&nbsp;&nbsp;{base_str}<br>
                        <span style="color:#718096;">NOW&nbsp;</span>&nbsp;&nbsp;{curr_str}<br>
                        <span style="color:#718096;font-size:10px;">{ts}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        total_val = sum(live_stock_vals.values())
        total_ret = (total_val - TOTAL_INV) / TOTAL_INV * 100

        st.markdown(f"""
        <div style="text-align:center;margin:16px 0;padding:16px;
                    background:rgba(99,179,237,0.05);border-radius:12px;border:1px solid rgba(99,179,237,0.15);">
            <span style="font-family:'Space Mono',monospace;color:#718096;font-size:12px;">
                {selected} {part_type} — Total Portfolio (live)
            </span><br>
            <span style="font-family:'Space Mono',monospace;font-size:32px;font-weight:700;color:#63b3ed;">${total_val:,.2f}</span>
            <span style="font-family:'Space Mono',monospace;font-size:18px;color:{'#68d391' if total_ret >= 0 else '#fc8181'};margin-left:12px;">{total_ret:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
        
        fig4 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_df.columns:
                fig4.add_trace(go.Scatter(
                    x=stock_df.index, y=stock_df[ticker], name=ticker,
                    line=dict(width=2.5, color=stock_colors_ind[i]), hovertemplate=f"<b>{ticker}</b><br>$%{{y:,.2f}}<extra></extra>"
                ))
        
        fig4.add_hline(y=INITIAL, line_dash="dot", line_color="rgba(255,255,255,0.2)", annotation_text="Initial $1,000")
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0aec0", family="Space Mono"),
            legend=dict(bgcolor="rgba(0,0,0,0.3)"), xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickprefix="$", tickformat=",.0f"), hovermode="x unified",
            height=420, margin=dict(l=0, r=0, t=20, b=0), title=dict(text=f"{selected}'s Portfolio — Individual Stock Performance", font=dict(size=14, color="#718096"), x=0)
        )
        st.plotly_chart(fig4, use_container_width=True)
        
        stock_pct = ((stock_df - INITIAL) / INITIAL * 100)
        fig5 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_pct.columns:
                fig5.add_trace(go.Scatter(
                    x=stock_pct.index, y=stock_pct[ticker], name=ticker,
                    line=dict(width=2, color=stock_colors_ind[i], dash="dot"), hovertemplate=f"<b>{ticker}</b><br>%{{y:+.2f}}%<extra></extra>"
                ))
        
        fig5.add_hline(y=0, line_color="rgba(255,255,255,0.2)")
        fig5.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#a0aec0", family="Space Mono"),
            legend=dict(bgcolor="rgba(0,0,0,0.3)"), xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.04)", ticksuffix="%"), hovermode="x unified",
            height=350, margin=dict(l=0, r=0, t=20, b=0), title=dict(text="Percentage Return by Stock", font=dict(size=14, color="#718096"), x=0)
        )
        st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<p style="text-align:center;color:#2d3748;font-family:'Space Mono',monospace;font-size:11px;letter-spacing:2px;">
    STOCK MARKET CHAMPIONSHIP 2026 · DATA VIA YAHOO FINANCE<br>
    BASELINE: FEB 27, 2026 4:00 PM ET CLOSE · LIVE PRICES REFRESH EVERY 5 MIN · CHARTS REFRESH EVERY 15 MIN
</p>
""", unsafe_allow_html=True)