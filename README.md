# GitHub Teams Helper — Demo

A helper that reviews pull-request diffs for critical issues only and posts
the result to Teams, rebuilt from scratch with synthetic data. It also
manages GitHub OAuth tokens, refreshing them before they expire.

This is a personal demo project. It captures the pattern — critical-only
review, chat notification, token lifecycle — without any client code,
client data, or proprietary material.

## The problem

A review bot that comments on everything gets muted. A review bot that
comments only when something would break production gets read. The
discipline is in what it ignores: style, naming, minor improvements, and
missing tests are not its job. Security holes, crash bugs, data loss, and
breaking changes are.

## How it works

```
PR opens
  -> fetch the diff (truncated at 30,000 chars — a review of a truncated
     diff says so, rather than pretending it saw everything)
  -> review for CRITICAL issues only
       - secrets committed in source
       - injection (SQL built from user input)
       - eval()/exec() on untrusted input
       - destructive operations (DROP TABLE, recursive delete)
  -> if none: result is NO_CRITICAL_ISSUES
  -> post the result to Teams as a message card
  -> tokens: GitHub access tokens are refreshed when they are within
     5 minutes of expiring, using the stored refresh token
```

## Run it

```bash
python -m src.run_demo
```

Pure standard library, no dependencies. It reviews the synthetic diff in
`data/sample_diff.diff`, posts the result to a recorded Teams message, and
shows a token refresh.

Run the checks:

```bash
python -m unittest discover -s tests -v
```

## What this proves

- **Critical-only review.** The demo diff contains a hardcoded secret
  (flagged) next to a missing test and a naming nit (ignored). A reviewer
  that reports only the secret earns the next read.
- **Honest truncation.** A diff over the character limit is cut and the
  result says it was cut. Silent truncation is how a critical issue gets
  missed on a large PR.
- **Token lifecycle.** Access tokens are refreshed before expiry, not
  after a 401. The refresh path is tested, including the failure fallback
  (keep the old token and log it, never crash the review).
- **Notification as a record.** The Teams message is a card with the PR,
  the finding count, and the findings. The demo records it instead of
  sending it; the shape is the contract.

## Layout

- `src/review.py` — critical-only diff review + truncation.
- `src/tokens.py` — token store with refresh-before-expiry.
- `src/teams.py` — Teams message card builder + recorded sender.
- `src/run_demo.py` — the demo walkthrough.
- `data/sample_diff.diff` — synthetic diff with one critical issue and
  non-critical noise.
- `docs/design.md` — the full design.
- `tests/` — checks for the review filter, truncation, tokens, and cards.

## What production adds

Real model calls behind the review (the rules here are stand-ins), a web
frontend for configuration, Azure Functions hosting, Table storage for
tokens and state, and Terraform for the infrastructure. None of those are
claimed here — the demo is the review discipline and the token lifecycle,
local only.
