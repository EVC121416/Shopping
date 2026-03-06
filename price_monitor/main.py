from __future__ import annotations

import logging
from decimal import Decimal

from price_monitor.alerts import AlertService, SmtpConfig
from price_monitor.config import load_settings
from price_monitor.db import AlertDB
from price_monitor.matcher import evaluate_listing
from price_monitor.scraper import PriceScraper, parse_comparison_stores
from price_monitor.sheets import ProductRow, SheetsClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def as_decimal(raw: object) -> Decimal | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def decide_status(
    main_price: Decimal | None,
    best_comp_price: Decimal | None,
    main_threshold: Decimal | None,
    comp_threshold: Decimal | None,
    manual_check: bool,
    errored: bool,
) -> str:
    if errored:
        return "ERROR"
    if manual_check:
        return "CHECK MANUALLY"
    if main_price is not None and main_threshold is not None and main_price <= main_threshold:
        return "DEAL"
    if best_comp_price is not None and comp_threshold is not None and best_comp_price <= comp_threshold:
        return "DEAL"
    return "WAIT"


def process_row(
    row: ProductRow,
    scraper: PriceScraper,
    sheets: SheetsClient,
    alerts: AlertService,
) -> None:
    v = row.values
    product_name = str(v.get("Product Name", "")).strip()
    brand = str(v.get("Brand", "")).strip()
    model = str(v.get("Model", "")).strip()
    variant = str(v.get("Variant", "")).strip()
    main_store = str(v.get("Main Store", "")).strip()
    main_url = str(v.get("Main URL", "")).strip()
    excluded = str(v.get("Excluded Keywords", "")).strip()

    main_threshold = as_decimal(v.get("Main Threshold"))
    comp_threshold = as_decimal(v.get("Comparison Threshold"))

    manual_check = False
    errored = False
    notes: list[str] = []

    current_main_price = None
    best_comp_price = None
    best_comp_store = ""

    try:
        main_listing = scraper.fetch_listing(main_store, main_url)
        main_decision = evaluate_listing(main_listing, product_name, brand, model, variant, excluded)
        if main_decision.accepted:
            current_main_price = main_listing.price
        else:
            manual_check = True
            notes.append(f"Main: {main_decision.reason}")

        for comp_store, comp_url in parse_comparison_stores(str(v.get("Comparison Stores", ""))):
            try:
                listing = scraper.fetch_listing(comp_store, comp_url)
                decision = evaluate_listing(listing, product_name, brand, model, variant, excluded)
                if not decision.accepted:
                    notes.append(f"{comp_store}: {decision.reason}")
                    continue
                if listing.price is not None and (
                    best_comp_price is None or listing.price < best_comp_price
                ):
                    best_comp_price = listing.price
                    best_comp_store = comp_store
            except Exception as exc:
                notes.append(f"{comp_store}: scrape error: {exc}")
    except Exception as exc:
        errored = True
        notes.append(f"Main scrape error: {exc}")

    status = decide_status(
        current_main_price,
        best_comp_price,
        main_threshold,
        comp_threshold,
        manual_check,
        errored,
    )

    sheets.update_result(
        product=row,
        current_main_price=current_main_price,
        best_comparison_price=best_comp_price,
        best_comparison_store=best_comp_store,
        status=status,
        notes=" | ".join(notes)[:400],
    )

    if status == "DEAL":
        deal_store = best_comp_store if best_comp_price is not None and comp_threshold and best_comp_price <= comp_threshold else main_store
        deal_url = main_url
        deal_price = best_comp_price if deal_store == best_comp_store and best_comp_price is not None else current_main_price
        if deal_price is not None:
            sent = alerts.maybe_send_deal_alert(
                product_key=row.product_key,
                product_name=product_name,
                store=deal_store,
                url=deal_url,
                price=deal_price,
                status=status,
            )
            if sent:
                logger.info("Sent deal alert for %s", product_name)


def run() -> None:
    settings = load_settings()

    sheets = SheetsClient(
        service_account_json=settings.google_service_account_json,
        sheet_id=settings.google_sheet_id,
        worksheet_name=settings.worksheet_name,
    )
    scraper = PriceScraper(settings.user_agent, settings.request_timeout_seconds)

    db = AlertDB(settings.sqlite_path)
    db.init()
    alerts = AlertService(
        db,
        SmtpConfig(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            email_from=settings.email_from,
            email_to=settings.email_to,
        ),
    )

    for row in sheets.get_active_products():
        logger.info("Checking %s", row.values.get("Product Name"))
        process_row(row, scraper, sheets, alerts)


if __name__ == "__main__":
    run()
