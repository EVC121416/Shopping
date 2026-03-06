from __future__ import annotations

import smtplib
from dataclasses import dataclass
from decimal import Decimal
from email.message import EmailMessage
from typing import Optional

from price_monitor.db import AlertDB


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    email_from: str
    email_to: str


class AlertService:
    def __init__(self, db: AlertDB, smtp: SmtpConfig) -> None:
        self.db = db
        self.smtp = smtp

    def maybe_send_deal_alert(
        self,
        product_key: str,
        product_name: str,
        store: str,
        url: str,
        price: Decimal,
        status: str,
    ) -> bool:
        previous_status, previous_alert_price = self.db.get_last(product_key)

        should_alert = (
            status == "DEAL"
            and (
                previous_status != "DEAL"
                or previous_alert_price is None
                or price < previous_alert_price
            )
        )

        if should_alert:
            subject = f"Deal Alert: {product_name} now ${price} at {store}"
            body = (
                f"{product_name}\n"
                f"Store: {store}\n"
                f"Price: ${price}\n"
                f"URL: {url}\n"
            )
            self._send_email(subject, body)
            self.db.upsert(product_key, status, price)
            return True

        self.db.upsert(product_key, status, previous_alert_price)
        return False

    def _send_email(self, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.smtp.email_from
        msg["To"] = self.smtp.email_to
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(self.smtp.host, self.smtp.port) as server:
            server.starttls()
            server.login(self.smtp.username, self.smtp.password)
            server.send_message(msg)
