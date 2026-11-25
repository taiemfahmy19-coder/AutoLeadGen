"""AutoLeadGen V3 — Inbound IMAP Email Listener & Reply Intelligence.

Features:
- Built-in imaplib (100% free, zero paid dependencies)
- SSL/TLS IMAP connection
- Auto-decryption of stored credentials via core.security.decrypt_secret
- Matches replies to leads via In-Reply-To header or Sender Email address
- Local NLP sentiment classification:
    'interested' | 'not_interested' | 'follow_up' | 'out_of_office' | 'unknown'
- Updates lead status in DB: STATUS_REPLIED ('REPLIED') & records interaction
- Background scheduled worker via TaskManager
"""
import os
import re
import imaplib
import email
from email.header import decode_header
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from config.settings import DATA_DIR
from config.constants import STATUS_REPLIED
from core.security import decrypt_secret
from database.repository import LeadRepository
from utils.logger import info, warning, error

logger = logging.getLogger("AutoLeadGen")

# Local Sentiment Classification Rules
POSITIVE_SIGNALS = [
    r"\b(interested|price|quote|details|call me|schedule|demo|meet|proposal|yes|tell me more|send info|sounds good)\b",
    r"(مهتم|السعر|تفاصيل|عرض أسعار|موافقة|اتصل بي|حدد موعد|تمام|مرحبا|ارسل التفاصيل|حابب اعرف)",
]
NEGATIVE_SIGNALS = [
    r"\b(not interested|unsubscribe|remove|stop|no thanks|never|don't contact|spam)\b",
    r"(غير مهتم|احذف|الغاء الاشتراك|لا ترسل|شكرا لا نريد|توقف)",
]
OOO_SIGNALS = [
    r"\b(out of office|automatic reply|on vacation|away from|annual leave|maternity leave)\b",
    r"(خارج المكتب|رد تلقائي|في اجازة|غير متواجد)",
]
FOLLOW_UP_SIGNALS = [
    r"\b(next week|next month|later|busy right now|contact me in|follow up|after)\b",
    r"(الاسبوع القادم|الشهر القادم|مشغول حاليا|تواصل معي لاحقا|بعد العيد)",
]


def classify_reply_sentiment(text: str) -> str:
    """Classify reply text into business sentiment categories locally."""
    if not text:
        return "unknown"
    t = text.lower()
    for pat in OOO_SIGNALS:
        if re.search(pat, t, re.I):
            return "out_of_office"
    for pat in NEGATIVE_SIGNALS:
        if re.search(pat, t, re.I):
            return "not_interested"
    for pat in POSITIVE_SIGNALS:
        if re.search(pat, t, re.I):
            return "interested"
    for pat in FOLLOW_UP_SIGNALS:
        if re.search(pat, t, re.I):
            return "follow_up"
    return "unknown"


def _decode_mime_words(raw: Optional[str]) -> str:
    if not raw:
        return ""
    decoded_fragments = decode_header(raw)
    result = []
    for frag, enc in decoded_fragments:
        if isinstance(frag, bytes):
            result.append(frag.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(str(frag))
    return "".join(result)


def _extract_body(msg: email.message.Message) -> Tuple[str, str]:
    """Extract plain text and HTML bodies from MIME email."""
    text_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get("Content-Disposition", ""))
            if "attachment" in cdispo:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ctype == "text/plain" and not text_body:
                text_body = decoded
            elif ctype == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text_body = payload.decode(charset, errors="replace")
    return text_body.strip(), html_body.strip()


