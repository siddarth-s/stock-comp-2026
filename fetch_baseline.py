"""
fetch_baseline.py
─────────────────
Run this ONCE to lock in the Feb 27, 2026 4 PM ET regular-session closing
prices for every ticker in the competition.

Usage:
    python fetch_baseline.py

This writes / overwrites baseline_prices.json in the same directory.
Commit that file to your GitHub repo — the main app.py will read from it
and NEVER call yfinance for baseline prices again.
"""

import json
import sys
from pathlib import Path
import yfinance as yf
import pandas as pd

ANCHOR_DATE  = "2026-02-27"
NEXT_DAY     = "2026-02-28"   # yfinance end is exclusive, so +1 day to capture Feb 27

TICKERS = [
    # Human participants
    "MU", "AAPL", "GLD", "COST",
    "RKLB", "WDC", "ASML", "GE",
    "GME", "HOOD", "HYMC", "RCAT",
    "ASTS", "POET", "META", "SLV",
    "NVDA", "AVGO", "SMCI", "SNOW",
    "SNDK", "AMZN", "AGI", "NFLX",
    "SOFI", "MSFT", "PANW", "NVO",
    "PLTR", "COIN", "TSLA", "TSM",
    "GOOG", "AMD", "BABA", "RIVN",
    "MRVL", "FLY", "INTC", "TMC",
    # AI participants
    "CEG", "APP", "AXON", "ARM",
    "KLAC", "VRT", "CDNS", "DDOG",
    "UBER", "CELH", "CRWD", "LUNR",
    "LLY", "DELL", "MSTR", "NOW",
    "ANET", "BSX", "V", "ISRG",
    "MDB", "ZS", "SNPS", "ADSK",
    "VKTX", "SONY", "ACLX", "USAR",
    # Benchmarks
    "SPY", "QQQ", "BTC-USD", "UUP",
]

OUT_FILE = Path(__file__).parent / "baseline_prices.json"


def fetch_close(ticker: str) -> float | None:
    """Fetch the regular-session 4 PM close for a single ticker on ANCHOR_DATE."""
    try:
        df = yf.download(
            ticker,
            start=ANCHOR_DATE,
            end=NEXT_DAY,
            auto_adjust=True,
            progress=False,
            prepost=False,   # regular session ONLY — no pre/after-hours
        )
        if df.empty:
            return None
        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        # Should be exactly one row (Feb 27)
        return round(float(close.iloc[-1]), 6)
    except Exception as e:
        print(f"  ⚠️  {ticker}: {e}")
        return None


def main():
    print(f"\n📌 Fetching Feb 27, 2026 4 PM ET closing prices for {len(TICKERS)} tickers...\n")

    prices = {}
    missing = []

    for i, ticker in enumerate(TICKERS, 1):
        price = fetch_close(ticker)
        if price is not None:
            prices[ticker] = price
            print(f"  [{i:02d}/{len(TICKERS)}] {ticker:<10} ${price:>12.4f}")
        else:
            prices[ticker] = None
            missing.append(ticker)
            print(f"  [{i:02d}/{len(TICKERS)}] {ticker:<10} *** MISSING — will assume $0 gain ***")

    payload = {
        "_metadata": {
            "anchor_date":  ANCHOR_DATE,
            "anchor_time":  "16:00 ET (regular session close, no after-hours)",
            "description":  (
                "Official competition baseline — regular session close prices at "
                "4:00 PM ET on Friday, February 27, 2026. "
                "These prices are LOCKED and will never be re-fetched."
            ),
            "source":       "Yahoo Finance (auto_adjust=True, prepost=False)",
            "missing":      missing,
        },
        "prices": prices,
    }

    with open(OUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ Saved {len(prices)} tickers → {OUT_FILE}")
    if missing:
        print(f"⚠️  Missing ({len(missing)}): {', '.join(missing)}")
    print("\nNext step: commit baseline_prices.json to your GitHub repo.\n")


if __name__ == "__main__":
    main()
