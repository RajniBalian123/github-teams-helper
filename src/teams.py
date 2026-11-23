"""Teams message cards. The demo records cards instead of sending them."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TeamsCard:
    repo: str
    pr_number: int
    title: str
    result: str  # findings text, or NO_CRITICAL_ISSUES

    def text(self) -> str:
        if self.result == "NO_CRITICAL_ISSUES":
            body = "No critical issues found."
        else:
            body = f"Critical issues found:\n{self.result}"
        return (f"PR review: {self.repo}#{self.pr_number} — {self.title}\n"
                f"{body}")


class TeamsSender:
    """Records cards. Production posts them to a Teams webhook."""

    def __init__(self) -> None:
        self.sent: list[TeamsCard] = []

    def send(self, card: TeamsCard) -> None:
        self.sent.append(card)
