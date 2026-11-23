"""Demo walkthrough: review a PR, post the result to Teams, refresh a token."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.review import CLEAN, review_diff
from src.teams import TeamsCard, TeamsSender
from src.tokens import Token, TokenStore

ROOT = Path(__file__).resolve().parents[1]


def fake_refresh(refresh_token: str) -> dict:
    return {"access_token": "gho_refreshed_token",
            "refresh_token": "ghr_new_refresh_token", "expires_in": 3600}


def main() -> None:
    diff = (ROOT / "data" / "sample_diff.diff").read_text(encoding="utf-8")
    result = review_diff(diff)
    print("Review result:")
    print(result)

    sender = TeamsSender()
    sender.send(TeamsCard(repo="demo/billing-service", pr_number=42,
                          title="Add invoice discount endpoint", result=result))
    print("\nTeams card posted:")
    print(sender.sent[0].text())

    store = TokenStore()
    store.save(Token(access_token="gho_old", refresh_token="ghr_old",
                     expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
                     username="demo-user"))
    token = store.ensure_valid_token("demo-user", fake_refresh)
    print(f"\nToken refreshed before expiry: {token!r}")

    clean = review_diff("def add(a, b):\n    return a + b\n")
    print(f"\nClean diff result: {clean} (== NO_CRITICAL_ISSUES: {clean == CLEAN})")


if __name__ == "__main__":
    main()
