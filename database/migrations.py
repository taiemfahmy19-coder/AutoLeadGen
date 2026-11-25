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


V3_LEAD_COLUMNS = [
    ("latitude", "REAL DEFAULT NULL"),
    ("longitude", "REAL DEFAULT NULL"),
    ("coord_source", "TEXT DEFAULT ''"),
    ("coord_verified", "INTEGER DEFAULT 0"),
    ("country", "TEXT DEFAULT ''"),
    ("continent", "TEXT DEFAULT ''"),
    ("collected_at", "TEXT DEFAULT ''"),
    ("source_url", "TEXT DEFAULT ''"),
    ("ai_summary", "TEXT DEFAULT ''"),
    ("ai_category", "TEXT DEFAULT ''"),
    ("unsubscribed", "INTEGER DEFAULT 0"),
    ("last_reply_at", "TEXT DEFAULT ''"),
    ("reply_sentiment", "TEXT DEFAULT ''"),
    ("data_confidence", "TEXT DEFAULT 'unknown'"),
]


def run_v3_migrations(db_path=DB_PATH) -> dict:
    """Apply AutoLeadGen V3 schema extensions idempotently without touching existing data."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15.0)
    added_cols = []
    try:
        with conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA foreign_keys = ON;")

            # Ensure leads table has V3 columns if it already exists
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads'")
            if cur.fetchone():
                for col, col_def in V3_LEAD_COLUMNS:
                    try:
                        conn.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_def};")
                        added_cols.append(col)
                    except sqlite3.OperationalError:
                        pass
                conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_coords ON leads(latitude, longitude);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_industry ON leads(industry);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT DEFAULT '',
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'operator',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    is_active INTEGER DEFAULT 1,
                    last_login TEXT DEFAULT ''
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    progress REAL DEFAULT 0.0,
                    started_at TEXT DEFAULT '',
                    finished_at TEXT DEFAULT '',
                    error_log TEXT DEFAULT '',
                    params_json TEXT DEFAULT '{}',
                    result_json TEXT DEFAULT '{}',
                    cancel_requested INTEGER DEFAULT 0
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS discovery_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_key TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    last_offset INTEGER DEFAULT 0,
                    total_found INTEGER DEFAULT 0,
                    resumed_at TEXT DEFAULT (datetime('now', 'localtime'))
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    direction TEXT NOT NULL,
                    subject TEXT DEFAULT '',
                    body_html TEXT DEFAULT '',
                    body_text TEXT DEFAULT '',
                    from_addr TEXT DEFAULT '',
                    to_addr TEXT DEFAULT '',
                    message_id_header TEXT DEFAULT '',
                    in_reply_to TEXT DEFAULT '',
                    sent_at TEXT DEFAULT '',
                    received_at TEXT DEFAULT '',
                    sentiment TEXT DEFAULT 'unknown',
                    thread_id TEXT DEFAULT '',
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE SET NULL
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email_lead_id ON email_messages(lead_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email_msg_id ON email_messages(message_id_header);")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT DEFAULT '',
                    is_read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    lead_id INTEGER DEFAULT NULL
                );
            """)
        info(f"V3 migrations applied cleanly. Added columns: {added_cols}")
        return {"status": "success", "added_columns": added_cols}
    except Exception as e:
        error(f"V3 migration failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


if __name__ == "__main__":
    result = run_migrations()
    print("V2 Migration Result:", result)
    v3_res = run_v3_migrations()
    print("V3 Migration Result:", v3_res)
