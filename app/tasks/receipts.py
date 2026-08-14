from app.parsers import parse_br_receipt
from app.worker import celery_app


@celery_app.task(name="receipts.parse_br")
def parse_br_receipt_task(text: str) -> dict:
    result = parse_br_receipt(text)
    return {key: str(value) if value is not None else None for key, value in result.items()}
