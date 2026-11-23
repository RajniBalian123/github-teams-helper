"""Checks for critical-only review, truncation, tokens, and cards."""

import unittest
from datetime import datetime, timedelta, timezone

from src.review import CLEAN, MAX_DIFF_CHARS, review_diff
from src.teams import TeamsCard, TeamsSender
from src.tokens import Token, TokenStore


class TestReview(unittest.TestCase):
    def test_critical_issues_found(self):
        diff = ('API_KEY = "sk-live-12345678"\n'
                'query = f"SELECT * FROM t WHERE id = \'{x}\'"\n')
        result = review_diff(diff)
        self.assertIn("hardcoded secret", result)
        self.assertIn("SQL built with string interpolation", result)

    def test_non_critical_ignored(self):
        diff = ("# TODO: add a test\n"
                "# NOTE: rename this variable\n"
                "def add(a, b):\n    return a + b\n")
        self.assertEqual(review_diff(diff), CLEAN)

    def test_clean_diff(self):
        self.assertEqual(review_diff("def add(a, b):\n    return a + b\n"), CLEAN)

    def test_truncation_is_disclosed(self):
        diff = "x = 1\n" * 10000  # far over the limit
        result = review_diff(diff + 'API_KEY = "sk-live-12345678"\n')
        self.assertIn("truncated", result)
        # the secret is past the cut, so the review must not claim full coverage
        self.assertNotIn("hardcoded secret", result)

    def test_destructive_operation_flagged(self):
        self.assertIn("destructive",
                      review_diff("cursor.execute('DROP TABLE invoices')"))


class TestTokens(unittest.TestCase):
    def test_refresh_before_expiry(self):
        store = TokenStore()
        store.save(Token(access_token="old", refresh_token="r",
                         expires_at=datetime.now(timezone.utc) + timedelta(minutes=3),
                         username="u"))
        token = store.ensure_valid_token(
            "u", lambda rt: {"access_token": "new", "expires_in": 3600})
        self.assertEqual(token, "new")

    def test_no_refresh_when_plenty_of_time(self):
        store = TokenStore()
        store.save(Token(access_token="old", refresh_token="r",
                         expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
                         username="u"))
        calls = []
        token = store.ensure_valid_token(
            "u", lambda rt: calls.append(rt) or {"access_token": "new", "expires_in": 3600})
        self.assertEqual(token, "old")
        self.assertEqual(calls, [])

    def test_failed_refresh_keeps_old_token(self):
        store = TokenStore()
        store.save(Token(access_token="old", refresh_token="r",
                         expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
                         username="u"))
        def boom(rt):
            raise RuntimeError("refresh endpoint down")
        token = store.ensure_valid_token("u", boom)
        self.assertEqual(token, "old")
        self.assertEqual(store.get("u").refresh_failures, 1)


class TestTeams(unittest.TestCase):
    def test_card_content(self):
        sender = TeamsSender()
        sender.send(TeamsCard(repo="demo/app", pr_number=7, title="Fix bug",
                              result=CLEAN))
        self.assertIn("No critical issues", sender.sent[0].text())
        self.assertIn("demo/app#7", sender.sent[0].text())


if __name__ == "__main__":
    unittest.main()
