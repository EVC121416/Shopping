from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    google_service_account_json: str
    google_sheet_id: str
    worksheet_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: str
    sqlite_path: str
    user_agent: str
    request_timeout_seconds: int



def env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value or ""


def load_settings() -> Settings:
    return Settings(
        google_service_account_json=env("GOOGLE_SERVICE_ACCOUNT_JSON", required=True),
        google_sheet_id=env("GOOGLE_SHEET_ID", required=True),
        worksheet_name=env("GOOGLE_WORKSHEET_NAME", default="Sheet1"),
        smtp_host=env("SMTP_HOST", required=True),
        smtp_port=int(env("SMTP_PORT", default="587")),
        smtp_username=env("SMTP_USERNAME", required=True),
        smtp_password=env("SMTP_PASSWORD", required=True),
        email_from=env("EMAIL_FROM", required=True),
        email_to=env("EMAIL_TO", required=True),
        sqlite_path=env("SQLITE_PATH", default="price_monitor.db"),
        user_agent=env(
            "USER_AGENT",
            default=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
        ),
        request_timeout_seconds=int(env("REQUEST_TIMEOUT_SECONDS", default="20")),
    )
