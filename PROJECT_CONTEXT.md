# Intrinsic Project Context & Architecture State

**Last Updated:** 2026-09-08
**Test Suite Status:** 32 / 32 tests passing (`venv/bin/python -m pytest tests/ -v`)

---

## 1. Executive Summary & Purpose

Intrinsic is a financial analysis and valuation web dashboard for Brazilian & US Equities (Stocks and REITs/FIIs), tracking B3 indices and market announcements.

---

## 2. Architecture & Design Patterns Implemented

### 2.1 Strategy Pattern for Metrics Providers (`app/providers/`)
Data fetching was previously tangled inside `app/services/data_service.py` with hardcoded calls to StatusInvest and yfinance. Now, it follows the **Strategy Design Pattern**:
- **`app/providers/base.py` (`MetricsProvider`)**: Abstract Base Class defining the interface:
  - `name: str`
  - `priority: int` (Lower values execute first)
  - `fetch_stock(ticker: str, data: dict, **kwargs)`
  - `fetch_reit(ticker: str, data: dict, **kwargs)`
- **`app/providers/yfinance_provider.py` (`YFinanceProvider`, priority 10)**: Primary data provider. Fetches prices, company info, balance sheet data (Assets, NWC), TTM P/FCF, and full fundamental metrics (`trailingPE`, `trailingEps`, `pegRatio`, `dividendYield`, `priceToBook`, `totalDebt/ebitda`, `returnOnEquity`, `returnOnAssets`, `profitMargins`).
- **`app/providers/statusinvest_provider.py` (`StatusInvestProvider`, priority 20)**: Secondary/override provider. Gracefully handles Cloudflare blocks without crashing, provides anomaly filtering (Argentine ADRs), and scrapes extra FII metrics (`dy_cagr`, `val_cagr`, `caixa`, `cotistas`).
- **Extensibility**: Third-party providers (e.g. AlphaVantage, Finnhub) can be registered via `register_provider(provider)`.

### 2.2 Domain Dataclass (`app/domain/models.py`)
- **`StockMetrics`**: Typed dataclass representing all stock and REIT financial metrics, with `to_dict()` and `from_dict()` serialization helpers for type safety and clean schema validation.

### 2.3 Concurrency & Performance Optimization
- **`app/api/routes.py`**: Replaced unbounded thread allocation (`loop.run_in_executor(None, ...)`) with a dedicated `ThreadPoolExecutor(max_workers=10)` governed by an `asyncio.Semaphore(10)`. Prevents threadpool exhaustion when fetching 70+ index tickers.
- **`app/main.py`**: Startup index/news fetching moved to asynchronous non-blocking background tasks (`asyncio.create_task(_startup_data_fetch())`). The server starts immediately and binds to port 8000 without waiting for external web scrapers.

### 2.4 Frontend Refactoring (`frontend/app.js`)
- **Eliminated Duplicate Ranking Calculation**: Deleted duplicate 60-line `calculateRanking()` function on the frontend. The backend calculations (`app/domain/calculations.py`) are now the single source of truth for `rank_score` and `final_rank`.
- **Active News Filtering**: Wired up `currentNewsType` in `getFilteredData()` matching against `parsedType`.
- **Search & Filter Debouncing**: Added a `debounce(fn, ms)` utility applied with 300ms delay to ticker searches and column header filters, preventing layout thrashing and unnecessary table re-renders.
- **Network Race Condition Protection**: Introduced `AbortController` in `loadTabData()` canceling prior in-flight tab requests when the user rapidly switches tabs.
- **Theme Persistence**: Dark/light mode state is stored in `localStorage.getItem('theme')` and preserved across reloads.
- **Dynamic Table Colspan**: Error row rendering dynamically computes column count according to tab configuration (5 to 17 columns) rather than hardcoding `colspan="10"`.
- **Internationalization & Currency**: `formatCurrency` uses `pt-BR` / `BRL` for Brazilian equities/FIIs and `en-US` / `USD` for US assets.
- **Defensive Type Formatting**: `formatPercent` safely validates `typeof val === 'number'` before calling `.toFixed()`.
- **Safe Grid Dismissal**: `excludeFromGrid` only mutates `localStorage` if the user was already in manual ticker mode, preventing unintended overrides of active index selections.

---

## 3. Directory Layout

```
intrinsic/
├── app/
│   ├── api/
│   │   └── routes.py           # FastAPI routes, bounded thread execution
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── calculations.py     # Pure financial math & ranking algorithms
│   │   └── models.py           # StockMetrics dataclass
│   ├── providers/              # Strategy pattern providers
│   │   ├── __init__.py
│   │   ├── base.py             # MetricsProvider ABC
│   │   ├── statusinvest_provider.py
│   │   └── yfinance_provider.py
│   ├── services/
│   │   ├── data_service.py     # Orchestrator & SQLite caching
│   │   ├── index_service.py    # B3 index compositions
│   │   └── news_service.py     # B3 news aggregation
│   ├── config.py               # Constants, timeouts, header configs
│   ├── database.py             # Peewee SQLite connection
│   ├── main.py                 # FastAPI application and lifespan hooks
│   └── models.py               # Database ORM models (News, Cache, Index)
├── frontend/
│   ├── app.js                  # Frontend dashboard logic
│   ├── index.html              # HTML structure
│   └── index.css               # Theme and layout styles
├── tests/
│   ├── test_api_routes.py
│   ├── test_calculations.py
│   ├── test_data_service.py
│   ├── test_domain_models.py
│   └── test_providers.py
├── PROJECT_CONTEXT.md          # THIS FILE (State handoff for AI models)
└── start.sh                    # Dual-process launcher (backend 8000, frontend 3000)
```

---

## 4. Running and Testing

```bash
# Run all unit tests:
venv/bin/python -m pytest tests/ -v

# Launch backend and frontend:
./start.sh
```

---

## 5. Next Planned Roadmap Items (If Session Resets)

1. **Modularize `frontend/app.js` into ES Modules**:
   Split the 1,500-line closure into `frontend/js/api.js`, `state.js`, `table.js`, `grid.js`, and `utils.js` using native `<script type="module">`.
2. **Batch Quotes via `yf.download`**:
   For large indices (IBOV with 70+ tickers), query prices in batch to reduce HTTP roundtrips.
3. **Database Concurrency Protection**:
   Wrap multi-threaded cache writes in a write queue or connection pool to prevent SQLite `database is locked` warnings under burst requests.
