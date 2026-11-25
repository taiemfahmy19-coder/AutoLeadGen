"""AutoLeadGen v2 - Database Repository with Indexed Queries, Thread Safety, and Atomic Merges."""
import sqlite3
import os
from datetime import datetime
from config.settings import DB_PATH
from config.constants import (
    STATUS_NEW,
    STATUS_QUALIFIED,
    STATUS_READY,
    STATUS_CONTACTED,
    STATUS_REPLIED,
    STATUS_INTERESTED,
    STATUS_NOT_INTERESTED,
    STATUS_DO_NOT_CONTACT,
    STATUS_INVALID,
    STATUS_NEEDS_REVIEW,
    WA_STATUS_VERIFIED,
    WA_STATUS_NOT_VERIFIED,
    WA_STATUS_UNKNOWN,
    SCORE_QUALIFIED_THRESHOLD,
    DEFAULT_ARABIC_TEMPLATE,
    DEFAULT_ENGLISH_TEMPLATE,
)
from database.connection import DatabaseManager
from database.base import AbstractLeadRepository
from utils.logger import info, audit, error


# Allowed columns for dynamic updates to prevent SQL column injection
ALLOWED_UPDATE_COLUMNS = {
    "business_name", "phone", "address", "website", "industry", "city",
    "source", "score", "status", "language", "whatsapp_status", "phone_validity",
    "email", "email_status", "instagram_handle", "facebook_url",
    "latitude", "longitude", "coord_source", "coord_verified",
    "country", "continent", "collected_at", "source_url",
    "ai_summary", "ai_category", "unsubscribed", "last_reply_at",
    "reply_sentiment", "data_confidence",
}


