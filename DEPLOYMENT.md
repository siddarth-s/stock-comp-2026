# 🚀 Deployment Guide — Stock Market Championship 2026
## Deploy to Render (Free Web Service)

---

### Step 1 — Prepare Your GitHub Repository

1. Create a new GitHub repository (e.g., `stock-championship-2026`).
2. Add the following files to the root of the repo:
   ```
   app.py
   requirements.txt
   ```
3. Commit and push to `main`.

---

### Step 2 — Create a Render Account

1. Go to [https://render.com](https://render.com) and sign up (free).
2. Connect your GitHub account when prompted.

---

### Step 3 — Create a New Web Service

1. On your Render Dashboard, click **"New +"** → **"Web Service"**.
2. Select your GitHub repo (`stock-championship-2026`).
3. Fill in the settings:

| Setting           | Value                                      |
|-------------------|--------------------------------------------|
| **Name**          | `stock-championship-2026` (or any name)    |
| **Runtime**       | `Python 3`                                 |
| **Region**        | Choose nearest to you                      |
| **Branch**        | `main`                                     |
| **Build Command** | `pip install -r requirements.txt`          |
| **Start Command** | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |
| **Instance Type** | `Free`                                     |

4. Click **"Create Web Service"**.

---

### Step 4 — Wait for Deploy

Render will:
1. Clone your repo
2. Install dependencies (`pip install -r requirements.txt`)
3. Start the Streamlit server

This takes ~2–3 minutes. You'll get a live URL like:
```
https://stock-championship-2026.onrender.com
```

---

### Step 5 — Keep It Alive (Optional — Free Tier Caveat)

Free Render services spin down after 15 minutes of inactivity. To prevent this:
- Use a free uptime monitor like [UptimeRobot](https://uptimerobot.com)
- Set it to ping your Render URL every 5 minutes

---

### Notes

- **Data caching**: The app caches Yahoo Finance data for 1 hour using `@st.cache_data(ttl=3600)`. This avoids rate limits and speeds up repeated loads.
- **Missing tickers**: If any ticker is delisted or unavailable (e.g., SNDK post-acquisition), the app assumes 0% return for that $1,000 slice and shows a warning in the sidebar.
- **Competition start**: The app uses `2026-03-01` as the start date. All returns are calculated relative to the first available price on or after that date.
- **Auto-refresh**: Streamlit doesn't auto-refresh by default. Users can manually refresh, or you can add `st_autorefresh` from `streamlit-extras` if desired.

---

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app.py
```

The app will open at `http://localhost:8501`.
