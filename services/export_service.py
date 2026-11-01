"""AutoLeadGen v2 - Services: Low-Memory Excel and CSV (UTF-8-BOM) Lead Exporter."""
import csv
from datetime import datetime
from utils.logger import info, error

EXPORT_COLUMNS = [
    "ID",
    "Business",
    "Phone",
    "WhatsApp Status",
    "Phone Validity",
    "Address",
    "Website",
    "Industry",
    "City",
    "Score",
    "Language",
    "Status",
    "Source",
    "Created At",
    "Updated At",
]


def _format_lead_row(lead) -> dict:
    """Normalize a lead record tuple or dict into export dict."""
    if isinstance(lead, (list, tuple)):
        return {
            "ID": lead[0] if len(lead) > 0 else "",
            "Business": lead[1] if len(lead) > 1 else "",
            "Phone": lead[2] if len(lead) > 2 else "",
            "WhatsApp Status": lead[13] if len(lead) > 13 else "UNKNOWN",
            "Phone Validity": lead[14] if len(lead) > 14 else "UNKNOWN",
            "Address": lead[3] if len(lead) > 3 else "",
            "Website": lead[4] if len(lead) > 4 else "",
            "Industry": lead[5] if len(lead) > 5 else "",
            "City": lead[6] if len(lead) > 6 else "",
            "Score": lead[8] if len(lead) > 8 else 0,
            "Language": lead[10] if len(lead) > 10 else "",
            "Status": lead[9] if len(lead) > 9 else "",
            "Source": lead[7] if len(lead) > 7 else "",
            "Created At": lead[11] if len(lead) > 11 else "",
            "Updated At": lead[12] if len(lead) > 12 else "",
        }
    elif isinstance(lead, dict):
        return {col: lead.get(col, lead.get(col.lower().replace(" ", "_"), "")) for col in EXPORT_COLUMNS}
    return {}


class ExportService:
    @staticmethod
    def to_csv(leads, file_path=None) -> str:
        """
        Export leads to CSV file with UTF-8 BOM encoding for perfect Arabic rendering in Excel.
        Uses streaming rows to maintain low memory usage.
        """
        if not leads:
            return ""

        if file_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            file_path = f"leads_{timestamp}.csv"

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
                writer.writeheader()
                for lead in leads:
                    writer.writerow(_format_lead_row(lead))

            info(f"ExportService: {len(leads)} leads exported to CSV: {file_path}")
            return file_path
        except Exception as e:
            error(f"ExportService: Failed to export CSV: {e}")
            return ""

    @staticmethod
    def to_excel(leads, file_path=None) -> str:
        """Export leads to Excel (.xlsx) file using openpyxl."""
        if not leads:
            return ""

        if file_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            file_path = f"leads_{timestamp}.xlsx"

        try:
            import pandas as pd
            rows = [_format_lead_row(l) for l in leads]
            df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
            df.to_excel(file_path, index=False, engine="openpyxl")
            info(f"ExportService: {len(leads)} leads exported to Excel: {file_path}")
            return file_path
        except Exception as e:
            error(f"ExportService: Failed to export Excel: {e}")
            return ""


# Backward-compatible alias
Exporter = ExportService
