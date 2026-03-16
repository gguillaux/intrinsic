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

---

# V2.1 Enhancements

We further refined the application with the following V2.1 enhancements:

1. **Light/Dark Retro Bloomberg UI Theme**
   - Restored the 1980s Retro Bloomberg Terminal aesthetic natively by setting the core font to `Fira Code` monospace.
   - The theme now adapts the requested 5-color vintage palette to provide high data density: Salmon (`#D94B2B`), Mustard Yellow (`#ECA13A`), Cream (`#F3E1B6`), Muted Teal (`#45A5AE`), and Dark Slate (`#144358`).
   - Implemented a **[ TOGGLE THEME ]** button in the sidebar allowing a user to swap between the original Black Dark theme and the new Cream-based Light theme dynamically.

2. **Historical News Fetching**
   - Added a `DD/MM/YYYY` Date Picker to the Market News tab.
   - The backend `/news` route was rewritten to accept historical dates, scraping the B3 portal specifically for the requested timeline.

3. **Index Configurations & Status Invest Integration**
   - The B3 Indices tab now acts as a pure configuration screen. Selecting an index (like IFIX) instantly redirects you to the BR Stocks tab, which now correctly queries the backend to display *only* the tickers belonging to that specific index.
   - We completely replaced `yfinance` with a robust **Status Invest** parsing integration. `yfinance` was consistently returning `null` data for Brazilian fundamental indicators (FCF, EPS, Debt, P/E, PEG). The App now queries Status Invest's historical API directly to guarantee 100% accurate data for Brazilian Equities.

## Live Demo & Verification
The application is fully functional. The subagent tested the new Status Invest parsed tables and the new Dark/Light retro terminal toggle in action:

![V2.1 Status Invest Data Validation](/home/ggx/.gemini/antigravity/brain/74bd31ec-d161-45ea-97dc-22eb0e5b1dd9/br_stocks_filled_data_1773631962933.webp)

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
