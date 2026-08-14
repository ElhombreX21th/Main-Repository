from datetime import date
from decimal import Decimal

from app.parsers.br_receipt import parse_br_receipt


def test_parse_brazilian_receipt():
    text = (
        "CNPJ 12.345.678/0001-90 Emissão 14/08/2026 TOTAL R$ 1.234,56 "
        "Chave 12345678901234567890123456789012345678901234"
    )
    result = parse_br_receipt(text)
    assert result == {
        "merchant_tax_id": "12345678000190",
        "invoice_key": "12345678901234567890123456789012345678901234",
        "expense_date": date(2026, 8, 14),
        "amount": Decimal("1234.56"),
    }


def test_parser_accepts_partial_text():
    assert parse_br_receipt("comprovante ilegível")["amount"] is None
