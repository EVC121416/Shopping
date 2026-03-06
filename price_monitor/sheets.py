from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

import gspread
from gspread.worksheet import Worksheet


HEADERS = [
    "Active",
    "Product Name",
    "Brand",
    "Model",
    "Variant",
    "Main Store",
    "Main URL",
    "Main Threshold",
    "Comparison Stores",
    "Comparison Threshold",
    "Reference Price",
    "Excluded Keywords",
    "Current Main Price",
    "Best Comparison Price",
    "Best Comparison Store",
    "Last Checked",
    "Status",
    "Notes",
]


@dataclass
class ProductRow:
    row_number: int
    values: dict[str, Any]

    @property
    def product_key(self) -> str:
        name = str(self.values.get("Product Name", "")).strip().lower()
        model = str(self.values.get("Model", "")).strip().lower()
        return f"{name}::{model}"


class SheetsClient:
    def __init__(self, service_account_json: str, sheet_id: str, worksheet_name: str) -> None:
        gc = gspread.service_account(filename=service_account_json)
        spreadsheet = gc.open_by_key(sheet_id)
        self.worksheet: Worksheet = spreadsheet.worksheet(worksheet_name)

    def get_active_products(self) -> list[ProductRow]:
        rows = self.worksheet.get_all_records(expected_headers=HEADERS)
        active_rows: list[ProductRow] = []
        for idx, row in enumerate(rows, start=2):
            active = str(row.get("Active", "")).strip().lower()
            if active in {"true", "1", "yes", "y"}:
                active_rows.append(ProductRow(row_number=idx, values=row))
        return active_rows

    def update_result(
        self,
        product: ProductRow,
        current_main_price: Optional[Decimal],
        best_comparison_price: Optional[Decimal],
        best_comparison_store: str,
        status: str,
        notes: str,
    ) -> None:
        stamp = datetime.now(timezone.utc).isoformat()
        updates = {
            "Current Main Price": "" if current_main_price is None else str(current_main_price),
            "Best Comparison Price": "" if best_comparison_price is None else str(best_comparison_price),
            "Best Comparison Store": best_comparison_store,
            "Last Checked": stamp,
            "Status": status,
            "Notes": notes,
        }
        col_map = self._header_col_map()
        cells = []
        for field, value in updates.items():
            col = col_map[field]
            cells.append(gspread.Cell(row=product.row_number, col=col, value=value))
        self.worksheet.update_cells(cells)

    def _header_col_map(self) -> dict[str, int]:
        header_values = self.worksheet.row_values(1)
        return {name: i + 1 for i, name in enumerate(header_values)}
