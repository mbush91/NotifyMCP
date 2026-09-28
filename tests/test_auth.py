import hashlib

from notifymcp.auth import hash_api_key, verify_api_key


def test_hash_api_key_matches_sha256():
    assert hash_api_key("super-secret") == hashlib.sha256(b"super-secret").hexdigest()


def test_verify_api_key_ok_and_failures():
    expected = hash_api_key("correct-key")
    assert verify_api_key("correct-key", expected) is True
    assert verify_api_key("wrong-key", expected) is False
    assert verify_api_key(None, expected) is False
    assert verify_api_key("", expected) is False
    assert verify_api_key("correct-key", "") is False


def test_verify_api_key_hash_case_insensitive():
    expected = hash_api_key("abc").upper()
    assert verify_api_key("abc", expected) is True
