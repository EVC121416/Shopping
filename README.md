# Python Price Monitor (Google Sheets Dashboard)

Simple price-monitoring script that uses **Google Sheets as the dashboard/source of truth**.

## What it does

- Reads active products from your Google Sheet.
- Checks price from the main store URL.
- Optionally checks comparison stores.
- Uses product matching rules (brand/model/variant + excluded keywords).
- Rejects used/refurbished/open-box listings.
- Writes results back to the same sheet.
- Sends an email when status newly becomes `DEAL` (or price improves).
- Uses SQLite to prevent duplicate alerts.

## Sheet columns (required)

The worksheet must include this exact header row:

1. Active
2. Product Name
3. Brand
4. Model
5. Variant
6. Main Store
7. Main URL
8. Main Threshold
9. Comparison Stores
10. Comparison Threshold
11. Reference Price
12. Excluded Keywords
13. Current Main Price
14. Best Comparison Price
15. Best Comparison Store
16. Last Checked
17. Status
18. Notes

## Comparison Stores format

Use this format in `Comparison Stores`:

```text
Walmart|https://example.com/p1;BestBuy|https://example.com/p2
```

## Setup

### 1) Create and share Google Sheet

- Create the sheet + worksheet.
- Share the sheet with your Google service-account email.

### 2) Google API credentials

- Create a Google Cloud service account.
- Enable Google Sheets API.
- Download service account JSON key.

### 3) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Environment variables

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
export GOOGLE_SHEET_ID=your_sheet_id
export GOOGLE_WORKSHEET_NAME=Sheet1

export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=you@example.com
export SMTP_PASSWORD=app-password-or-smtp-password
export EMAIL_FROM=you@example.com
export EMAIL_TO=you@example.com

export SQLITE_PATH=price_monitor.db
export REQUEST_TIMEOUT_SECONDS=20
```

### 5) Run

```bash
python main.py
```

## Example item

| Active | Product Name | Brand | Model | Variant | Main Store | Main URL | Main Threshold | Comparison Stores | Comparison Threshold | Excluded Keywords |
|---|---|---|---|---|---|---|---:|---|---:|---|
| TRUE | Shark StainForce Portable Cordless Spot & Stain Cleaner | Shark | HX101 | Gray | Target | https://www.target.com/... | 150 | Walmart\|https://www.walmart.com/...;BestBuy\|https://www.bestbuy.com/... | 150 | HX100, used, refurbished, open box |

## Status rules

- `DEAL`: main price <= main threshold OR best comparison <= comparison threshold
- `WAIT`: checked and no threshold met
- `CHECK MANUALLY`: low-confidence product match
- `ERROR`: technical issue (request/parsing/etc)

## Notes on scraping

This starter uses lightweight HTML scraping and regex price extraction.
For some stores, anti-bot pages or dynamic rendering may require store-specific parsers later.

## Run daily with GitHub Actions

A workflow is included: `.github/workflows/daily-price-monitor.yml`

### Required GitHub Secrets

- `GOOGLE_SERVICE_ACCOUNT_JSON_B64` (base64-encoded service account JSON)
- `GOOGLE_SHEET_ID`
- `GOOGLE_WORKSHEET_NAME`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`
- (optional) `SQLITE_PATH`

Create base64 value locally:

```bash
base64 -w0 /path/to/service-account.json
```

Then paste output into `GOOGLE_SERVICE_ACCOUNT_JSON_B64` secret.

The workflow runs daily and also supports manual dispatch.
