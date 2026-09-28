"""API-key hashing and verification for the HTTP endpoint."""

from __future__ import annotations

import hashlib
import hmac


def hash_api_key(api_key: str) -> str:
    """Return the SHA-256 hex digest of an API key.

    Run this once locally to generate the value for NOTIFY_API_KEY_HASH:

        python -c "import hashlib; print(hashlib.sha256(b'super-secret').hexdigest())"
    """
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(provided_key: str | None, expected_hash: str) -> bool:
    """Compare a provided API key against the expected SHA-256 hex digest."""
    if not provided_key or not expected_hash:
        return False
    candidate = hash_api_key(provided_key)
    return hmac.compare_digest(candidate.lower(), expected_hash.strip().lower())
