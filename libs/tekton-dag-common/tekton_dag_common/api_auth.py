"""Authentication primitives shared by HTTP control-plane services."""

import hmac


def bearer_token_matches(authorization: str | None, expected_token: str) -> bool:
    """Return whether an Authorization header contains the expected bearer token."""
    if not authorization or not expected_token:
        return False

    scheme, separator, supplied_token = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied_token:
        return False

    return hmac.compare_digest(supplied_token, expected_token)
