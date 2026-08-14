from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_token_roundtrip():
    hashed = hash_password("uma-senha-segura")
    assert hashed != "uma-senha-segura"
    assert verify_password("uma-senha-segura", hashed)
    assert decode_access_token(create_access_token("user-id")) == "user-id"
