#!/usr/bin/env python3
"""
Playwright-based debug runner for the Dash frontend mounted under FastAPI.
This is a lightweight MVP to help you inspect assets loading and page
rendering locally.
"""

import os
import sys
import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    print(f"[ERROR] Playwright not installed or could not be imported: {e}")
    sys.exit(2)


def main(url: str = "http://localhost:8000/dash/"):
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path("debug_dash")
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # Headless by default; you can switch to headful for debugging
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logs = []
        def on_console(msg):
            logs.append(f"{msg.type.upper()}: {msg.text}")
        page.on("console", on_console)

        try:
            page.goto(url, wait_until="networkidle")
        except Exception as e:
            logs.append(f"ERROR navigating to {url}: {e}")

        # Save HTML content and a screenshot for quick inspection
        content = page.content()
        with open(out_dir / f"dash_home_{ts}.log", "w", encoding="utf-8") as f:
            f.write(content)
        page.screenshot(path=out_dir / f"dash_home_{ts}.png")

        if logs:
            with open(out_dir / f"dash_console_{ts}.log", "w", encoding="utf-8") as f:
                f.write("\n".join(logs))

        browser.close()
    print(f"Debug dash page written to {out_dir} (content + screenshot).")


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/dash/"
    main(url=url)
