"""AutoLeadGen v2 - Database Migration & Legacy Data Cleanup Script."""
import os
import sqlite3
from datetime import datetime
from config.settings import DB_PATH
from database.backup_service import BackupService
from pipeline.cleaner import normalize_phone, is_mobile_phone, get_phone_validity
from config.constants import (
    STATUS_NEEDS_REVIEW,
    WA_STATUS_VERIFIED,
    WA_STATUS_UNKNOWN,
    PHONE_VALID,
)
from utils.logger import info, audit, error


def run_migrations(db_path=DB_PATH) -> dict:
    """
    Execute full database migration and legacy data cleaning:
    1. Create safety snapshot of database.
    2. Upgrade SQLite settings (WAL, Foreign keys, busy_timeout).
    3. Ensure all columns & indexes exist.
    4. Re-normalize all existing phone numbers.
    5. Reset unverified false 'VERIFIED' statuses to 'UNKNOWN'.
    6. Flag landlines and unverified fake numbers as 'NEEDS_REVIEW'.
    """
    if not os.path.exists(db_path):
        info("Migration: No existing database found. Skipping migration.")
        return {"status": "skipped", "message": "Database does not exist."}

    # 1. Safety Backup First
    backup_svc = BackupService(db_path=db_path)
    backup_file = f"pre_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    backup_path = backup_svc.create_backup(backup_file)
    info(f"Migration: Safety backup created at: {backup_path}")

    stats = {
        "total_leads_checked": 0,
        "phones_re_normalized": 0,
        "false_verified_reset": 0,
        "moved_to_needs_review": 0,
        "interactions_cleaned": 0,
    }

    conn = sqlite3.connect(db_path, timeout=15.0)
    try:
        with conn:
            # 2. Pragmas
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")

            # 3. Columns
            for col, dflt in [("whatsapp_status", "UNKNOWN"), ("phone_validity", "UNKNOWN")]:
                try:
                    conn.execute(f"ALTER TABLE leads ADD COLUMN {col} TEXT DEFAULT '{dflt}';")
                except sqlite3.OperationalError:
                    pass

            # 4. Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_wa ON leads(whatsapp_status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON interactions(lead_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_lead_id ON contacts(lead_id);")

            # 5. Inspect and Clean Leads Table
            cursor = conn.cursor()
            cursor.execute("SELECT id, phone, whatsapp_status, status, source FROM leads")
            rows = cursor.fetchall()
            stats["total_leads_checked"] = len(rows)

            for row in rows:
                lid, raw_phone, wa_st, crm_st, src = row
                new_phone = normalize_phone(raw_phone)
                phone_val = get_phone_validity(new_phone)
                is_mobile = is_mobile_phone(new_phone)

                updates = {}
                if new_phone != raw_phone:
                    updates["phone"] = new_phone
                    stats["phones_re_normalized"] += 1

                updates["phone_validity"] = phone_val

                # Reset any false 'VERIFIED' status from synthetic searches
                if wa_st == WA_STATUS_VERIFIED and src in ["search", "verified_directory", "local_directory"]:
                    updates["whatsapp_status"] = WA_STATUS_UNKNOWN
                    stats["false_verified_reset"] += 1

                # If phone is not a valid mobile line, move from READY/QUALIFIED to NEEDS_REVIEW
                if not is_mobile and crm_st in ["READY", "QUALIFIED", "NEW"]:
                    updates["status"] = STATUS_NEEDS_REVIEW
                    stats["moved_to_needs_review"] += 1

                if updates:
                    set_parts = [f"{k} = ?" for k in updates.keys()]
                    vals = list(updates.values()) + [lid]
                    conn.execute(f"UPDATE leads SET {', '.join(set_parts)} WHERE id = ?", tuple(vals))

            # 6. Clean interactions table (change simulated SENT to MANUALLY_MARKED)
            cursor.execute("""
                UPDATE interactions 
                SET status = 'MANUALLY_MARKED' 
                WHERE status = 'SENT' AND (notes LIKE '%Supervised outreach sent%' OR channel = 'WhatsApp')
            """)
            stats["interactions_cleaned"] = cursor.rowcount

        info(f"Migration completed successfully. Stats: {stats}")
        return {"status": "success", "stats": stats, "backup_path": backup_path}

    except Exception as e:
        error(f"Migration failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


if __name__ == "__main__":
    result = run_migrations()
    print("Migration Result:", result)
