# Intrinsic Valuation Dashboard - V3 Architecture

Welcome to the **Intrinsic Valuation API & Dashboard (V3)**. This application aggregates, parses, and formats critical fundamental indicators from B3 (Brazilian Stocks/FIIs/News) and US Markets into a high-density, 1980s retro-Bloomberg styled interface.

## 🏗️ Architecture & Component Relationships

The application follows a decoupled architecture, separating the frontend visualization layer from the data-fetching and caching backend.

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#1e1e1e,stroke:#00ff9f,stroke-width:2px,color:#fff
    classDef backend fill:#1e1e1e,stroke:#ffb86c,stroke-width:2px,color:#fff
    classDef db fill:#1e1e1e,stroke:#bd93f9,stroke-width:2px,color:#fff
    classDef api fill:#1e1e1e,stroke:#ff79c6,stroke-width:2px,color:#fff

    %% Components
    subgraph Frontend [UI Layer - Vanilla JS/CSS]
        UI[Retro Bloomberg UI]:::frontend
        Settings[Settings Modal]:::frontend
    end

    subgraph Backend [FastAPI Server]
        API[FastAPI Routes]:::backend
        DataService[Data Service Module]:::backend
        NewsService[News Service Module]:::backend
    end

    subgraph Data Stores [Caching & Persistence]
        DB[(SQLite: data.db)]:::db
        Peewee[Peewee ORM]:::db
        ReqCache[(requests_cache: intrinsic_statusinvest.cache)]:::db
    end

    subgraph External APIs [Data Sources]
        SI(StatusInvest API):::api
        YF(Yahoo Finance - yfinance):::api
        B3(B3 Official News API):::api
    end

    %% Flow
    UI -->|HTTP GET /api/*| API
    Settings -->|HTTP POST /api/cache| API
    API --> DataService
    API --> NewsService

    DataService --> Peewee
    NewsService --> Peewee
    Peewee --> DB

    DataService --> ReqCache
    ReqCache -->|If Miss| SI
    DataService --> YF

    NewsService --> B3
```

## 🔄 External API Consumption & Data Flow

To avoid rate-limiting and ensure ultra-fast load times, the system employs a two-tier caching strategy using `requests_cache` for raw HTTP payloads and a dedicated `SQLite` database for parsed metrics.

```mermaid
sequenceDiagram
    participant User as Frontend UI
    participant Backend as FastAPI Route
    participant Cache as DB (ParsedMetricsCache)
    participant ReqCache as Requests Cache
    participant API as External (StatusInvest/YFinance)

    User->>Backend: Request data for Ticker (e.g., PETR4)
    Backend->>Cache: Check if Parsed Metrics exist & valid
    alt Cache Hit (Valid Data)
        Cache-->>Backend: Return parsed metrics (JSON)
    else Cache Miss / Expired
        Backend->>ReqCache: Request HTML/JSON for Ticker
        alt HTTP Cache Hit
            ReqCache-->>Backend: Return cached HTTP response
        else HTTP Cache Miss
            ReqCache->>API: Fetch raw data over network
            API-->>ReqCache: Return Raw HTML/JSON
            ReqCache-->>Backend: Return & Cache HTTP response
        end
        Backend->>Backend: Parse metrics, compute TTM FCF
        Backend->>Cache: Save Parsed Metrics (data.db)
    end
    Backend-->>User: Return clean dataset
```

## 📸 Core Features & Navigation

### 1. BR Stocks (Ações Brasileiras)
The Brazilian stocks tab cross-references data from StatusInvest and Yahoo Finance. It calculates Free Cash Flow (FCF) dynamically from TTM financial statements and applies a strict ranking algorithm (prioritizing low PEG, low P/FCF, and high ROE).

![BR Stocks](assets/tab_br-stocks.png)

### 2. US Stocks (Ações Americanas)
A dedicated view for the US Market, utilizing the same core fundamentals. It includes an **Anomaly Firewall** that intercepts hyper-inflated anomalies (e.g., Argentine ADRs displaying >1000% ROE) and falls back to reliable bounds.

![US Stocks](assets/tab_us-stocks.png)

### 3. BR FIIs (Fundos Imobiliários)
Specialized tab for Brazilian REITs. It features:
* **Ceiling Price Calculation**: Dynamically computed based on global macroeconomic settings (NTN-B, Spread, Selic).
* **Sharpe Ratio**: Assesses the historical risk-adjusted return of the fund against the Selic rate.
* **Smart Highlighting**: Prices below the calculated Ceiling Price are automatically highlighted in bright green (`#00FF9F`).

![BR FIIs](assets/tab_br-fiis.png)

### 4. US REITs
An overview of US Real Estate Investment Trusts, tracking Dividend Yields, P/VPA, and price actions.

![US REITs](assets/tab_us-reits.png)

### 5. B3 Indices Configuration
Allows users to dynamically set the default composition array for the BR Stocks tab. Selecting `IBOV`, `IFIX`, or `SMLL` triggers backend logic to immediately resolve and inject the precise index ticker makeup.

![B3 Indices](assets/tab_b3-indices.png)

### 6. Market News Feed
Features an advanced regex parsing engine that filters unstructured text directly from the B3 string pipeline. It dynamically extracts over 20+ hidden event classifications (e.g., `DEMONSTRAÇÕES FINANCEIRAS`, `AVISO AOS ACIONISTAS`) and plots them alongside the ticker.

![Market News](assets/tab_market-news.png)

### 7. Global Configuration
A quick-access settings modal allows the user to manually configure the default tickers for each tab, set the Cache Expiration window, and configure macroeconomic variables (NTN-B, Spread, IPCA, Selic) for advanced Intrinsic Valuation formulas.

![Settings Modal](assets/settings_modal.png)

---

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
