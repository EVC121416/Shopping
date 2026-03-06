from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from typing import Iterator, Optional


class AlertDB:
    def __init__(self, path: str) -> None:
        self.path = path

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_history (
                    product_key TEXT PRIMARY KEY,
                    last_status TEXT NOT NULL,
                    last_alert_price TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def get_last(self, product_key: str) -> tuple[Optional[str], Optional[Decimal]]:
        with self._conn() as conn:
            cur = conn.execute(
                "SELECT last_status, last_alert_price FROM alert_history WHERE product_key = ?",
                (product_key,),
            )
            row = cur.fetchone()
            if not row:
                return None, None
            status, price = row
            return status, (Decimal(price) if price else None)

    def upsert(self, product_key: str, status: str, alert_price: Optional[Decimal]) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO alert_history(product_key, last_status, last_alert_price)
                VALUES(?, ?, ?)
                ON CONFLICT(product_key)
                DO UPDATE SET
                    last_status = excluded.last_status,
                    last_alert_price = excluded.last_alert_price,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (product_key, status, str(alert_price) if alert_price is not None else None),
            )
