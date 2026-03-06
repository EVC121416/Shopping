from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

import requests
from bs4 import BeautifulSoup

PRICE_PATTERN = re.compile(r"(?:\$|USD\s*)(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")


@dataclass
class ScrapeResult:
    store: str
    url: str
    title: str
    text: str
    price: Optional[Decimal]
    confidence: float


class PriceScraper:
    def __init__(self, user_agent: str, timeout_seconds: int = 20) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.timeout_seconds = timeout_seconds

    def fetch_listing(self, store: str, url: str) -> ScrapeResult:
        response = self.session.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        text = soup.get_text(" ", strip=True)

        price = self._extract_price(response.text, text)
        confidence = 0.8 if price is not None else 0.1
        return ScrapeResult(store=store, url=url, title=title, text=text, price=price, confidence=confidence)

    def _extract_price(self, html: str, text: str) -> Optional[Decimal]:
        for source in (html, text):
            match = PRICE_PATTERN.search(source)
            if not match:
                continue
            raw = match.group(1).replace(",", "")
            try:
                return Decimal(raw)
            except InvalidOperation:
                continue
        return None


def parse_comparison_stores(raw: str) -> list[tuple[str, str]]:
    """Expected format: StoreA|https://url-a;StoreB|https://url-b"""
    if not raw:
        return []
    pairs: list[tuple[str, str]] = []
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "|" not in chunk:
            continue
        store, url = chunk.split("|", 1)
        pairs.append((store.strip(), url.strip()))
    return pairs
