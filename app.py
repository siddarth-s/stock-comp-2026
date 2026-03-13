import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# Deep Dive Selection State Initialization
_jump_to_deep_dive = False
if "participant" in st.query_params:
    st.session_state["deep_dive_selection"] = st.query_params["participant"]
    del st.query_params["participant"]
    _jump_to_deep_dive = True

# Theme Initialization
if "theme_setting" not in st.session_state:
    st.session_state.theme_setting = "Auto"

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
# THEME ENGINE & CUSTOM CSS
# ─────────────────────────────────────────────
css_vars_light = """
    --app-bg: linear-gradient(135deg, #f0f2f6 0%, #e2e8f0 100%);
    --card-bg: rgba(255, 255, 255, 0.85);
    --dropdown-bg: #ffffff;
    --card-border: rgba(0, 0, 0, 0.1);
    --text-main: #1a202c;
    --text-muted: #4a5568;
    --text-value: #2b6cb0;
    --pos: #2f855a;
    --neg: #c53030;
    --table-border: rgba(0, 0, 0, 0.08);
    --table-header: rgba(0, 0, 0, 0.04);
    --grid-line: rgba(0, 0, 0, 0.06);
"""
css_vars_dark = """
    --app-bg: linear-gradient(135deg, #0a0e1a 0%, #0d1526 50%, #0a1020 100%);
    --card-bg: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
    --dropdown-bg: #1a202c;
    --card-border: rgba(255,255,255,0.08);
    --text-main: #e2e8f0;
    --text-muted: #718096;
    --text-value: #63b3ed;
    --pos: #68d391;
    --neg: #fc8181;
    --table-border: rgba(255,255,255,0.04);
    --table-header: rgba(255,255,255,0.02);
    --grid-line: rgba(255,255,255,0.04);
"""

if st.session_state.theme_setting == "Light":
    css_injection = f":root {{ {css_vars_light} }}"
    plotly_font, plotly_grid = "#1a202c", "rgba(0,0,0,0.06)"
    heat_colors = [[0.0, "#fc8181"], [0.35, "#edf2f7"], [0.5, "#ffffff"], [0.65, "#edf2f7"], [1.0, "#68d391"]]
    heat_font = "#1a202c"
elif st.session_state.theme_setting == "Dark":
    css_injection = f":root {{ {css_vars_dark} }}"
    plotly_font, plotly_grid = "#e2e8f0", "rgba(255,255,255,0.04)"
    heat_colors = [[0.0, "#7b2d2d"], [0.35, "#2d3748"], [0.5, "#1e2a3a"], [0.65, "#2d3748"], [1.0, "#1a4731"]]
    heat_font = "rgba(255,255,255,0.9)"
else: # Auto
    css_injection = f":root {{ {css_vars_light} }} @media (prefers-color-scheme: dark) {{ :root {{ {css_vars_dark} }} }}"
    plotly_font, plotly_grid = None, None 
    heat_colors = [[0.0, "#e53e3e"], [0.35, "#edf2f7"], [0.5, "#ffffff"], [0.65, "#edf2f7"], [1.0, "#38a169"]]
    heat_font = None 

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

{css_injection}

html, body, [class*="css"] {{ font-family: 'Syne', sans-serif; color: var(--text-main); }}
.stApp {{ background: var(--app-bg) !important; }}

/* ── Deep UI CSS Overrides ── */
p, span, div, label, li {{ color: var(--text-main) !important; }}

/* Metric Cards */
.metric-card {{
    background: var(--card-bg); border: 1px solid var(--card-border);
    border-radius: 16px; padding: 24px; text-align: center;
    backdrop-filter: blur(10px); transition: transform 0.2s, border-color 0.2s;
}}
.metric-card:hover {{ transform: translateY(-2px); border-color: var(--text-value); }}
.metric-rank {{ font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 3px; color: var(--text-muted) !important; text-transform: uppercase; margin-bottom: 8px; }}
.metric-name {{ font-size: 22px; font-weight: 800; color: var(--text-main) !important; margin-bottom: 4px; }}
.metric-name a {{ color: inherit; text-decoration: none; transition: color 0.2s; }}
.metric-name a:hover {{ color: var(--text-value) !important; }}
.metric-value {{ font-family: 'Space Mono', monospace; font-size: 28px; font-weight: 700; color: var(--text-value) !important; margin-bottom: 4px; }}
.metric-return {{ font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; }}

