import os
import time
from playwright.sync_api import sync_playwright

def main():
    os.makedirs('assets', exist_ok=True)
    
    tabs = [
        'br-stocks',
        'us-stocks',
        'br-fiis',
        'us-reits',
        'b3-indices',
        'market-news'
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        print("Navigating to http://localhost:3000...")
        page.goto('http://localhost:3000')
        
        for tab in tabs:
            print(f"Capturing tab: {tab}")
            # Click the tab
            page.click(f'button[data-tab="{tab}"]')
            
            # Wait for loader to disappear. The loader has id="loader". 
            # We wait for its style to become display: none
            page.wait_for_selector('#loader', state='hidden', timeout=30000)
            
            # Small delay for rendering animations
            time.sleep(1)
            
            # Screenshot
            page.screenshot(path=f'assets/tab_{tab}.png')
            
        print("Capturing settings modal...")
        # Capture settings modal
        page.click('#settings-btn')
        time.sleep(1)
        page.screenshot(path='assets/settings_modal.png')
        
        browser.close()
        print("All screenshots captured successfully!")

if __name__ == "__main__":
    main()
