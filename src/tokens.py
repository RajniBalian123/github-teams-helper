"""GitHub token lifecycle: refresh before expiry, never after a 401."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

REFRESH_WINDOW = timedelta(minutes=5)


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expires_at: datetime
    username: str = ""
    refresh_failures: int = 0


class TokenStore:
    """In-memory token store. Production uses Table storage."""

    def __init__(self) -> None:
        self.tokens: dict[str, Token] = {}

    def save(self, token: Token) -> None:
        self.tokens[token.username] = token

    def get(self, username: str) -> Token | None:
        return self.tokens.get(username)

    def ensure_valid_token(self, username: str, refresh_fn) -> str:
        """Return a usable access token, refreshing when within the window.

        If the refresh fails, keep the old token and record the failure —
        a failed refresh must not crash a review in flight.
        """
        token = self.tokens[username]
        now = datetime.now(timezone.utc)
        if now > token.expires_at - REFRESH_WINDOW:
            try:
                new = refresh_fn(token.refresh_token)
                token.access_token = new["access_token"]
                token.expires_at = now + timedelta(seconds=new["expires_in"])
                if new.get("refresh_token"):
                    token.refresh_token = new["refresh_token"]
                token.refresh_failures = 0
            except Exception:
                token.refresh_failures += 1
        return token.access_token
