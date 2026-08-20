import re
from datetime import datetime
from decimal import Decimal

CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
KEY_RE = re.compile(r"(?<!\d)(?:\d[ .]?){44}(?!\d)")
DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
TOTAL_RE = re.compile(r"(?:valor\s+total|total)\s*(?:r\$)?\s*([\d.]+,\d{2})", re.IGNORECASE)
CITY_RE = re.compile(
    r"cidade\s*[:=-]\s*([A-Za-zÀ-ÿ .'-]{2,}?)(?=\s+(?:uf|estado)\s*[:=-]|$)",
    re.IGNORECASE,
)
STATE_RE = re.compile(r"(?:uf|estado)\s*[:=-]\s*([A-Z]{2})\b", re.IGNORECASE)


def digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def parse_br_receipt(text: str) -> dict:
    cnpj = CNPJ_RE.search(text)
    key = KEY_RE.search(text)
    date_match = DATE_RE.search(text)
    total = TOTAL_RE.search(text)
    city = CITY_RE.search(text)
    state = STATE_RE.search(text)
    return {
        "merchant_tax_id": digits(cnpj.group()) if cnpj else None,
        "merchant_city": city.group(1).strip() if city else None,
        "merchant_state": state.group(1).upper() if state else None,
        "invoice_key": digits(key.group()) if key else None,
        "expense_date": datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
        if date_match
        else None,
        "amount": Decimal(total.group(1).replace(".", "").replace(",", ".")) if total else None,
    }
