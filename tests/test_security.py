import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.entities import ExpenseStatus
from app.schemas.expense import ReceiptText
from app.services.expenses import transition


def test_password_hash_and_token_roundtrip():
    hashed = hash_password("uma-senha-segura")
    assert hashed != "uma-senha-segura"
    assert verify_password("uma-senha-segura", hashed)
    assert decode_access_token(create_access_token("user-id")) == "user-id"


def test_known_or_short_secrets_are_rejected():
    with pytest.raises(ValidationError):
        Settings(secret_key="development-secret-change-in-production")
    with pytest.raises(ValidationError):
        Settings(secret_key="short")


def test_access_token_rejects_missing_context_claims():
    from app.core.security import settings

    token = jwt.encode(
        {"sub": "user-id", "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_invalid_password_hash_is_a_safe_authentication_failure():
    assert not verify_password("password", "not-a-valid-password-hash")


def test_receipt_text_size_is_bounded():
    with pytest.raises(ValidationError):
        ReceiptText(text="x" * 100_001)


def test_user_cannot_approve_their_own_expense():
    owner_id = uuid.uuid4()
    actor = SimpleNamespace(id=owner_id)
    expense = SimpleNamespace(user_id=owner_id, status=ExpenseStatus.submitted)

    with pytest.raises(HTTPException) as error:
        transition(SimpleNamespace(), actor, expense, "approve")
    assert error.value.status_code == 403