class LeadRepository(AbstractLeadRepository):
    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.conn
        self.cursor = self.conn.cursor()
        self._create_tables_and_indexes()
        self._seed_defaults()

    def _create_tables_and_indexes(self):
        with self.db_mgr.transaction() as conn:
            # 1. leads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT,
                    phone TEXT,
                    address TEXT,
                    website TEXT,
                    industry TEXT,
                    city TEXT,
                    source TEXT DEFAULT 'search',
                    score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'NEW',
                    language TEXT DEFAULT 'Arabic',
                    created_at TEXT DEFAULT (datetime('now', 'localtime')),
                    updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                    whatsapp_status TEXT DEFAULT 'UNKNOWN',
                    phone_validity TEXT DEFAULT 'UNKNOWN',
                    email TEXT DEFAULT '',
                    email_status TEXT DEFAULT 'UNKNOWN',
                    instagram_handle TEXT DEFAULT '',
                    facebook_url TEXT DEFAULT ''
                );
            """)

            # Migration: ensure omnichannel & V3 columns exist in existing databases
            for col, dflt in [
                ("whatsapp_status", "UNKNOWN"),
                ("phone_validity", "UNKNOWN"),
                ("email", "''"),
                ("email_status", "'UNKNOWN'"),
                ("instagram_handle", "''"),
                ("facebook_url", "''"),
                ("latitude", "NULL"),
                ("longitude", "NULL"),
                ("coord_source", "''"),
                ("coord_verified", "0"),
                ("country", "''"),
                ("continent", "''"),
                ("collected_at", "''"),
                ("source_url", "''"),
                ("ai_summary", "''"),
                ("ai_category", "''"),
                ("unsubscribed", "0"),
                ("last_reply_at", "''"),
                ("reply_sentiment", "''"),
                ("data_confidence", "'unknown'"),
            ]:
                try:
                    col_type = "REAL" if col in ("latitude", "longitude") else ("INTEGER" if col in ("coord_verified", "unsubscribed") else "TEXT")
                    conn.execute(f"ALTER TABLE leads ADD COLUMN {col} {col_type} DEFAULT {dflt};")
                except sqlite3.OperationalError:
                    pass

            # 2. contacts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    phone TEXT,
                    email TEXT,
                    website TEXT,
                    instagram TEXT,
                    facebook TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
                );
            """)

            # 3. interactions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    date TEXT,
                    channel TEXT,
                    message TEXT,
                    status TEXT,
                    notes TEXT,
                    FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
                );
            """)

            # 4. searches table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    industry TEXT,
                    city TEXT,
                    date TEXT,
                    results_count INTEGER DEFAULT 0
                );
            """)

            # 5. templates table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    language TEXT,
                    content TEXT,
                    industry TEXT
                );
            """)

            # 6. settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                );
            """)

            # 7. merge_history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS merge_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    source_lead_id INTEGER,
                    reason TEXT,
                    merged_at TEXT DEFAULT (datetime('now', 'localtime')),
                    master_record_id INTEGER
                );
            """)

            # 8. audit_log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                    action TEXT,
                    details TEXT
                );
            """)

            # Create Indexes for fast, O(1) searches
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_wa ON leads(whatsapp_status);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_coords ON leads(latitude, longitude);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_country ON leads(country);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_industry ON leads(industry);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_interactions_lead_id ON interactions(lead_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_contacts_lead_id ON contacts(lead_id);")

            # V3 Tables
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

    def _seed_defaults(self):
        with self.db_mgr.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM templates")
            if cursor.fetchone()[0] == 0:
                templates = [
                    ("العرض الأساسي - عام (عربي)", "Arabic", DEFAULT_ARABIC_TEMPLATE, "General"),
                    ("عطور ومستحضرات تجميل (عربي)", "Arabic", DEFAULT_ARABIC_TEMPLATE.replace("للبيزنسات", "لمحلات وبراندات العطور والتجميل"), "Perfumes"),
                    ("مطاعم وكافيهات (عربي)", "Arabic", DEFAULT_ARABIC_TEMPLATE.replace("للبيزنسات", "للمطاعم والكافيهات"), "Restaurants"),
                    ("Standard AI Video Pitch (English)", "English", DEFAULT_ENGLISH_TEMPLATE, "General"),
                ]
                cursor.executemany(
                    "INSERT INTO templates (name, language, content, industry) VALUES (?, ?, ?, ?)",
                    templates
                )

    def insert_lead(
        self,
        business_name: str,
        phone: str,
        address: str = "",
        website: str = "",
        industry: str = "",
        city: str = "",
        source: str = "search",
        language: str = "Arabic",
        score: int = 0,
        status: str = STATUS_NEW,
        whatsapp_status: str = WA_STATUS_UNKNOWN,
        phone_validity: str = "UNKNOWN",
    ) -> int:
        with self.db_mgr.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leads (business_name, phone, address, website, industry, city, source, score, status, language, whatsapp_status, phone_validity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (business_name, phone, address, website, industry, city, source, score, status, language, whatsapp_status, phone_validity))
            lead_id = cursor.lastrowid

        self.insert_audit_log("LEAD_CREATED", f"Lead ID {lead_id} ({business_name}) created from {source}")
        return lead_id

    def get_lead_by_id(self, lead_id: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        return cursor.fetchone()

    def get_lead_by_phone(self, phone: str):
        """Fast indexed search by normalized phone."""
        if not phone:
            return None
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE phone = ? LIMIT 1", (phone.strip(),))
        return cursor.fetchone()

    def get_lead_by_website(self, domain_or_url: str):
        """Fast indexed search by website substring."""
        if not domain_or_url:
            return None
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE lower(website) LIKE ? LIMIT 1", (f"%{domain_or_url.strip().lower()}%",))
        return cursor.fetchone()

    def get_leads_by_name_prefix(self, prefix: str):
        """Fetch candidate leads sharing the same 4-letter name prefix."""
        if not prefix or len(prefix) < 2:
            return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE lower(business_name) LIKE ? LIMIT 50", (f"{prefix.lower()}%",))
        return cursor.fetchall()

    def get_all_leads(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY score DESC, id DESC")
        return cursor.fetchall()

    def get_all_known_phones(self) -> set:
        """Return a set of all normalized and raw phone numbers already in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT phone FROM leads WHERE phone IS NOT NULL AND phone != ''")
        phones = set()
        for row in cursor.fetchall():
            p = row[0].strip()
            if p:
                digits_only = "".join(filter(str.isdigit, p))
                phones.add(p)
                phones.add(digits_only)
                phones.add(f"+{digits_only}")
                if digits_only.startswith("0"):
                    phones.add(digits_only[1:])
        return phones

    def get_all_known_business_names(self) -> set:
        """Return a set of lowercase normalized business names in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT business_name FROM leads WHERE business_name IS NOT NULL AND business_name != ''")
        return {row[0].strip().lower() for row in cursor.fetchall() if row[0]}

    def update_lead_language(self, lead_id: int, language: str):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET language = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (language, lead_id)
            )
        self.insert_audit_log("LANGUAGE_UPDATED", f"Lead ID {lead_id} language updated to {language}")

    def update_lead_status(self, lead_id: int, status: str):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (status, lead_id)
            )
        self.insert_audit_log("STATUS_UPDATED", f"Lead ID {lead_id} status updated to {status}")

    def update_lead_whatsapp_status(self, lead_id: int, whatsapp_status: str):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET whatsapp_status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (whatsapp_status, lead_id)
            )
        self.insert_audit_log("WA_STATUS_UPDATED", f"Lead ID {lead_id} whatsapp_status updated to {whatsapp_status}")

    def update_lead_email(self, lead_id: int, email: str):
        norm = (email or "").strip().lower()
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET email = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (norm, lead_id)
            )
        self.insert_audit_log("EMAIL_UPDATED", f"Lead ID {lead_id} email updated to {norm}")

    def update_lead_email_status(self, lead_id: int, email_status: str):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET email_status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (email_status, lead_id)
            )
        self.insert_audit_log("EMAIL_STATUS_UPDATED", f"Lead ID {lead_id} email_status updated to {email_status}")

    def update_lead_social(self, lead_id: int, instagram_handle: str = None, facebook_url: str = None):
        fields = {}
        if instagram_handle is not None:
            fields["instagram_handle"] = instagram_handle.strip()
        if facebook_url is not None:
            fields["facebook_url"] = facebook_url.strip()
        if fields:
            self.update_lead_fields(lead_id, **fields)

    def update_lead_score(self, lead_id: int, score: int):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE leads SET score = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
                (score, lead_id)
            )

    def update_lead_fields(self, lead_id: int, **fields):
        if not fields:
            return
        set_clauses = []
        values = []
        for k, v in fields.items():
            if k not in ALLOWED_UPDATE_COLUMNS:
                raise ValueError(f"Invalid column update attempt: {k}")
            set_clauses.append(f"{k} = ?")
            values.append(v)

        set_clauses.append("updated_at = datetime('now', 'localtime')")
        values.append(lead_id)
        sql = f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?"

        with self.db_mgr.transaction() as conn:
            conn.execute(sql, tuple(values))

    def delete_lead(self, lead_id: int):
        with self.db_mgr.transaction() as conn:
            conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            conn.execute("DELETE FROM contacts WHERE lead_id = ?", (lead_id,))
            conn.execute("DELETE FROM interactions WHERE lead_id = ?", (lead_id,))
        self.insert_audit_log("LEAD_DELETED", f"Lead ID {lead_id} deleted")

    def clear_all_leads(self, reset_searches: bool = True) -> int:
        """Delete all leads, contacts, and interactions. Returns count of leads deleted."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads")
        count = cursor.fetchone()[0]

        with self.db_mgr.transaction() as conn:
            conn.execute("DELETE FROM interactions")
            conn.execute("DELETE FROM contacts")
            conn.execute("DELETE FROM leads")
            if reset_searches:
                conn.execute("DELETE FROM searches")
            try:
                conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('leads', 'contacts', 'interactions', 'searches')")
            except Exception:
                pass

        self.insert_audit_log("DATABASE_RESET", f"Wiped all {count} leads and reset dashboard.")
        info(f"LeadRepository: Cleared all {count} leads successfully.")
        return count

    def auto_qualify_new_leads(self, min_score=SCORE_QUALIFIED_THRESHOLD) -> int:
        """Promote high-scoring NEW leads with valid phone to QUALIFIED."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM leads 
            WHERE status = ? 
              AND score >= ? 
              AND phone IS NOT NULL 
              AND TRIM(phone) != ''
        """, (STATUS_NEW, min_score))
        eligible_ids = [row[0] for row in cursor.fetchall()]

        if eligible_ids:
            placeholders = ",".join("?" * len(eligible_ids))
            with self.db_mgr.transaction() as conn:
                conn.execute(f"""
                    UPDATE leads 
                    SET status = ?, updated_at = datetime('now', 'localtime') 
                    WHERE id IN ({placeholders})
                """, (STATUS_QUALIFIED, *eligible_ids))
            self.insert_audit_log("AUTO_QUALIFY", f"Auto-qualified {len(eligible_ids)} leads with Score >= {min_score}")

        return len(eligible_ids)

    def promote_to_ready(self, lead_ids=None):
        """
        Promote QUALIFIED leads to READY:
        - Must have phone
        - Must have business name (>= 2 chars)
        - Must NOT be DO_NOT_CONTACT or INVALID or NOT_VERIFIED
        """
        cursor = self.conn.cursor()
        if lead_ids is not None:
            if not lead_ids:
                return [], []
            placeholders = ",".join("?" * len(lead_ids))
            cursor.execute(f"SELECT id, business_name, phone, status, score, whatsapp_status FROM leads WHERE id IN ({placeholders})", tuple(lead_ids))
        else:
            cursor.execute("SELECT id, business_name, phone, status, score, whatsapp_status FROM leads WHERE status = ?", (STATUS_QUALIFIED,))

        rows = cursor.fetchall()
        promoted = []
        rejected = []

        for row in rows:
            lid, b_name, phone, st_val, sc, wa_st = row[0], row[1], row[2], row[3], row[4], row[5] if len(row) > 5 else WA_STATUS_UNKNOWN
            if st_val in [STATUS_DO_NOT_CONTACT, STATUS_INVALID, STATUS_NEEDS_REVIEW] or wa_st == WA_STATUS_NOT_VERIFIED:
                rejected.append(lid)
                continue

            has_phone = bool(phone and str(phone).strip())
            has_name = bool(b_name and len(str(b_name).strip()) >= 2)

            if has_phone and has_name:
                promoted.append(lid)
            else:
                rejected.append(lid)

        if promoted:
            p_holders = ",".join("?" * len(promoted))
            with self.db_mgr.transaction() as conn:
                conn.execute(f"""
                    UPDATE leads 
                    SET status = ?, updated_at = datetime('now', 'localtime') 
                    WHERE id IN ({p_holders})
                """, (STATUS_READY, *promoted))
            self.insert_audit_log("PROMOTED_TO_READY", f"Promoted {len(promoted)} leads to READY")

        return promoted, rejected

    def merge_leads(self, master_id: int, duplicate_id: int, reason="Smart duplicate match") -> bool:
        """Atomic merge of duplicate lead into master lead with transaction protection."""
        master = self.get_lead_by_id(master_id)
        duplicate = self.get_lead_by_id(duplicate_id)
        if not master or not duplicate:
            return False

        with self.db_mgr.transaction() as conn:
            updates = {}
            if not master[2] and duplicate[2]:
                updates["phone"] = duplicate[2]
            if not master[3] and duplicate[3]:
                updates["address"] = duplicate[3]
            if not master[4] and duplicate[4]:
                updates["website"] = duplicate[4]
            if not master[5] and duplicate[5]:
                updates["industry"] = duplicate[5]
            if not master[6] and duplicate[6]:
                updates["city"] = duplicate[6]

            if duplicate[8] and duplicate[8] > (master[8] or 0):
                updates["score"] = duplicate[8]

            if updates:
                set_clauses = [f"{k} = ?" for k in updates.keys()]
                set_clauses.append("updated_at = datetime('now', 'localtime')")
                vals = list(updates.values()) + [master_id]
                conn.execute(f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?", tuple(vals))

            # Re-associate contacts and interactions to master
            conn.execute("UPDATE contacts SET lead_id = ? WHERE lead_id = ?", (master_id, duplicate_id))
            conn.execute("UPDATE interactions SET lead_id = ? WHERE lead_id = ?", (master_id, duplicate_id))

            # Record in merge_history
            conn.execute(
                "INSERT INTO merge_history (lead_id, source_lead_id, reason, merged_at, master_record_id) VALUES (?, ?, ?, ?, ?)",
                (master_id, duplicate_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), master_id)
            )

            # Delete duplicate lead
            conn.execute("DELETE FROM leads WHERE id = ?", (duplicate_id,))

        self.insert_audit_log("LEADS_MERGED", f"Duplicate Lead {duplicate_id} merged into Master {master_id}. Reason: {reason}")
        return True

    def insert_interaction(self, lead_id: int, date: str = None, channel: str = "WhatsApp", message: str = "", status: str = "MANUALLY_MARKED", notes: str = ""):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO interactions (lead_id, date, channel, message, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (lead_id, date, channel, message, status, notes)
            )
        self.insert_audit_log("INTERACTION_LOGGED", f"Interaction ({status}) logged for Lead ID {lead_id} via {channel}")

    def get_interactions_for_lead(self, lead_id: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM interactions WHERE lead_id = ? ORDER BY id DESC", (lead_id,))
        return cursor.fetchall()

    def insert_search(self, industry: str, city: str, results_count: int = 0):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO searches (industry, city, date, results_count) VALUES (?, ?, ?, ?)",
                (industry, city, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), results_count)
            )

    def get_searches(self, limit: int = 20):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM searches ORDER BY id DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def insert_template(self, name: str, language: str, content: str, industry: str = "General") -> int:
        with self.db_mgr.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO templates (name, language, content, industry) VALUES (?, ?, ?, ?)",
                (name, language, content, industry)
            )
            return cursor.lastrowid

    def update_template(self, template_id: int, name: str, language: str, content: str, industry: str = "General"):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE templates SET name = ?, language = ?, content = ?, industry = ? WHERE id = ?",
                (name, language, content, industry, template_id)
            )

    def get_all_templates(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM templates ORDER BY id ASC")
        return cursor.fetchall()

    def insert_merge_history(self, lead_id: int, source_lead_id: int = None, reason: str = "", master_record_id: int = None):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO merge_history (lead_id, source_lead_id, reason, merged_at, master_record_id) VALUES (?, ?, ?, ?, ?)",
                (lead_id, source_lead_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), master_record_id)
            )

    def get_merge_history(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM merge_history ORDER BY id DESC")
        return cursor.fetchall()

    def insert_audit_log(self, action: str, details: str):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO audit_log (action, details) VALUES (?, ?)",
                (action, str(details))
            )

    def get_audit_logs(self, limit: int = 100):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def get_dashboard_metrics(self) -> dict:
        leads = self.get_all_leads()
        total = len(leads)

        counts = {
            "total": total,
            "new": sum(1 for l in leads if l[9] == STATUS_NEW),
            "qualified": sum(1 for l in leads if l[9] == STATUS_QUALIFIED),
            "ready": sum(1 for l in leads if l[9] == STATUS_READY),
            "contacted": sum(1 for l in leads if l[9] == STATUS_CONTACTED),
            "replied": sum(1 for l in leads if l[9] == STATUS_REPLIED),
            "interested": sum(1 for l in leads if l[9] == STATUS_INTERESTED),
            "not_interested": sum(1 for l in leads if l[9] == STATUS_NOT_INTERESTED),
            "do_not_contact": sum(1 for l in leads if l[9] == STATUS_DO_NOT_CONTACT),
            "invalid": sum(1 for l in leads if l[9] == STATUS_INVALID),
            "needs_review": sum(1 for l in leads if l[9] == STATUS_NEEDS_REVIEW),
            "wa_verified": sum(1 for l in leads if len(l) > 13 and l[13] == WA_STATUS_VERIFIED),
            "wa_not_verified": sum(1 for l in leads if len(l) > 13 and l[13] == WA_STATUS_NOT_VERIFIED),
            "wa_unknown": sum(1 for l in leads if len(l) <= 13 or l[13] == WA_STATUS_UNKNOWN or not l[13]),
        }

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM merge_history")
        counts["duplicates_merged"] = cursor.fetchone()[0]

        scores = [l[8] for l in leads if l[8] is not None]
        counts["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0
        return counts

    # ── V3 Paginated, Geospatial & Platform Methods ───────────────────────────

    def _lead_row_to_dict(self, cursor, row) -> dict:
        if row is None:
            return {}
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))

    def get_leads_paginated(self, page: int = 1, page_size: int = 50, filters: dict = None):
        page = max(1, int(page))
        page_size = max(1, min(500, int(page_size)))
        offset = (page - 1) * page_size
        where_clauses, params = [], []
        if filters:
            if filters.get("status"):
                where_clauses.append("status = ?")
                params.append(filters["status"])
            if filters.get("country"):
                where_clauses.append("lower(country) = lower(?)")
                params.append(filters["country"])
            if filters.get("city"):
                where_clauses.append("lower(city) LIKE ?")
                params.append(f"%{filters['city'].lower()}%")
            if filters.get("industry"):
                where_clauses.append("lower(industry) LIKE ?")
                params.append(f"%{filters['industry'].lower()}%")
            if filters.get("min_score") is not None:
                where_clauses.append("score >= ?")
                params.append(int(filters["min_score"]))
            if filters.get("search"):
                q = f"%{filters['search'].lower()}%"
                where_clauses.append("(lower(business_name) LIKE ? OR lower(email) LIKE ? OR phone LIKE ? OR lower(city) LIKE ?)")
                params.extend([q, q, q, q])
        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM leads{where_sql}", tuple(params))
        total = cursor.fetchone()[0]
        cursor.execute(
            f"SELECT * FROM leads{where_sql} ORDER BY score DESC, id DESC LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]),
        )
        rows = [self._lead_row_to_dict(cursor, r) for r in cursor.fetchall()]
        return rows, total

    def get_leads_in_bbox(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        limit: int = 5000,
        filters: dict = None,
    ) -> list:
        where_clauses = [
            "latitude IS NOT NULL",
            "longitude IS NOT NULL",
            "latitude BETWEEN ? AND ?",
            "longitude BETWEEN ? AND ?",
        ]
        params = [float(min_lat), float(max_lat), float(min_lon), float(max_lon)]
        if filters:
            if filters.get("country"):
                where_clauses.append("lower(country) = lower(?)")
                params.append(filters["country"])
            if filters.get("industry"):
                where_clauses.append("lower(industry) LIKE ?")
                params.append(f"%{filters['industry'].lower()}%")
            if filters.get("min_score") is not None:
                where_clauses.append("score >= ?")
                params.append(int(filters["min_score"]))
        sql = f"SELECT * FROM leads WHERE {' AND '.join(where_clauses)} ORDER BY score DESC LIMIT ?"
        params.append(int(limit))
        cursor = self.conn.cursor()
        cursor.execute(sql, tuple(params))
        return [self._lead_row_to_dict(cursor, r) for r in cursor.fetchall()]

    # Users
    def create_user(self, username: str, email: str, password_hash: str, role: str = "operator") -> int:
        with self.db_mgr.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username.strip(), email.strip(), password_hash, role),
            )
            return cur.lastrowid

    def get_user_by_username(self, username: str):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? LIMIT 1", (username.strip(),))
        row = cur.fetchone()
        return self._lead_row_to_dict(cur, row) if row else None

    def get_user_by_id(self, user_id: int):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,))
        row = cur.fetchone()
        return self._lead_row_to_dict(cur, row) if row else None

    def count_users(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

    def list_users(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT id, username, email, role, created_at, is_active, last_login FROM users ORDER BY id ASC")
        return [self._lead_row_to_dict(cur, r) for r in cur.fetchall()]

    def update_user_last_login(self, user_id: int):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "UPDATE users SET last_login = datetime('now', 'localtime') WHERE id = ?",
                (user_id,),
            )

    # Tasks
    def create_task(self, task_id: str, task_type: str, params_json: str = "{}"):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO tasks (id, task_type, status, progress, started_at, params_json) VALUES (?, ?, 'running', 0.0, datetime('now', 'localtime'), ?)",
                (task_id, task_type, params_json),
            )

    def update_task_progress(self, task_id: str, progress: float, status: str, error_log: str = "", result_json: str = None):
        with self.db_mgr.transaction() as conn:
            if status in ("completed", "failed", "cancelled"):
                if result_json is not None:
                    conn.execute(
                        "UPDATE tasks SET progress = ?, status = ?, error_log = ?, result_json = ?, finished_at = datetime('now', 'localtime') WHERE id = ?",
                        (progress, status, error_log, result_json, task_id),
                    )
                else:
                    conn.execute(
                        "UPDATE tasks SET progress = ?, status = ?, error_log = ?, finished_at = datetime('now', 'localtime') WHERE id = ?",
                        (progress, status, error_log, task_id),
                    )
            else:
                conn.execute(
                    "UPDATE tasks SET progress = ?, status = ?, error_log = ? WHERE id = ?",
                    (progress, status, error_log, task_id),
                )

    def get_task_by_id(self, task_id: str):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ? LIMIT 1", (task_id,))
        row = cur.fetchone()
        return self._lead_row_to_dict(cur, row) if row else None

    def list_tasks(self, limit: int = 50) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks ORDER BY started_at DESC LIMIT ?", (limit,))
        return [self._lead_row_to_dict(cur, r) for r in cur.fetchall()]

    def cancel_task(self, task_id: str):
        with self.db_mgr.transaction() as conn:
            conn.execute("UPDATE tasks SET cancel_requested = 1 WHERE id = ?", (task_id,))

    def is_task_cancelled(self, task_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute("SELECT cancel_requested FROM tasks WHERE id = ? LIMIT 1", (task_id,))
        row = cur.fetchone()
        return bool(row and row[0] == 1)

    # Discovery checkpoints
    def save_checkpoint(self, search_key: str, source: str, last_offset: int, total_found: int):
        with self.db_mgr.transaction() as conn:
            conn.execute(
                """
                INSERT INTO discovery_checkpoints (search_key, source, last_offset, total_found, resumed_at)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
                ON CONFLICT(search_key) DO UPDATE SET
                    last_offset = excluded.last_offset,
                    total_found = excluded.total_found,
                    resumed_at = datetime('now', 'localtime')
                """,
                (search_key, source, last_offset, total_found),
            )

    def load_checkpoint(self, search_key: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT last_offset FROM discovery_checkpoints WHERE search_key = ? LIMIT 1", (search_key,))
        row = cur.fetchone()
        return int(row[0]) if row else 0

    # Email messages & notifications
    def insert_email_message(
        self,
        lead_id: int,
        direction: str,
        subject: str = "",
        body_html: str = "",
        body_text: str = "",
        from_addr: str = "",
        to_addr: str = "",
        message_id_header: str = "",
        in_reply_to: str = "",
        sent_at: str = "",
        received_at: str = "",
        sentiment: str = "unknown",
        thread_id: str = "",
    ) -> int:
        with self.db_mgr.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO email_messages
                (lead_id, direction, subject, body_html, body_text, from_addr, to_addr,
                 message_id_header, in_reply_to, sent_at, received_at, sentiment, thread_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (lead_id, direction, subject, body_html, body_text, from_addr, to_addr,
                 message_id_header, in_reply_to, sent_at, received_at, sentiment, thread_id),
            )
            return cur.lastrowid

    def get_email_messages(self, lead_id: int = None, limit: int = 100) -> list:
        cur = self.conn.cursor()
        if lead_id is not None:
            cur.execute("SELECT * FROM email_messages WHERE lead_id = ? ORDER BY id DESC LIMIT ?", (lead_id, limit))
        else:
            cur.execute("SELECT * FROM email_messages ORDER BY id DESC LIMIT ?", (limit,))
        return [self._lead_row_to_dict(cur, r) for r in cur.fetchall()]

    def create_notification(self, ntype: str, title: str, body: str = "", lead_id: int = None) -> int:
        with self.db_mgr.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notifications (type, title, body, lead_id) VALUES (?, ?, ?, ?)",
                (ntype, title, body, lead_id),
            )
            return cur.lastrowid

    def get_notifications(self, unread_only: bool = False, limit: int = 50) -> list:
        cur = self.conn.cursor()
        if unread_only:
            cur.execute("SELECT * FROM notifications WHERE is_read = 0 ORDER BY id DESC LIMIT ?", (limit,))
        else:
            cur.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,))
        return [self._lead_row_to_dict(cur, r) for r in cur.fetchall()]

    def mark_notification_read(self, notification_id: int):
        with self.db_mgr.transaction() as conn:
            conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))

    def close(self):
        self.db_mgr.close()
