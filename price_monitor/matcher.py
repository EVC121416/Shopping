from __future__ import annotations

from dataclasses import dataclass

from price_monitor.scraper import ScrapeResult

BLOCKED_TERMS = {"used", "refurbished", "open box", "open-box"}


@dataclass
class MatchDecision:
    accepted: bool
    reason: str


def _tokenize_excluded(raw: str) -> set[str]:
    return {t.strip().lower() for t in raw.split(",") if t.strip()}


def evaluate_listing(
    listing: ScrapeResult,
    product_name: str,
    brand: str,
    model: str,
    variant: str,
    excluded_keywords: str,
) -> MatchDecision:
    haystack = f"{listing.title} {listing.text}".lower()

    for term in BLOCKED_TERMS.union(_tokenize_excluded(excluded_keywords)):
        if term in haystack:
            return MatchDecision(False, f"Excluded term detected: {term}")

    if model and model.lower() not in haystack:
        return MatchDecision(False, f"Model not found exactly: {model}")

    required_clues = [c for c in [product_name, brand, variant] if c]
    matches = sum(1 for clue in required_clues if clue.lower() in haystack)
    if required_clues and matches < max(1, len(required_clues) - 1):
        return MatchDecision(False, "Low confidence match")

    if listing.price is None:
        return MatchDecision(False, "Price not found")

    return MatchDecision(True, "Matched")
