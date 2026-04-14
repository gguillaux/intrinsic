# Backlog

## Future Development Items

1. **Replace Mock Index Data**: Integrate a reliable, real-world API or build a robust scraper to replace the mock data currently used in `app/services/index_service.py` for B3 index compositions (IBOV, IFIX, SMLL, IDIV, IBRX).
2. **Dynamic Tickers Endpoint**: Allow users to query and track dynamic lists of stocks/REITs and save them to a user-specific portfolio or database.
3. **Frontend Integration**: Complete the frontend dashboard to display the valuation metrics fetched by the backend in a responsive, modern SPA.
4. **Resilient Scraping**: StatusInvest scraping is prone to blocking; implement better error handling, retries, headers rotation, or migrate to an official financial data API.
5. **Database Enhancements**: Move from SQLite to a more robust database like PostgreSQL, especially if the volume of historical valuation data grows.
6. **Authentication & Authorization**: Implement user accounts (e.g., using JWTs) to secure private portfolios.
7. **Automated Testing**: Introduce `pytest` for unit testing the data service logic and API endpoints.
