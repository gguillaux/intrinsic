# Intrinsic Valuation Dashboard - V2 Delivery

I have successfully finished building Phase 2 of the Valuation Web Application (Intrinsic Pro v2.0).

## What's new in V2?
1. **Caching and Rate-Limiting Architecture**
   - Implemented `requests_cache` with a 6-hour TTL backed by an SQLite Database (`data.db`).
   - This ensures the app is genuinely "Low Frequency," bypasses rate limiting from yfinance and B3 APIs, and drastically improves perceived performance.

2. **Database Models for Financial Context**
   - Created a historical `News` table for market events.
   - Created an `IndexComposition` table that overwrites itself with the latest weights.

3. **New API Endpoints & Market Breadth**
   - Added support to filter by **ALL major B3 Indices** (IBOV, IFIX, SMLL, IDIV, IBRX).
   - Added a News endpoint integrating global/market headlines.

4. **1980s Retro Bloomberg Terminal Redesign**
   - Fully transformed the frontend CSS.
   - Features absolute dark mode (#000000), neon amber/green text, monospace fonts, and a subtle CRT scanline overlay.
   - Redesigned the table layouts for highest data density, mimicking professional trader terminals.

## Live Demo & Verification
The application is fully functional. I ran a test subagent that verified the SQLite caching worked, navigated the new Retro index tabs, tested the dropdown filters for `IFIX`, and checked the news feed.

You can see the demonstration of the new Version 2 dashboard here:

![V2 Terminal Dashboard Demo](file:///home/ggx/.gemini/antigravity/brain/74bd31ec-d161-45ea-97dc-22eb0e5b1dd9/retro_terminal_v2_demo_1773628721475.webp)

## How to run it locally
To start the application yourself, you need to start the API and the web server:

**Terminal 1 (Backend):**
```bash
cd ~/repos/intrinsic
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd ~/repos/intrinsic/frontend
python3 -m http.server 3000
```

Then simply open `http://localhost:3000` in your web browser!
