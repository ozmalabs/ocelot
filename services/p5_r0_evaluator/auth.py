from __future__ import annotations

from .interfaces import Principal, TokenVerifier


class AuthError(PermissionError):
    pass


class StaticTokenVerifier(TokenVerifier):
    """Test-only verifier. Production must use Google signed OIDC tokens."""
    def __init__(self, tokens: dict[str, Principal]):
        self.tokens = dict(tokens)

    def verify(self, authorization: str | None) -> Principal:
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise AuthError("missing bearer token")
        token = authorization[7:]
        if not token or token not in self.tokens:
            raise AuthError("invalid identity token")
        return self.tokens[token]


class GoogleOIDCVerifier(TokenVerifier):
    def __init__(self, audience: str, allowed_subjects: set[str]):
        if not audience or not allowed_subjects:
            raise ValueError("OIDC audience and allowlist are required")
        self.audience = audience
        self.allowed_subjects = set(allowed_subjects)

    def verify(self, authorization: str | None) -> Principal:
        if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
            raise AuthError("missing bearer token")
        token = authorization[7:]
        if not token:
            raise AuthError("invalid identity token")
        try:
            from google.auth.transport import requests
            from google.oauth2 import id_token
            claims = id_token.verify_oauth2_token(token, requests.Request(), self.audience)
            subject = claims.get("sub")
            email = claims.get("email")
        except Exception as exc:
            raise AuthError("invalid identity token") from exc
        if not isinstance(subject, str) or subject not in self.allowed_subjects:
            raise AuthError("principal is not authorized")
        return Principal(subject=subject, email=email if isinstance(email, str) else None)
