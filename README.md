# Intrinsic Valuation Dashboard - V3 Architecture

Welcome to the **Intrinsic Valuation API & Dashboard (V3)**. This application aggregates, parses, and formats critical fundamental indicators from B3 (Brazilian Stocks/FIIs/News) and US Markets into a high-density, 1980s retro-Bloomberg styled interface.

## 🚀 What's New in V3?

### 1. Robust Quality Assurance (TDD)
- **Pytest Pipeline**: A comprehensive unit testing suite is now deployed under `/tests`. FastApi routes and core calculation algorithms (like the complex TTM P/FCF logic) are strictly tested with Mock arrays to guarantee stability without spamming external APIs.
- **Anomaly Firewalls**: Deployed fail-safes for US equities (ADRs). When hyper-inflated anomalies are reported from base APIs (e.g., Argentine ADRs displaying >1000% ROE), the backend intercepts the response and gracefully falls back to reliable bounds from Yahoo Finance.

### 2. De-monolithication & Cache Stability
- **Decoupled Architecture**: Removed the global HTTP caching monkey-patches that structurally conflicted with Yahoo Finance (`yfinance` error 429). The `data_service.py` functions were split into atomic, testable functions for pure modularity (`_get_statusinvest_data`, `_compute_ttm_fcf`, etc.).
- **Localized Sessions**: HTTP Caching is securely sandboxed to isolated components, allowing aggressive API fetching natively.

### 3. Smart Market Feed Parser
- The `News Feed` module features an advanced regex parsing engine. It normalizes unstructured text directly from the B3 string pipeline by filtering trailing dashes, squashing multi-line line-breaks, and dynamically extracting over 20+ hidden event classifications (`DEMONSTRAÇÕES FINANCEIRAS`, `SUMÁRIO AGE`, `PROPOSTA AGOE`) reliably into independent columns.

### 4. Unified Status Invest Cross-Border API
- Fundaments for Global US Stocks (P/E, Debt/EBIT, ROIC, ROE) are no longer loosely coupled to `yfinance` approximations. The application leverages a unified algorithm fetching precision data exclusively through Native `StatusInvest` Endpoints (`/stock` and `/acao`), guaranteeing perfect data symmetry whether visualizing Apple (`AAPL`) or Petrobras (`PETR4`).

---

## 🎨 Visualization Features

- **Retro Bloomberg UI Theme**: Adaptive Light/Dark modes mapping 5 distinct vintage palettes, rendered purely in CSS + JS native. High-speed array sorting explicitly written for maximum browser performance.
- **Dynamic B3 Index Ticker Integration**: Selecting `IBOV`, `IFIX`, or `SMLL` triggers backend logic to immediately resolve and inject the precise index ticker makeup. 

## ⚡ How to run it locally

We consolidated execution. You no longer need to run multiple terminals.

**Start the Entire Engine (Backend + Frontend):**
```bash
bash start.sh
```
> The API will bind to `localhost:8000` and the web interface will stream on `localhost:3000`. To stop safely, type `CTRL+C`.

## 🧪 Running Automated Tests

To verify the integrity of the data services without making external web calls:
```bash
source venv/bin/activate
pytest -v tests/
```

---
*Developed with focus on Low P/FCF, deep EPS, Low Debt, and optimal Returns on Invested Capital (ROIC).*