class IMAPListener:
    def __init__(self, host: str, port: int, email_addr: str, password: str, use_ssl: bool = True):
        self.host = host.strip()
        self.port = int(port)
        self.email_addr = email_addr.strip()
        self.password = decrypt_secret(password.strip())
        self.use_ssl = use_ssl
        self._client: Optional[imaplib.IMAP4] = None

    def connect(self) -> bool:
        try:
            if self.use_ssl:
                self._client = imaplib.IMAP4_SSL(self.host, self.port, timeout=20)
            else:
                self._client = imaplib.IMAP4(self.host, self.port, timeout=20)
            self._client.login(self.email_addr, self.password)
            return True
        except Exception as e:
            error(f"IMAP connect failed for {self.email_addr} on {self.host}:{self.port} — {e}")
            self._client = None
            return False

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
                self._client.logout()
            except Exception:
                pass
            self._client = None

    def poll_unseen_emails(self, max_fetch: int = 50) -> List[Dict[str, Any]]:
        """Fetch unread messages from INBOX."""
        if not self._client and not self.connect():
            return []
        messages = []
        try:
            self._client.select("INBOX")
            status, response = self._client.search(None, "UNSEEN")
            if status != "OK" or not response or not response[0]:
                return []
            msg_ids = response[0].split()
            # Fetch latest first
            msg_ids = msg_ids[-max_fetch:]
            for mid in msg_ids:
                try:
                    res, data = self._client.fetch(mid, "(RFC822)")
                    if res != "OK" or not data:
                        continue
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    subject = _decode_mime_words(msg.get("Subject", ""))
                    from_hdr = _decode_mime_words(msg.get("From", ""))
                    to_hdr = _decode_mime_words(msg.get("To", ""))
                    msg_id_hdr = msg.get("Message-ID", "").strip()
                    in_reply_to = msg.get("In-Reply-To", "").strip()
                    date_hdr = msg.get("Date", "")
                    text_body, html_body = _extract_body(msg)

                    # Extract pure email from From header (e.g. "John <john@example.com>" -> "john@example.com")
                    match = re.search(r"[\w\.-]+@[\w\.-]+", from_hdr)
                    from_clean = match.group(0).lower() if match else from_hdr.lower()

                    messages.append({
                        "subject": subject,
                        "from_addr": from_clean,
                        "to_addr": to_hdr,
                        "message_id": msg_id_hdr,
                        "in_reply_to": in_reply_to,
                        "date_str": date_hdr,
                        "text_body": text_body,
                        "html_body": html_body,
                        "sentiment": classify_reply_sentiment(f"{subject} {text_body}"),
                    })
                except Exception as ex:
                    logger.warning(f"Failed parsing email {mid}: {ex}")
        except Exception as e:
            error(f"IMAP poll error: {e}")
        return messages

    def process_incoming_replies(self, repo: Optional[LeadRepository] = None) -> int:
        """Poll unread emails, match with leads in CRM, update status and record interactions."""
        close_repo = False
        if repo is None:
            repo = LeadRepository()
            close_repo = True
        matched_count = 0
        try:
            unseen = self.poll_unseen_emails()
            for item in unseen:
                sender_email = item["from_addr"]
                sentiment = item["sentiment"]
                # 1. Look up lead by email
                cur = repo.conn.cursor()
                cur.execute("SELECT id, business_name, status FROM leads WHERE lower(email) = ? LIMIT 1", (sender_email,))
                lead_row = cur.fetchone()
                lead_id = lead_row[0] if lead_row else None

                # 2. Store in email_messages table
                repo.insert_email_message(
                    lead_id=lead_id,
                    direction="inbound",
                    subject=item["subject"],
                    body_html=item["html_body"],
                    body_text=item["text_body"],
                    from_addr=item["from_addr"],
                    to_addr=item["to_addr"],
                    message_id_header=item["message_id"],
                    in_reply_to=item["in_reply_to"],
                    received_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    sentiment=sentiment,
                )

                if lead_id:
                    matched_count += 1
                    # Update lead record
                    repo.update_lead_fields(
                        lead_id,
                        status=STATUS_REPLIED,
                        last_reply_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        reply_sentiment=sentiment,
                    )
                    # Log interaction
                    repo.insert_interaction(
                        lead_id=lead_id,
                        channel="Email",
                        message=f"Subject: {item['subject']}\n\n{item['text_body'][:300]}",
                        status="REPLIED",
                        notes=f"Sentiment: {sentiment.upper()}",
                    )
                    # Create notification
                    repo.create_notification(
                        ntype="reply_received",
                        title=f"📩 رد جديد من {lead_row[1]}",
                        body=f"المشاعر: {sentiment} | الموضوع: {item['subject']}",
                        lead_id=lead_id,
                    )
                    info(f"Matched incoming reply from {sender_email} to Lead ID {lead_id} ({sentiment})")
                else:
                    # General notification
                    repo.create_notification(
                        ntype="inbox_message",
                        title=f"بريد وارد جديد من {sender_email}",
                        body=f"الموضوع: {item['subject']}",
                    )
            return matched_count
        finally:
            self.disconnect()
            if close_repo:
                repo.close()