/* Metric Colors */
.positive {{ color: var(--pos) !important; }}
.negative {{ color: var(--neg) !important; }}
.gold   {{ border-top: 3px solid #F6D860; }}
.silver {{ border-top: 3px solid #C0C0C0; }}
.bronze {{ border-top: 3px solid #CD7F32; }}

/* Section Headers */
.section-header {{
    font-family: 'Space Mono', monospace; font-size: 11px; letter-spacing: 4px; text-transform: uppercase;
    color: var(--text-muted) !important; margin: 32px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid var(--card-border);
}}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: var(--card-bg) !important; border-right: 1px solid var(--card-border); }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: var(--table-header) !important; border-radius: 12px; padding: 4px; }}
.stTabs [data-baseweb="tab"] {{ border-radius: 8px; background: transparent !important; }}
.stTabs [data-baseweb="tab"] p {{ font-family: 'Space Mono', monospace; font-size: 12px; letter-spacing: 1px; color: var(--text-main) !important; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ background: var(--card-bg) !important; border: 1px solid var(--card-border); }}

/* Radio Buttons (Theme Toggle) */
div[data-testid="stRadio"] label p {{ color: var(--text-main) !important; font-weight: bold; }}

/* Selectbox Dropdown (Deep Dive) */
div[data-baseweb="select"] > div {{ background-color: var(--card-bg) !important; border-color: var(--card-border) !important; }}
div[data-baseweb="select"] span {{ color: var(--text-main) !important; }}

/* Streamlit Popover Portal Fixes */
div[data-baseweb="popover"] {{ background-color: var(--dropdown-bg) !important; }}
div[data-baseweb="popover"] ul {{ background-color: var(--dropdown-bg) !important; }}
div[data-baseweb="popover"] li {{ background-color: var(--dropdown-bg) !important; color: var(--text-main) !important; }}
div[data-baseweb="popover"] li:hover {{ background-color: var(--table-header) !important; }}

/* Responsive Container Logic */
@media (max-width: 768px) {{
    div[data-testid="stElementContainer"]:has(.hide-on-mobile),
    div[data-testid="stElementContainer"]:has(.hide-on-mobile) + div[data-testid="stElementContainer"] {{ display: none !important; }}
}}
@media (min-width: 769px) {{
    div[data-testid="stElementContainer"]:has(.hide-on-desktop),
    div[data-testid="stElementContainer"]:has(.hide-on-desktop) + div[data-testid="stElementContainer"] {{ display: none !important; }}
}}
</style>
""", unsafe_allow_html=True)

def apply_plotly_theme(fig, prefix="", suffix=""):
    # Removed the hardcoded l, r, b margins to allow Plotly to auto-expand for labels
    kwargs = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", hovermode="x unified", margin=dict(t=30))
    if plotly_font:
        kwargs["font"] = dict(color=plotly_font, family="Space Mono")
        kwargs["legend"] = dict(font=dict(color=plotly_font))
    else: 
        kwargs["font"] = dict(family="Space Mono")
    if plotly_grid:
        kwargs["xaxis"] = dict(gridcolor=plotly_grid)
        kwargs["yaxis"] = dict(gridcolor=plotly_grid, tickprefix=prefix, ticksuffix=suffix)
    else: 
        kwargs["yaxis"] = dict(tickprefix=prefix, ticksuffix=suffix)
    fig.update_layout(**kwargs)
    return fig

def render_responsive_plot(fig_desktop, fig_mobile):
    plotly_theme = None if st.session_state.theme_setting != "Auto" else "streamlit"
    st.markdown('<div class="hide-on-mobile" style="display:none;"></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_desktop, use_container_width=True, theme=plotly_theme)
    st.markdown('<div class="hide-on-desktop" style="display:none;"></div>', unsafe_allow_html=True)
    st.plotly_chart(fig_mobile, use_container_width=True, theme=plotly_theme)

def create_mobile_heatmap(sorted_series, title):
    hm_vals = sorted_series.values.reshape(-1, 1)
    hm_text = [[f"{v:+.1f}%"] for v in sorted_series.values]
    fig = go.Figure(data=go.Heatmap(
        z=hm_vals, x=[title], y=sorted_series.index.tolist(),
        colorscale=heat_colors, zmid=0, text=hm_text, texttemplate="%{text}",
        textfont=dict(size=12, family="Space Mono", color=heat_font),
        hovertemplate="<b>%{y}</b><br>" + title + ": %{z:+.2f}%<extra></extra>", showscale=False,
    ))
    fig = apply_plotly_theme(fig)
    fig.update_layout(height=max(300, 30 * len(sorted_series)), margin=dict(t=10, b=10), xaxis=dict(side="top"), yaxis=dict(autorange="reversed"))
    return fig

def create_mobile_line_chart(fig_desktop):
    fig_mobile = go.Figure(fig_desktop)
    fig_mobile.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(t=20, b=80))
    return fig_mobile

def create_html_table(df):
    th_html = "".join([f'<th style="text-align:left;padding:10px 12px;color:var(--text-muted);font-family:\'Space Mono\',monospace;font-size:10px;letter-spacing:2px;font-weight:400;border-bottom:1px solid var(--table-border);">{str(col).upper()}</th>' for col in df.columns])
    rows_html = ""
    for _, row in df.iterrows():
        tds = ""
        for val in row:
            color = "var(--text-main)"
            if isinstance(val, str) and "%" in val and (val.startswith("+") or val.startswith("-")):
                color = "var(--pos)" if val.startswith("+") else "var(--neg)"
            font = "'Space Mono', monospace;" if isinstance(val, (int, float)) or "$" in str(val) or "%" in str(val) else "'Syne', sans-serif;"
            weight = "700" if color != "var(--text-main)" else "500"
            tds += f'<td style="padding:10px 12px;color:{color};font-family:{font};font-weight:{weight};border-bottom:1px solid var(--table-border);">{val}</td>'
        rows_html += f"<tr>{tds}</tr>"
        
    return f"""
    <div style="border:1px solid var(--table-border);border-radius:12px;overflow:hidden;margin-bottom:16px;">
    <table style="width:100%;border-collapse:collapse;font-size:14px;background:var(--card-bg);">
        <thead><tr style="background:var(--table-header);">{th_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """

# ─────────────────────────────────────────────
# BASELINE & DATA FETCHING
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_baseline() -> dict:
    import json
    from pathlib import Path
    baseline_path = Path(__file__).parent / "baseline_prices.json"
    if not baseline_path.exists(): return {}
    with open(baseline_path) as f:
        data = json.load(f)
    return {k: v for k, v in data.get("prices", {}).items() if v is not None}

@st.cache_data(ttl=900, show_spinner=False)
def fetch_daily_history(tickers: tuple, start: str, end: str, _cache_bucket: int = 0):
    today, actual_end = date.today().isoformat(), min(end, date.today().isoformat())
    if start > today: start = today
    frames, missing = {}, []
    try: raw = yf.download(tickers, start=start, end=actual_end, auto_adjust=True, progress=False, group_by="ticker", threads=True, prepost=False)
    except Exception: raw = pd.DataFrame()

    for ticker in tickers:
        try:
            if raw.empty: raise ValueError("empty")
            if len(tickers) == 1: series = raw["Close"]
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
            except Exception: missing.append(ticker)
    if not frames: return pd.DataFrame(), list(tickers)
    prices = pd.DataFrame(frames)
    prices.index = pd.to_datetime(prices.index)
    prices.sort_index(inplace=True)
    return prices, missing

@st.cache_data(ttl=300, show_spinner=False)
def _do_fetch_latest_prices(tickers: tuple, _progress_placeholder=None) -> tuple[dict, dict]:
    import pytz
    et_tz = pytz.timezone("US/Eastern")
    current_prices, price_times = {}, {}

    def _unix_to_label(ts_unix) -> str:
        if not ts_unix: return ""
        return datetime.fromtimestamp(float(ts_unix), tz=pytz.utc).astimezone(et_tz).strftime("%b %d, %Y %I:%M %p ET")

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
        return price, ts.timestamp(), ts.astimezone(et_tz).strftime("%b %d, %Y %I:%M %p ET")

    def _fetch_single_ticker(ticker):
        price, label = None, "unavailable"
        t = yf.Ticker(ticker)
        try:
            info = t.info
            candidates = []
            for p_key, t_key, suffix in [("postMarketPrice", "postMarketTime", "after-hours"), ("preMarketPrice", "preMarketTime", "pre-market"), ("currentPrice", "regularMarketTime", "")]:
                p, tm = info.get(p_key), info.get(t_key)
                if not p: p = info.get("regularMarketPrice") if p_key == "currentPrice" else None
                if p and float(p) > 0 and tm: candidates.append((float(p), float(tm), suffix))
            if candidates:
                best = max(candidates, key=lambda x: x[1])
                price, label = best[0], _unix_to_label(best[1]) + (f" ({best[2]})" if best[2] else "")
        except Exception: pass

        if price is None:
            try:
                fi = t.fast_info
                reg_p, reg_t = getattr(fi, "last_price", None), getattr(fi, "regular_market_time", None)
                if reg_p and float(reg_p) > 0 and reg_t: price, label = float(reg_p), _unix_to_label(float(reg_t))
            except Exception: pass

        if price is None:
            try: price, _, label = _parse_history_latest(t.history(period="5d", interval="1m", prepost=True, auto_adjust=True))
            except Exception: pass

        if price is None:
            try:
                price, _, label = _parse_history_latest(t.history(period="10d", interval="1d", prepost=False, auto_adjust=True))
                label = label.replace(" ET", " ET (close)")
            except Exception: pass

        return ticker, price, label if price is not None else "unavailable"

    total = len(tickers)
    completed = 0
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(_fetch_single_ticker, t): t for t in tickers}
        for future in as_completed(futures):
            ticker, price, label = future.result()
            current_prices[ticker] = price
            price_times[ticker] = label
            completed += 1

    return current_prices, price_times

def compute_portfolio_history(daily_prices: pd.DataFrame, participants: dict, baseline: dict, missing_tickers: list) -> pd.DataFrame:
    portfolios = {}
    for name, tickers in participants.items():
        total = pd.Series(0.0, index=daily_prices.index)
        for ticker in tickers:
            base = baseline.get(ticker)
            if base and base > 0 and ticker in daily_prices.columns and ticker not in missing_tickers:
                total += (daily_prices[ticker].ffill() / base) * INITIAL
            else: total += INITIAL
        portfolios[name] = total
    return pd.DataFrame(portfolios)

def compute_current_portfolio(current_prices: dict, participants: dict, baseline: dict) -> pd.Series:
    values = {}
    for name, tickers in participants.items():
        total = sum([(current_prices.get(t) / baseline.get(t)) * INITIAL if (baseline.get(t) and baseline.get(t) > 0 and current_prices.get(t)) else INITIAL for t in tickers])
        values[name] = total
    return pd.Series(values)

def compute_benchmark_history(daily_prices: pd.DataFrame, baseline: dict, missing_tickers: list) -> pd.DataFrame:
    benchmarks = {}
    for label, ticker in BENCHMARKS.items():
        base = baseline.get(ticker)
        if base and base > 0 and ticker in daily_prices.columns and ticker not in missing_tickers:
            benchmarks[label] = (daily_prices[ticker].ffill() / base) * TOTAL_INV
    return pd.DataFrame(benchmarks)

def compute_current_benchmarks(current_prices: dict, baseline: dict) -> pd.Series:
    return pd.Series({label: ((current_prices.get(ticker) / baseline.get(ticker)) * TOTAL_INV) if (baseline.get(ticker) and baseline.get(ticker) > 0 and current_prices.get(ticker)) else TOTAL_INV for label, ticker in BENCHMARKS.items()})

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏆 Championship 2026")
    st.markdown('<p style="color:var(--text-muted);font-size:12px;font-family:\'Space Mono\',monospace;">MAR 01 – DEC 31, 2026</p>', unsafe_allow_html=True)
    st.divider()
    filter_opt = st.radio("**Participant Filter**", ["All Participants", "Human Only", "AI Only"], index=0)
    st.divider()
    st.markdown('<p style="color:var(--text-muted);font-size:11px;">Initial investment: $1,000 per stock<br>Total per portfolio: $4,000<br><br>Baseline: Feb 27, 2026 close<br>Live prices include after-hours</p>', unsafe_allow_html=True)

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
if missing_from_baseline:
    try:
        missing_df, _ = fetch_daily_history(tuple(missing_from_baseline), ANCHOR_DATE, "2026-02-28", 0)
        for t in missing_from_baseline:
            if t in missing_df.columns and not missing_df.empty: baseline[t] = float(missing_df[t].iloc[0])
            elif len(missing_from_baseline) == 1 and not missing_df.empty: baseline[t] = float(missing_df.iloc[0])
    except Exception: pass

# ─── Loading UI ───
import threading, time

if _jump_to_deep_dive:
    # Data is already cached from initial load — fetch directly, no animation
    daily_prices, missing_tickers = fetch_daily_history(
        _tickers_tuple, ANCHOR_DATE, END_DATE,
        _cache_bucket=int(datetime.now().timestamp() // 900)
    )
    current_prices, price_times = _do_fetch_latest_prices(_tickers_tuple)
else:
    _loading_container = st.empty()
    with _loading_container.container():
        st.markdown("""
        <div style="background:var(--card-bg);border:1px solid var(--card-border);border-radius:16px;
                    padding:32px;text-align:center;margin:20px 0;backdrop-filter:blur(10px);">
            <div style="font-family:'Space Mono',monospace;font-size:11px;letter-spacing:4px;
                        color:var(--text-muted);text-transform:uppercase;margin-bottom:12px;">📡 Loading Market Data</div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;
                        color:var(--text-main);margin-bottom:4px;">Fetching live prices…</div>
            <div style="font-family:'Space Mono',monospace;font-size:12px;color:var(--text-muted);">
                Downloading data for <strong>{len(_tickers_tuple)}</strong> tickers
            </div>
        </div>
        """.replace("{len(_tickers_tuple)}", str(len(_tickers_tuple))), unsafe_allow_html=True)
        _progress_bar = st.progress(0, text="Fetching daily price history…")

        # Step 1: Daily history (bulk download) — animate 0% → 30%
        _hist_done = threading.Event()
        _hist_result = {}

        def _bg_hist():
            _hist_result["prices"], _hist_result["missing"] = fetch_daily_history(
                _tickers_tuple, ANCHOR_DATE, END_DATE,
                _cache_bucket=int(datetime.now().timestamp() // 900)
            )
            _hist_done.set()

        threading.Thread(target=_bg_hist, daemon=True).start()

        _pct = 0
        while not _hist_done.is_set():
            _hist_done.wait(timeout=0.15)
            if _pct < 28:
                _pct = min(_pct + 1, 28)
                _progress_bar.progress(_pct, text=f"Fetching daily price history… {_pct}%")

        daily_prices, missing_tickers = _hist_result["prices"], _hist_result["missing"]

        # Ramp to 30%
        for _p in range(_pct + 1, 31):
            _progress_bar.progress(_p, text=f"Daily history loaded… {_p}%")
            time.sleep(0.01)
        _pct = 30
        _progress_bar.progress(30, text="Daily history loaded. Fetching live prices…")

        # Step 2: Live prices (parallelized) — animate 30% → 95%
        _fetch_done = threading.Event()
        _fetch_result = {}

        def _bg_fetch():
            _fetch_result["prices"], _fetch_result["times"] = _do_fetch_latest_prices(_tickers_tuple)
            _fetch_done.set()

        threading.Thread(target=_bg_fetch, daemon=True).start()

        while not _fetch_done.is_set():
            _fetch_done.wait(timeout=0.15)
            if _pct < 95:
                _pct = min(_pct + 1, 95)
                _progress_bar.progress(_pct, text=f"Fetching live prices… {_pct}%")

        current_prices, price_times = _fetch_result["prices"], _fetch_result["times"]

        # Ramp to 100%
        for _p in range(_pct + 1, 101):
            _progress_bar.progress(_p, text=f"Finalizing… {_p}%")
            time.sleep(0.01)

        _progress_bar.progress(100, text="✅ All data loaded!")
        time.sleep(0.8)

    _loading_container.empty()

if daily_prices.empty:
    st.error("Could not fetch daily price history. Please check your internet connection.")
    st.stop()

def _parse_label_dt(label: str):
    try: return datetime.strptime(label.split(" ET")[0].strip(), "%b %d, %Y %I:%M %p")
    except Exception: return datetime.min

_valid_times = {tk: lbl for tk, lbl in price_times.items() if lbl not in ("unavailable", "", None)}
last_updated = max(_valid_times.values(), key=_parse_label_dt) if _valid_times else "unavailable"

portfolio_df  = compute_portfolio_history(daily_prices, active_participants, baseline, missing_tickers)
benchmark_df  = compute_benchmark_history(daily_prices, baseline, missing_tickers)
current_portfolio  = compute_current_portfolio(current_prices, active_participants, baseline)
current_benchmarks = compute_current_benchmarks(current_prices, baseline)

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

colors = (px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.Alphabet)[:len(active_participants)]

# ─────────────────────────────────────────────
# TOP BAR & TITLE
# ─────────────────────────────────────────────
c1, c2 = st.columns([8, 3])
with c1:
    st.markdown("""
    <div style="padding: 16px 0 8px 0;">
        <h1 style="font-family:'Syne',sans-serif;font-size:36px;font-weight:800;
                   background:linear-gradient(135deg,var(--text-main),var(--text-value));
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   margin:0;line-height:1.1;">
            Stock Market<br>Championship 2026
        </h1>
        <p style="color:var(--text-muted);font-family:'Space Mono',monospace;font-size:12px;
                  letter-spacing:3px;margin-top:8px;">
            LIVE COMPETITION TRACKER · BASELINE: FEB 27
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.write("") 
    theme_choice = st.radio("Theme", ["Auto", "Light", "Dark"], index=["Auto", "Light", "Dark"].index(st.session_state.theme_setting), format_func=lambda x: {"Auto":"💻 Auto", "Light":"☀️ Light", "Dark":"🌙 Dark"}[x], horizontal=True, label_visibility="collapsed")
    if theme_choice != st.session_state.theme_setting:
        st.session_state.theme_setting = theme_choice
        st.rerun()

st.markdown(
    f"""<div style="display:inline-flex;align-items:center;gap:8px;
                    background:var(--card-bg);border:1px solid var(--card-border);
                    border-radius:8px;padding:6px 14px;margin-bottom:4px;">
        <span style="font-size:14px;">🕐</span>
        <span style="font-family:'Space Mono',monospace;font-size:11px;color:var(--text-value);letter-spacing:1px;">
            LATEST AVAILABLE PRICE: <strong>{last_updated}</strong>
        </span>
    </div>""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
if _jump_to_deep_dive:
    # Hide ENTIRE tabs container (header + content) until Deep Dive is selected
    st.markdown('<style id="deep-dive-hide">.stTabs { opacity: 0 !important; }</style>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Overall Leaderboard", "📈 Daily Leaderboard", "📅 Monthly Leaderboard", 
    "📊 Benchmarks", "📆 Monthly Breakdown", "🔍 Deep Dive",
])

if _jump_to_deep_dive:
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (function() {
        const doc = window.parent.document;
        const clickDeepDiveTab = () => {
            const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
            for (const tab of tabs) {
                if (tab.textContent.includes('Deep Dive')) {
                    tab.click();
                    // Wait for Streamlit to process the tab switch, then reveal
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            const hideStyle = doc.getElementById('deep-dive-hide') || 
                                [...doc.querySelectorAll('style')].find(s => s.textContent.includes('deep-dive-hide') || (s.textContent.includes('.stTabs') && s.textContent.includes('opacity: 0')));
                            if (hideStyle) hideStyle.remove();
                            // Also remove any matching style tags
                            doc.querySelectorAll('style').forEach(s => {
                                if (s.textContent.includes('.stTabs') && s.textContent.includes('opacity: 0')) s.remove();
                            });
                        });
                    });
                    return true;
                }
            }
            return false;
        };
        const interval = setInterval(() => {
            if (clickDeepDiveTab()) clearInterval(interval);
        }, 20);
        setTimeout(() => {
            clearInterval(interval);
            // Failsafe: always reveal after 2s
            doc.querySelectorAll('style').forEach(s => {
                if (s.textContent.includes('.stTabs') && s.textContent.includes('opacity: 0')) s.remove();
            });
        }, 2000);
    })();
    </script>
    """, height=0, width=0)

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
                <div class="metric-name"><a href="?participant={row['Participant']}" target="_self">{row['Participant']}</a></div>
                <div class="metric-value">${row['Portfolio ($)']:,.2f}</div>
                <div class="metric-return {ret_color}">{ret_sign}{row['Return (%)']:.2f}%</div>
                <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">{row['Type']}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown('<div class="section-header">Overall Performance</div>', unsafe_allow_html=True)
    sorted_overall = leaderboard.set_index("Participant")["Return (%)"].sort_values(ascending=False)
    
    fig_hm_ov = go.Figure(data=go.Heatmap(
        z=sorted_overall.values.reshape(1, -1), x=sorted_overall.index.tolist(), y=["Overall Return"],
        colorscale=heat_colors, zmid=0, text=[[f"{v:+.1f}" for v in sorted_overall.values]], texttemplate="%{text}",
        textfont=dict(size=10, family="Space Mono", color=heat_font), hovertemplate="<b>%{x}</b><br>Overall: %{z:+.2f}%<extra></extra>",
        showscale=True, colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_ov = apply_plotly_theme(fig_hm_ov)
    fig_hm_ov.update_layout(height=180, xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False))
    render_responsive_plot(fig_hm_ov, create_mobile_heatmap(sorted_overall, "Overall Return"))

    st.markdown('<div class="section-header">Full Leaderboard</div>', unsafe_allow_html=True)
    
    formatted_leaderboard = leaderboard[["Rank", "Participant", "Portfolio ($)", "Return (%)", "Type"]].copy()
    formatted_leaderboard["Participant"] = formatted_leaderboard["Participant"].map(lambda x: f'<a href="?participant={x}" target="_self" style="color:var(--text-main);text-decoration:none;font-weight:700;transition:color 0.2s;" onmouseover="this.style.color=\'var(--text-value)\'" onmouseout="this.style.color=\'var(--text-main)\'">{x}</a>')
    formatted_leaderboard["Portfolio ($)"] = formatted_leaderboard["Portfolio ($)"].map("${:,.2f}".format)
    formatted_leaderboard["Return (%)"] = formatted_leaderboard["Return (%)"].map("{:+.2f}%".format)
    st.markdown(create_html_table(formatted_leaderboard), unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Portfolio Value Over Time</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for i, col_name in enumerate(chart_df.columns):
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df[col_name], name=col_name, line=dict(width=2, color=colors[i % len(colors)]), hovertemplate=f"<b>{col_name}</b><br>Date: %{{x|%b %d}}<br>Value: $%{{y:,.2f}}<extra></extra>"))
    fig.add_hline(y=TOTAL_INV, line_dash="dot", line_color=plotly_grid or "rgba(128,128,128,0.5)", annotation_text="Initial $4,000")
    fig = apply_plotly_theme(fig, prefix="$")
    fig.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"), height=450)
    render_responsive_plot(fig, create_mobile_line_chart(fig))

    st.markdown('<div class="section-header">Total Return % Over Time</div>', unsafe_allow_html=True)
    ret_df = ((chart_df - TOTAL_INV) / TOTAL_INV * 100).round(3)
    fig_ret = go.Figure()
    for i, col_name in enumerate(ret_df.columns):
        fig_ret.add_trace(go.Scatter(x=ret_df.index, y=ret_df[col_name], name=col_name, line=dict(width=2, color=colors[i % len(colors)]), hovertemplate=f"<b>{col_name}</b><br>%{{x|%b %d}}<br>Return: %{{y:+.2f}}%<extra></extra>"))
    fig_ret.add_hline(y=0, line_dash="dot", line_color=plotly_grid or "rgba(128,128,128,0.5)", annotation_text="Baseline")
    fig_ret = apply_plotly_theme(fig_ret, suffix="%")
    fig_ret.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)", orientation="v", x=1.01, y=1), height=450, margin=dict(r=120))
    render_responsive_plot(fig_ret, create_mobile_line_chart(fig_ret))


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
        w_color = "var(--pos)" if todays_winner_val >= 0 else "var(--neg)"
        st.markdown(f"""
        <div class="metric-card gold" style="text-align:center;">
            <div class="metric-rank">🏅 TODAY'S LEADER</div>
            <div class="metric-name"><a href="?participant={todays_winner}" target="_self">{todays_winner}</a></div>
            <div class="metric-return" style="color:{w_color};font-size:26px;">{todays_winner_val:+.2f}%</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">{todays_winner_type} · vs yesterday's close</div>
        </div>
        """, unsafe_allow_html=True)

    sorted_today = todays_gain_pct.sort_values(ascending=False)
    
    fig_hm_daily = go.Figure(data=go.Heatmap(
        z=sorted_today.values.reshape(1, -1), x=sorted_today.index.tolist(), y=["Today's Return"],
        colorscale=heat_colors, zmid=0, text=[[f"{v:+.1f}" for v in sorted_today.values]], texttemplate="%{text}",
        textfont=dict(size=10, family="Space Mono", color=heat_font), hovertemplate="<b>%{x}</b><br>Today: %{z:+.2f}%<extra></extra>", showscale=True,
        colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_daily = apply_plotly_theme(fig_hm_daily)
    fig_hm_daily.update_layout(height=180, xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False))
    render_responsive_plot(fig_hm_daily, create_mobile_heatmap(sorted_today, "Today's Return"))

    st.markdown('<div class="section-header">Full Today\'s Ranking</div>', unsafe_allow_html=True)
    today_df = pd.DataFrame({
        "Rank": range(1, len(sorted_today) + 1),
        "Participant": [f'<a href="?participant={p}" target="_self" style="color:var(--text-main);text-decoration:none;font-weight:700;transition:color 0.2s;" onmouseover="this.style.color=\'var(--text-value)\'" onmouseout="this.style.color=\'var(--text-main)\'">{p}</a>' for p in sorted_today.index],
        "Today's Return": sorted_today.map("{:+.2f}%".format),
        "Live Portfolio": current_portfolio[sorted_today.index].map("${:,.2f}".format),
        "Type": [("🤖 AI" if p in AI_PARTICIPANTS else "👤 Human") for p in sorted_today.index],
    })
    st.markdown(create_html_table(today_df), unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3: MONTHLY LEADERBOARD
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Current Month Performance</div>', unsafe_allow_html=True)
    
    curr_mth_start = pd.Timestamp(date.today().replace(day=1))
    hist_before_mth = portfolio_df[portfolio_df.index < curr_mth_start]
    
    if len(hist_before_mth) > 0: prev_month_close = hist_before_mth.iloc[-1]
    else: prev_month_close = pd.Series(TOTAL_INV, index=current_portfolio.index)

    live_total_ret_pct = ((current_portfolio - TOTAL_INV) / TOTAL_INV * 100)
    prev_mth_ret_pct = ((prev_month_close - TOTAL_INV) / TOTAL_INV * 100)
    mtd_gain_pct = (live_total_ret_pct - prev_mth_ret_pct).round(3)

    mtd_winner = mtd_gain_pct.idxmax()
    mtd_winner_val = mtd_gain_pct.max()
    mtd_winner_type = "🤖 AI" if mtd_winner in AI_PARTICIPANTS else "👤 Human"

    m_col, spacer = st.columns([1, 2])
    with m_col:
        m_color = "var(--pos)" if mtd_winner_val >= 0 else "var(--neg)"
        st.markdown(f"""
        <div class="metric-card gold" style="text-align:center;">
            <div class="metric-rank">🏅 MONTH'S LEADER</div>
            <div class="metric-name"><a href="?participant={mtd_winner}" target="_self">{mtd_winner}</a></div>
            <div class="metric-return" style="color:{m_color};font-size:26px;">{mtd_winner_val:+.2f}%</div>
            <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">{mtd_winner_type} · Month-To-Date</div>
        </div>
        """, unsafe_allow_html=True)

    sorted_mtd = mtd_gain_pct.sort_values(ascending=False)
    
    fig_hm_mtd = go.Figure(data=go.Heatmap(
        z=sorted_mtd.values.reshape(1, -1), x=sorted_mtd.index.tolist(), y=["MTD Return"],
        colorscale=heat_colors, zmid=0, text=[[f"{v:+.1f}" for v in sorted_mtd.values]], texttemplate="%{text}",
        textfont=dict(size=10, family="Space Mono", color=heat_font), hovertemplate="<b>%{x}</b><br>MTD: %{z:+.2f}%<extra></extra>", showscale=True,
        colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)", tickfont=dict(family="Space Mono", size=10)),
    ))
    fig_hm_mtd = apply_plotly_theme(fig_hm_mtd)
    fig_hm_mtd.update_layout(height=180, xaxis=dict(side="bottom", tickangle=-30), yaxis=dict(showticklabels=False))
    render_responsive_plot(fig_hm_mtd, create_mobile_heatmap(sorted_mtd, "MTD Return"))

    st.markdown('<div class="section-header">Full MTD Ranking</div>', unsafe_allow_html=True)
    mtd_df = pd.DataFrame({
        "Rank": range(1, len(sorted_mtd) + 1),
        "Participant": [f'<a href="?participant={p}" target="_self" style="color:var(--text-main);text-decoration:none;font-weight:700;transition:color 0.2s;" onmouseover="this.style.color=\'var(--text-value)\'" onmouseout="this.style.color=\'var(--text-main)\'">{p}</a>' for p in sorted_mtd.index],
        "MTD Return": sorted_mtd.map("{:+.2f}%".format),
        "Live Portfolio": current_portfolio[sorted_mtd.index].map("${:,.2f}".format),
        "Type": [("🤖 AI" if p in AI_PARTICIPANTS else "👤 Human") for p in sorted_mtd.index],
    })
    st.markdown(create_html_table(mtd_df), unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 4: BENCHMARKS
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Portfolio vs Benchmarks (% Return)</div>', unsafe_allow_html=True)
    avg_portfolio = chart_df.mean(axis=1)
    
    avg_portfolio_pct = ((avg_portfolio - TOTAL_INV) / TOTAL_INV * 100).round(2)
    benchmark_df_live = compute_benchmark_history(daily_prices, baseline, missing_tickers)
    benchmark_df_live.loc[live_timestamp] = current_benchmarks
    benchmark_pct = ((benchmark_df_live - TOTAL_INV) / TOTAL_INV * 100).round(2)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=avg_portfolio_pct.index, y=avg_portfolio_pct, name=f"Avg Portfolio ({filter_opt})", line=dict(width=3, color="#63b3ed"), fill="tozeroy", fillcolor="rgba(99,179,237,0.05)", hovertemplate="<b>Avg Portfolio</b><br>%{y:+.2f}%<extra></extra>"))
    bm_colors = ["#F6D860","#68d391","#fc8181","#b794f4"]
    for i, col_name in enumerate(benchmark_pct.columns):
        fig2.add_trace(go.Scatter(x=benchmark_pct.index, y=benchmark_pct[col_name], name=col_name, line=dict(width=2, color=bm_colors[i % len(bm_colors)], dash="dash"), hovertemplate=f"<b>{col_name}</b><br>%{{y:+.2f}}%<extra></extra>"))
    
    fig2.add_hline(y=0, line_dash="dot", line_color=plotly_grid or "rgba(128,128,128,0.5)")
    fig2 = apply_plotly_theme(fig2, suffix="%")
    fig2.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"), height=500)
    render_responsive_plot(fig2, create_mobile_line_chart(fig2))
    
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
        st.markdown(create_html_table(bm_table), unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 5: MONTHLY BREAKDOWN
# ══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Monthly Performance</div>', unsafe_allow_html=True)
    
    full_history = pd.concat([portfolio_df, pd.DataFrame([current_portfolio.values], columns=current_portfolio.index, index=[pd.Timestamp(datetime.now())])])
    monthly = full_history.resample("ME").last()
    
    monthly_gain = monthly.diff().dropna() 
    monthly_pct  = (monthly_gain / monthly.shift(1).dropna() * 100).round(2)
    
    monthly_pct = monthly_pct[monthly_pct.index >= pd.Timestamp("2026-03-01")]
    monthly_gain = monthly_gain[monthly_gain.index >= pd.Timestamp("2026-03-01")]
    
    monthly_pct = monthly_pct.reindex(sorted(monthly_pct.columns, key=lambda x: x.lower()), axis=1)
    
    if not monthly_gain.empty:
        months_fmt = monthly_pct.index.strftime("%b %Y")
        fig3 = go.Figure(data=go.Heatmap(
            z=monthly_pct.T.values, x=months_fmt, y=monthly_pct.columns.tolist(),
            colorscale=heat_colors, zmid=0, text=monthly_pct.T.values, texttemplate="%{text:.1f}%", textfont=dict(size=11, family="Space Mono", color=heat_font),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Return: %{z:.2f}%<extra></extra>", colorbar=dict(tickformat=".1f", ticksuffix="%", outlinewidth=0, bgcolor="rgba(0,0,0,0)")
        ))
        fig3 = apply_plotly_theme(fig3)
        fig3.update_layout(height=max(400, 30 * len(portfolio_df.columns) + 80), xaxis=dict(side="top"))
        st.plotly_chart(fig3, use_container_width=True, theme=None if st.session_state.theme_setting != "Auto" else "streamlit")
        
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
            st.markdown(create_html_table(pd.DataFrame(winner_data)), unsafe_allow_html=True)
    else:
        st.info("Not enough data for monthly breakdown yet.")


# ══════════════════════════════════════════════
# TAB 6: INDIVIDUAL DEEP DIVE
# ══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">Individual Portfolio Analysis</div>', unsafe_allow_html=True)
    participant_names = list(active_participants.keys())
    
    default_idx = 0
    if "deep_dive_selection" in st.session_state and st.session_state["deep_dive_selection"] in participant_names:
        default_idx = participant_names.index(st.session_state["deep_dive_selection"])
        
    selected = st.selectbox("Select Participant", participant_names, index=default_idx, key="deep_dive")
    st.session_state["deep_dive_selection"] = selected

    if selected:
        tickers   = active_participants[selected]
        part_type = "🤖 AI" if selected in AI_PARTICIPANTS else "👤 Human"

        stock_hist = {}
        for ticker in tickers:
            base = baseline.get(ticker)
            if base and base > 0 and ticker in daily_prices.columns:
                stock_hist[ticker] = (daily_prices[ticker].ffill() / base) * INITIAL
            else:
                stock_hist[ticker] = pd.Series(INITIAL, index=daily_prices.index)
        stock_df = pd.DataFrame(stock_hist)
        
        live_hist_row = {}
        for tk in tickers:
            cp, bp = current_prices.get(tk), baseline.get(tk)
            live_hist_row[tk] = (cp / bp) * INITIAL if (cp and bp) else INITIAL
        stock_df.loc[live_timestamp] = live_hist_row

        stock_colors_ind = ["#63b3ed", "#68d391", "#F6D860", "#fc8181"]
        col1, col2, col3, col4 = st.columns(4)

        for i, (col, ticker) in enumerate(zip([col1, col2, col3, col4], tickers)):
            val      = live_hist_row[ticker]
            ret      = (val - INITIAL) / INITIAL * 100
            ts       = price_times.get(ticker, "—")
            base_px  = baseline.get(ticker)
            curr_px  = current_prices.get(ticker)
            with col:
                color = "var(--pos)" if ret >= 0 else "var(--neg)"
                base_str = f"${base_px:,.2f}" if base_px else "N/A"
                curr_str = f"${curr_px:,.4f}" if curr_px else "N/A"
                st.markdown(f"""
                <div class="metric-card" style="border-top:3px solid {stock_colors_ind[i]};">
                    <div class="metric-rank">{ticker}</div>
                    <div class="metric-value" style="font-size:20px;">${val:,.2f}</div>
                    <div class="metric-return" style="color:{color};">{ret:+.2f}%</div>
                    <div style="margin-top:10px;font-family:'Space Mono',monospace;font-size:11px;color:var(--text-muted);line-height:2.0;">
                        <span>BASE</span>&nbsp;&nbsp;{base_str}<br>
                        <span>NOW&nbsp;</span>&nbsp;&nbsp;{curr_str}<br>
                        <span style="font-size:10px;">{ts}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        total_val = sum(live_hist_row.values())
        total_ret = (total_val - TOTAL_INV) / TOTAL_INV * 100

        st.markdown(f"""
        <div style="text-align:center;margin:16px 0;padding:16px;background:var(--card-bg);border-radius:12px;border:1px solid var(--card-border);">
            <span style="font-family:'Space Mono',monospace;color:var(--text-muted);font-size:12px;">{selected} {part_type} — Total Portfolio (live)</span><br>
            <span style="font-family:'Space Mono',monospace;font-size:32px;font-weight:700;color:var(--text-value);">${total_val:,.2f}</span>
            <span style="font-family:'Space Mono',monospace;font-size:18px;color:{'var(--pos)' if total_ret >= 0 else 'var(--neg)'};margin-left:12px;">{total_ret:+.2f}%</span>
        </div>
        """, unsafe_allow_html=True)
        
        fig4 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_df.columns:
                fig4.add_trace(go.Scatter(x=stock_df.index, y=stock_df[ticker], name=ticker, line=dict(width=2.5, color=stock_colors_ind[i]), hovertemplate=f"<b>{ticker}</b><br>$%{{y:,.2f}}<extra></extra>"))
        fig4.add_hline(y=INITIAL, line_dash="dot", line_color=plotly_grid or "rgba(128,128,128,0.5)", annotation_text="Initial $1,000")
        fig4 = apply_plotly_theme(fig4, prefix="$")
        fig4.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"), height=420, title=dict(text=f"{selected}'s Portfolio — Individual Stock Performance", font=dict(size=14, color=plotly_font or "#718096"), x=0))
        st.plotly_chart(fig4, use_container_width=True, theme=None if st.session_state.theme_setting != "Auto" else "streamlit")
        
        stock_pct = ((stock_df - INITIAL) / INITIAL * 100)
        fig5 = go.Figure()
        for i, ticker in enumerate(tickers):
            if ticker in stock_pct.columns:
                fig5.add_trace(go.Scatter(x=stock_pct.index, y=stock_pct[ticker], name=ticker, line=dict(width=2, color=stock_colors_ind[i], dash="dot"), hovertemplate=f"<b>{ticker}</b><br>%{{y:+.2f}}%<extra></extra>"))
        fig5.add_hline(y=0, line_color=plotly_grid or "rgba(128,128,128,0.5)")
        fig5 = apply_plotly_theme(fig5, suffix="%")
        fig5.update_layout(legend=dict(bgcolor="rgba(0,0,0,0)"), height=350, title=dict(text="Percentage Return by Stock", font=dict(size=14, color=plotly_font or "#718096"), x=0))
        st.plotly_chart(fig5, use_container_width=True, theme=None if st.session_state.theme_setting != "Auto" else "streamlit")

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<p style="text-align:center;color:var(--text-muted);font-family:'Space Mono',monospace;font-size:11px;letter-spacing:2px;">
    STOCK MARKET CHAMPIONSHIP 2026 · DATA VIA YAHOO FINANCE<br>
    BASELINE: FEB 27, 2026 4:00 PM ET CLOSE · LIVE PRICES REFRESH EVERY 5 MIN · CHARTS REFRESH EVERY 15 MIN
</p>
""", unsafe_allow_html=True)