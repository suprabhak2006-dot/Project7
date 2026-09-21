import pytest
from backend.app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token

def test_password_hashing():
    pw = "Investigator@2026!"
    hashed = get_password_hash(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_flow():
    token = create_access_token(subject="42", role="INVESTIGATOR")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "INVESTIGATOR"
