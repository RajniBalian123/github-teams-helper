# Design: a review helper that only speaks when it matters

Status: demo of the critical-only review pattern, with synthetic diffs. It
does not claim a model, a frontend, hosting, or real Teams delivery.

## 1. The flow

```
PR opens
  -> fetch the diff
  -> truncate at 30,000 chars, and say so if truncated
  -> review for CRITICAL issues only
  -> post the result to Teams
```

## 2. Critical means critical

Flagged:

- Secrets committed in source (API keys, passwords, tokens).
- Injection — SQL or shell built from user input.
- `eval()` / `exec()` on untrusted input.
- Destructive operations — `DROP TABLE`, recursive deletes, mass updates
  without a filter.

Ignored, deliberately:

- Style, naming, formatting.
- Minor improvements and refactors.
- Missing tests.
- Non-critical suggestions.

The ignore list is the product. Every non-critical comment is a small
withdrawal from the team's trust; a bot that comments on everything is a
bot that gets muted, and then the critical finding goes unread too.

## 3. Honest truncation

A diff longer than the limit is cut, and the result says it was cut. A
review that silently reads half a PR and reports "no critical issues" is
worse than no review — it is a false clean bill of health. The truncation
note is part of the result, not a footnote.

## 4. Tokens: refresh before expiry, never after a 401

GitHub access tokens are short-lived. The helper stores the access token,
its expiry, and a refresh token, and refreshes when the token is within
5 minutes of expiring. If the refresh fails, it keeps the old token, logs
the failure, and continues — a failed refresh must not crash a review in
flight. The next request retries the refresh.

## 5. The Teams card is the contract

The notification is a message card: the PR (repo, number, title), the
finding count, and each finding with file and line. The demo records the
card instead of sending it. The card's shape is the interface between the
reviewer and the team — it should be readable in the 5 seconds someone
gives a notification.

## 6. What production adds

- **A model behind the review:** the rules here are stand-ins for a model
  call with a strict prompt (critical issues only, exact
  `NO_CRITICAL_ISSUES` when clean).
- **A frontend:** sign-in, repository selection, and review settings.
- **Hosting and state:** serverless functions, Table storage for tokens
  and review state, infrastructure as code.
- **Retries and backoff:** model and GitHub calls retry with backoff;
  failures are recorded, not swallowed.
