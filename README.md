# Intrinsic Valuation Dashboard - Delivery

I have successfully finished building the Valuation Web Application based on the "Modern Full-Stack" architecture. 

## What was built
We created a robust backend APIs to fetch and calculate financial metrics from yfinance, and a sleek, dynamic frontend dashboard to visualize them.

1. **Python FastAPI Backend**
   - Endpoints: `/stocks/br`, `/stocks/us`, `/fiis/br`, `/reits/us`
   - Handles parallel asynchronous data fetching using `yfinance` to bypass rate limits and speed up table rendering.
   - Extracts exact metrics needed for Valuation: FCF, EPS, Debt, P/E, PEG Ratio, Dividend Yield, and P/VPA.
2. **Modern Frontend**
   - Built with Vanilla HTML/JS/CSS for maximum performance without build steps.
   - Features a premium Dark Mode aesthetic using glassmorphism and subtle animations.
   - Includes real-time search filtering.
   - Automatically highlights "Good" metrics in Cyan and "Bad" metrics in Red based on standard valuation rules (e.g., PEG < 1 is good, Debt > X is bad).

## Live Demo & Verification
The application is fully functional. I ran a Browser Agent that successfully connected to the frontend, verified the API was answering, and tested the tab switching and search functionality successfully.

You can see the demonstration of the interactive dashboard here:

![Dashboard Recording](file:///home/ggx/.gemini/antigravity/brain/74bd31ec-d161-45ea-97dc-22eb0e5b1dd9/valuation_dashboard_demo_1773627577894.webp)

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
