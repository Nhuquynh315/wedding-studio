from api.core.security import hash_password, needs_rehash, verify_password


def test_bcrypt_round_trip():
    """Hashing and verifying a new password works."""
    password = "correct horse battery staple"
    hashed = hash_password(password)
    assert hashed.startswith("$2b$"), "bcrypt hashes start with $2b$"
    assert verify_password(password, hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_existing_flask_scrypt_hash_still_verifies():
    """Existing Flask-created users must still be able to log in.

    This hash was created by werkzeug.security.generate_password_hash
    in Flask 3.1 with the password "test-password-12345".
    Do NOT regenerate this hash — it's a fixed test fixture proving
    backward compatibility.
    """
    flask_hash = (
        "scrypt:32768:8:1$wtTEkuNlqqFNhQE9$c7eba9b21682998af78749d881bdafacfad3fb6adb594dfa08d4f651389a077b"
        "91ca935a413479fff21842fcb82195faf6b53d64681f4098e1f3c7dbc45053ad"
    )
    assert verify_password("test-password-12345", flask_hash) is True
    assert verify_password("wrong", flask_hash) is False


def test_malformed_hash_returns_false_not_crash():
    """A garbage hash should fail verification, not crash."""
    assert verify_password("anything", "not-a-real-hash") is False
    assert verify_password("anything", "") is False
    assert verify_password("anything", "$2b$malformed") is False


def test_needs_rehash_flags_legacy_hashes():
    """Legacy werkzeug hashes should be flagged for re-hash on next login."""
    legacy = "scrypt:32768:8:1$abc$def"
    fresh = hash_password("anything")

    assert needs_rehash(legacy) is True
    assert needs_rehash(fresh) is False


def test_legacy_hash_can_be_rehashed_to_bcrypt():
    """Full migration flow: legacy verify succeeds, then re-hash to bcrypt."""
    password = "test-password-12345"
    legacy_hash = (
        "scrypt:32768:8:1$wtTEkuNlqqFNhQE9$c7eba9b21682998af78749d881bdafacfad3fb6adb594dfa08d4f651389a077b"
        "91ca935a413479fff21842fcb82195faf6b53d64681f4098e1f3c7dbc45053ad"
    )

    # Step 1: legacy hash verifies
    assert verify_password(password, legacy_hash) is True
    assert needs_rehash(legacy_hash) is True

    # Step 2: produce a new bcrypt hash for the same password
    new_hash = hash_password(password)

    # Step 3: new hash verifies the same password
    assert verify_password(password, new_hash) is True
    assert needs_rehash(new_hash) is False
