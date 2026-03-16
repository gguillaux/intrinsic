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

1. **Vintage 5-Color UI Theme**
   - Completely transitioned away from the neon/dark theme.
   - Applied a beautiful, vintage 5-color palette: Salmon (`#DC6E55`), Mustard Yellow (`#DAB24F`), Cream (`#E3D4A8`), Sage Green (`#86A59A`), and Dark Slate (`#194146`).
   - Replaced titles with the `Roboto` font for a cleaner, modern aesthetic while preserving monospace for financial data.

2. **Historical News Fetching**
   - Added a `DD/MM/YYYY` Date Picker to the Market News tab.
   - The backend `/news` route was rewritten to accept historical dates, scraping the B3 portal specifically for the requested timeline.

3. **Index Configurations**
   - The B3 Indices tab now acts as a pure configuration screen. Selecting an index (like IFIX) instantly redirects you to the BR Stocks tab, which now correctly queries the backend to display *only* the tickers belonging to that specific index.

## Live Demo & Verification
The application is fully functional. The subagent tested the new Vintage UI, the Date Picker, and the Index routing.

You can see the demonstration of the new Version 2.1 dashboard here:

![V2.1 Vintage UI Demo](file:///home/ggx/.gemini/antigravity/brain/74bd31ec-d161-45ea-97dc-22eb0e5b1dd9/vintage_ui_news_filter_1773630695879.webp)

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
