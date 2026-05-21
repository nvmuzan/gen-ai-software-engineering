from __future__ import annotations

import logging
from typing import List, Tuple

from models import Category, ClassificationResult, Priority, Ticket

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    Category.account_access: [
        "login", "password", "sign in", "sign-in", "2fa", "two-factor",
        "authentication", "access denied", "locked out", "account locked",
        "forgot password", "reset password", "can't log", "cannot log",
        "unauthorized", "credentials",
    ],
    Category.technical_issue: [
        "error", "crash", "not working", "broken", "exception", "500",
        "timeout", "slow", "freeze", "hangs", "bug", "glitch", "issue",
        "failure", "failed", "doesn't work", "does not work",
    ],
    Category.billing_question: [
        "invoice", "payment", "charge", "refund", "billing", "subscription",
        "price", "cost", "fee", "credit card", "receipt", "transaction",
        "overcharged", "cancel subscription",
    ],
    Category.feature_request: [
        "feature", "suggestion", "enhancement", "improvement", "request",
        "would be nice", "could you add", "please add", "wish", "idea",
        "propose", "new functionality",
    ],
    Category.bug_report: [
        "reproduce", "steps to reproduce", "expected behavior", "actual behavior",
        "regression", "defect", "reproducible", "version", "environment",
        "stack trace", "log output",
    ],
}

PRIORITY_KEYWORDS: dict[str, list[str]] = {
    Priority.urgent: [
        "can't access", "cannot access", "critical", "production down",
        "security", "data loss", "breach", "urgent", "emergency",
        "system down", "outage", "all users affected",
    ],
    Priority.high: [
        "important", "blocking", "asap", "as soon as possible",
        "high priority", "escalate", "significant impact",
    ],
    Priority.low: [
        "minor", "cosmetic", "suggestion", "nice to have", "low priority",
        "whenever", "no rush", "small",
    ],
}


def _extract_keywords(text: str, keywords: list[str]) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def _classify_category(text: str) -> Tuple[Category, float, List[str]]:
    scores: dict[str, int] = {}
    found_keywords: dict[str, list[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = _extract_keywords(text, keywords)
        scores[category] = len(matched)
        found_keywords[category] = matched

    best = max(scores, key=lambda c: scores[c])
    best_score = scores[best]

    if best_score == 0:
        return Category.other, 0.3, []

    total = sum(scores.values())
    confidence = min(0.95, 0.5 + (best_score / max(total, 1)) * 0.5)
    return Category(best), round(confidence, 2), found_keywords[best]


def _classify_priority(text: str) -> Tuple[Priority, List[str]]:
    for priority in (Priority.urgent, Priority.high, Priority.low):
        matched = _extract_keywords(text, PRIORITY_KEYWORDS[priority])
        if matched:
            return Priority(priority), matched
    return Priority.medium, []


def classify_ticket(ticket: Ticket) -> ClassificationResult:
    combined = f"{ticket.subject} {ticket.description}".lower()

    category, confidence, cat_keywords = _classify_category(combined)
    priority, pri_keywords = _classify_priority(combined)

    all_keywords = list(set(cat_keywords + pri_keywords))

    reasoning_parts = []
    if cat_keywords:
        reasoning_parts.append(f"Category '{category}' matched keywords: {', '.join(cat_keywords)}")
    else:
        reasoning_parts.append("No strong category signal — defaulting to 'other'")
    if pri_keywords:
        reasoning_parts.append(f"Priority '{priority}' matched keywords: {', '.join(pri_keywords)}")
    else:
        reasoning_parts.append("No priority keywords found — defaulting to 'medium'")

    result = ClassificationResult(
        ticket_id=ticket.id,
        category=category,
        priority=priority,
        confidence=confidence,
        reasoning=". ".join(reasoning_parts),
        keywords_found=all_keywords,
    )

    logger.info(
        "Classified ticket %s: category=%s priority=%s confidence=%.2f",
        ticket.id, category, priority, confidence,
    )
    return result
