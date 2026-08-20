import re
import unicodedata
from datetime import datetime, time
from decimal import Decimal

BR_AMOUNT_RE = r"(?:\d{1,3}(?:\.\d{3})*|\d+),\d{2}"
CNPJ_LABEL_RE = re.compile(r"(?:cnpj|cpf\s*/\s*cnpj)\D{0,24}([\d\s./-]{14,34})", re.IGNORECASE)
CNPJ_RE = re.compile(r"\b\d{2}[\s.]?\d{3}[\s.]?\d{3}[\s/]?\d{4}[\s-]?\d{2}\b")
KEY_LABEL_RE = re.compile(
    r"(?:chave(?:\s+de\s+acesso)?|consulta\s+pela\s+chave|chave\s+(?:nfe|nfce))"
    r"\D{0,80}((?:\d[\s.:-]?){44})",
    re.IGNORECASE,
)
KEY_RE = re.compile(r"(?<!\d)(?:\d[\s.:-]?){44}(?!\d)")
DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
DATETIME_RE = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\D{0,12}"
    r"(\d{1,2})[:h](\d{2})(?:(?::|h|m)(\d{2}))?\b",
    re.IGNORECASE,
)
TIME_RE = re.compile(r"\b(\d{1,2})[:h](\d{2})(?:(?::|h|m)(\d{2}))?\b", re.IGNORECASE)
LABELED_TOTAL_RE = re.compile(
    rf"(?:valor\s+(?:total(?:\s+da\s+nota)?|a\s+pagar|pago)|total\s+(?:geral|r\$)?|"
    rf"vl\.?\s*total|v\.?\s*total|total\s+dos\s+produtos|total)\D{{0,26}}({BR_AMOUNT_RE})",
    re.IGNORECASE,
)
ANY_AMOUNT_RE = re.compile(rf"(?:r\$\s*)?({BR_AMOUNT_RE})", re.IGNORECASE)
CITY_RE = re.compile(
    r"(?:cidade|municipio|localidade)\s*[:=-]\s*([a-z .'-]{2,}?)"
    r"(?=\s+(?:uf|estado)\s*[:=-]|$)",
    re.IGNORECASE,
)
STATE_RE = re.compile(r"(?:uf|estado)\s*[:=-]\s*([a-z]{2})\b", re.IGNORECASE)
CITY_STATE_RE = re.compile(r"\b([a-z][a-z .'-]{2,})\s*[-/]\s*([a-z]{2})\b", re.IGNORECASE)
MERCHANT_HINTS_RE = re.compile(
    r"(?:ltda|mercado|restaurante|padaria|posto|farmacia|supermercado|"
    r"comercio|loja|hotel|bar|grill|cafe)",
    re.IGNORECASE,
)


def digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def without_accents(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value)
        if unicodedata.category(character) != "Mn"
    )


def normalize_text(text: str) -> str:
    normalized = text.replace("\u00a0", " ")
    normalized = re.sub(r"[|]+", " ", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def searchable_text(text: str) -> str:
    return without_accents(normalize_text(text))


def parse_date(match: re.Match[str] | None):
    if not match:
        return None
    day, month, year = match.group(1), match.group(2), match.group(3)
    if len(year) == 2:
        year = f"20{year}"
    try:
        return datetime(int(year), int(month), int(day)).date()
    except ValueError:
        return None


def parse_datetime_time(match: re.Match[str] | None):
    if not match:
        return None
    try:
        return time(int(match.group(4)), int(match.group(5)), int(match.group(6) or 0))
    except ValueError:
        return None


def parse_time(match: re.Match[str] | None):
    if not match:
        return None
    try:
        return time(int(match.group(1)), int(match.group(2)), int(match.group(3) or 0))
    except ValueError:
        return None


def parse_amount(text: str) -> Decimal | None:
    labeled = list(LABELED_TOTAL_RE.finditer(text))
    amount = labeled[-1].group(1) if labeled else None
    if not amount:
        amounts = [match.group(1) for match in ANY_AMOUNT_RE.finditer(text)]
        amount = amounts[-1] if amounts else None
    return Decimal(amount.replace(".", "").replace(",", ".")) if amount else None


def parse_invoice_key(text: str) -> str | None:
    key = KEY_LABEL_RE.search(text) or KEY_RE.search(text)
    if key:
        candidate = digits(key.group(1) if key.lastindex else key.group())
        if len(candidate) == 44:
            return candidate
    for line in text.splitlines():
        candidate = digits(line)
        if len(candidate) == 44:
            return candidate
    return None


def parse_cnpj(text: str) -> str | None:
    labeled = CNPJ_LABEL_RE.search(text)
    if labeled:
        candidate = digits(labeled.group(1))
        if len(candidate) == 14:
            return candidate
    cnpj = CNPJ_RE.search(text)
    if cnpj:
        candidate = digits(cnpj.group())
        if len(candidate) == 14:
            return candidate
    return None


def parse_city_state(text: str) -> tuple[str | None, str | None]:
    city = CITY_RE.search(text)
    state = STATE_RE.search(text)
    city_value = city.group(1).strip(" -/,.").title() if city else None
    state_value = state.group(1).upper() if state else None
    if city_value and state_value:
        return city_value, state_value

    for line in text.splitlines():
        match = CITY_STATE_RE.search(line.strip())
        if match and not MERCHANT_HINTS_RE.search(match.group(1)):
            return (
                city_value or match.group(1).strip(" -/,.").title(),
                state_value or match.group(2).upper(),
            )
    return city_value, state_value


def parse_br_receipt(text: str) -> dict:
    normalized_text = searchable_text(text)
    datetime_match = DATETIME_RE.search(normalized_text)
    date_match = datetime_match or DATE_RE.search(normalized_text)
    time_value = parse_datetime_time(datetime_match) or parse_time(TIME_RE.search(normalized_text))
    city, state = parse_city_state(normalized_text)
    return {
        "merchant_tax_id": parse_cnpj(normalized_text),
        "merchant_city": city,
        "merchant_state": state,
        "invoice_key": parse_invoice_key(normalized_text),
        "expense_date": parse_date(date_match),
        "expense_time": time_value,
        "amount": parse_amount(normalized_text),
    }
