# 🚀 Deployment Guide — Stock Market Championship 2026
## Deploy to Render (Free Web Service)

---

### Step 1 — Generate the Locked Baseline Prices (run ONCE locally)

Before deploying, you need to generate `baseline_prices.json` — the file that permanently stores every ticker's Feb 27, 2026 4:00 PM ET regular-session close price.

```bash
# Install dependencies locally first
pip install -r requirements.txt

# Run the one-time baseline fetcher
python fetch_baseline.py
```

This will print each ticker and its locked price, then save `baseline_prices.json` in the same folder. **Verify the output looks correct** (all tickers have prices, no unexpected NULLs).

> ⚠️ **Run this on or after March 1, 2026.** The Feb 27 trading session must have completed for the prices to be available via yfinance.

---

### Step 2 — Prepare Your GitHub Repository

Add **all four files** to the root of a new GitHub repo (e.g. `stock-comp-2026`):

```
app.py
fetch_baseline.py
baseline_prices.json     ← commit this after running Step 1
requirements.txt
```

Commit and push to `main`.

> **Important:** `baseline_prices.json` must be committed to the repo. Render has no persistent local storage, so if it's missing the app will show an error.

---

### Step 3 — Create a Render Account

1. Go to [https://render.com](https://render.com) and sign up (free).
2. Connect your GitHub account when prompted.

---

### Step 4 — Create a New Web Service

1. On your Render Dashboard, click **"New +"** → **"Web Service"**.
2. Select your GitHub repo (`stock-comp-2026`).
3. Fill in the settings:

| Setting           | Value                                      |
|-------------------|--------------------------------------------|
| **Name**          | `stock-comp-2026`                          |
| **Runtime**       | `Python 3`                                 |
| **Region**        | Choose nearest to you                      |
| **Branch**        | `main`                                     |
| **Build Command** | `pip install -r requirements.txt`          |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |
| **Instance Type** | `Free`                                     |

4. Click **"Create Web Service"**.

---

### Step 5 — Wait for Deploy

Render will install dependencies and start the app. After ~2–3 minutes your dashboard will be live at:

```
https://stock-comp-2026.onrender.com
```

---

### Step 6 — Keep It Alive (Optional — Free Tier Caveat)

Free Render services spin down after 15 minutes of inactivity. To prevent this:
- Use a free uptime monitor like [UptimeRobot](https://uptimerobot.com)
- Set it to ping `https://stock-comp-2026.onrender.com` every 5 minutes

---

### How the Price Architecture Works

| Purpose | Source | Refresh |
|---------|--------|---------|
| **Baseline (anchor)** | `baseline_prices.json` — locked forever | Never re-fetched |
| **Daily chart history** | `yf.download()` — regular session close | Every 15 min |
| **Live leaderboard & cards** | `yf.Ticker.fast_info.last_price` — includes after-hours & pre-market | Every 5 min |

The "last updated" timestamp shown in the app reflects when the live price quote was last retrieved, and will say e.g. `Mar 15, 2026 06:23 AM ET` during pre-market hours so users always know what they're looking at.

---

### Local Development

```bash
pip install -r requirements.txt
python fetch_baseline.py   # once only
streamlit run app.py
```

Opens at `http://localhost:8501`.

