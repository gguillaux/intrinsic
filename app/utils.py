import re
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def clean_value(value: str) -> Optional[float]:
    """Clean string value and convert to float."""
    if not value or value == "-" or value == "--":
        return None
    
    try:
        # Remove currency symbols, % and handle thousands separator
        value = value.replace("R$", "").replace("%", "").replace(".", "").replace(",", ".").strip()
        return float(value)
    except ValueError:
        return None
