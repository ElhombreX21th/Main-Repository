from datetime import date, time
from decimal import Decimal

from app.parsers.br_receipt import parse_br_receipt


def test_parse_brazilian_receipt():
    text = (
        "CNPJ 12.345.678/0001-90 Emissão 14/08/2026 CIDADE: São Paulo UF: SP "
        "TOTAL R$ 1.234,56 "
        "Chave 12345678901234567890123456789012345678901234"
    )
    result = parse_br_receipt(text)
    assert result == {
        "merchant_tax_id": "12345678000190",
        "merchant_city": "Sao Paulo",
        "merchant_state": "SP",
        "invoice_key": "12345678901234567890123456789012345678901234",
        "expense_date": date(2026, 8, 14),
        "expense_time": None,
        "amount": Decimal("1234.56"),
    }


def test_parse_receipt_with_datetime_and_nfce_key():
    text = """
    NFC-e
    EMPRESA EXEMPLO LTDA
    CNPJ: 12 345 678 0001 90
    Data de Emissão: 20/08/2026 14:35:09
    Valor a pagar R$ 61,11
    Chave de acesso
    3526 0812 3456 7800 0190 6500 1000 0012 3410 0001 2345
    Município: Rio de Janeiro UF: RJ
    """
    result = parse_br_receipt(text)
    assert result == {
        "merchant_tax_id": "12345678000190",
        "merchant_city": "Rio De Janeiro",
        "merchant_state": "RJ",
        "invoice_key": "35260812345678000190650010000012341000012345",
        "expense_date": date(2026, 8, 20),
        "expense_time": time(14, 35, 9),
        "amount": Decimal("61.11"),
    }


def test_parser_accepts_partial_text():
    result = parse_br_receipt("comprovante ilegível")
    assert result["amount"] is None
    assert result["merchant_city"] is None
    assert result["expense_time"] is None
