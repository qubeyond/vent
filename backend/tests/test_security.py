from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)


def test_password_hash_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert not verify_password("wrong password", hashed)


def test_password_hash_rejects_foreign_hash_format():
    bcrypt_like_hash = "$2b$12$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWX"
    assert not verify_password("whatever", bcrypt_like_hash)


def test_access_token_roundtrip():
    token = create_access_token(subject="alice")
    assert decode_access_token(token) == "alice"


def test_access_token_rejects_garbage():
    assert decode_access_token("not-a-jwt") is None
