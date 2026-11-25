"""AutoLeadGen V3 — Multi-Source Discovery Orchestrator.

Combines: Overpass API + Wikidata SPARQL + (future: Google Maps)
Deduplication via existing 5-level deduplicator.
No hardcoded result cap. Saves checkpoints for resume support.
"""
import time
import json
import logging
from typing import Optional, Callable

from integrations import overpass_discovery, wikidata_discovery
from pipeline.deduplicator import calculate_similarity, normalize_url_domain
from pipeline.cleaner import normalize_phone, clean_website, clean_business_name
from database.repository import LeadRepository
from utils.logger import info, warning

logger = logging.getLogger("AutoLeadGen")

# Score thresholds for deduplication across sources
_DEDUP_NAME_THRESHOLD = 82     # % similarity for business name
_DEDUP_PHONE_MATCH = True      # exact phone match always deduplicates
_DEDUP_EMAIL_MATCH = True      # exact email match always deduplicates
_DEDUP_DOMAIN_MATCH = True     # same website domain deduplicates


def _is_duplicate_in_buffer(lead: dict, seen_phones: set, seen_emails: set, seen_domains: set, seen_names: list) -> bool:
    """Fast in-memory dedup within a single discovery session."""
    phone = normalize_phone(lead.get("phone", ""))
    if phone and phone in seen_phones:
        return True

    email = (lead.get("email", "") or "").strip().lower()
    if email and email in seen_emails:
        return True

    website = clean_website(lead.get("website", ""))
    domain = normalize_url_domain(website) if website else ""
    if domain and domain in seen_domains:
        return True

    name_norm = clean_business_name(lead.get("business_name", "")).lower().strip()
    for existing_name in seen_names[-500:]:  # compare vs last 500 seen
        if calculate_similarity(name_norm, existing_name) >= _DEDUP_NAME_THRESHOLD:
            return True

    return False


def _record_in_buffer(lead: dict, seen_phones: set, seen_emails: set, seen_domains: set, seen_names: list):
    phone = normalize_phone(lead.get("phone", ""))
    if phone:
        seen_phones.add(phone)
    email = (lead.get("email", "") or "").strip().lower()
    if email:
        seen_emails.add(email)
    website = clean_website(lead.get("website", ""))
    domain = normalize_url_domain(website) if website else ""
    if domain:
        seen_domains.add(domain)
    name_norm = clean_business_name(lead.get("business_name", "")).lower().strip()
    if name_norm:
        seen_names.append(name_norm)


def _is_duplicate_in_db(lead: dict, repo: LeadRepository) -> bool:
    """Check the DB for near-duplicate before inserting."""
    phone = normalize_phone(lead.get("phone", ""))
    if phone:
        existing = repo.get_lead_by_phone(phone)
        if existing:
            return True

    email = (lead.get("email", "") or "").strip().lower()
    if email:
        cur = repo.conn.cursor()
        cur.execute("SELECT id FROM leads WHERE lower(email) = ? LIMIT 1", (email,))
        if cur.fetchone():
            return True

    website = clean_website(lead.get("website", ""))
    if website:
        existing = repo.get_lead_by_website(website)
        if existing:
            return True

    return False


def run_discovery(
    country: str,
    city: str = "",
    business_type: str = "all",
    sources: list = None,
    batch_size: int = 50,
    task_id: Optional[str] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
    **kwargs,  # absorbs extra kwargs from TaskManager
) -> dict:
    """
    Orchestrate multi-source business discovery.

    Args:
        country: Country name to search (e.g., "Egypt")
        city: Specific city (empty = search major cities)
        business_type: "all" or specific type (restaurant, shop, hotel, clinic, office)
        sources: list of ["overpass", "wikidata"] — defaults to both
        batch_size: leads to insert per checkpoint save
        task_id: optional task tracking ID
        progress_cb: callback(progress_pct: float, msg: str)
        cancel_check: callback() -> bool, returns True if cancelled

    Returns:
        dict with inserted, skipped_dups, errors counts + per-source breakdown
    """
    if sources is None:
        sources = ["overpass", "wikidata"]

    repo = LeadRepository()
    seen_phones, seen_emails, seen_domains, seen_names = set(), set(), set(), []
    stats = {"inserted": 0, "skipped_dups": 0, "errors": 0, "sources": {s: 0 for s in sources}}

    def _emit(pct: float, msg: str):
        if progress_cb:
            progress_cb(pct, msg)
        info(msg)

    _emit(0.0, f"🚀 Discovery started: {country}" + (f" / {city}" if city else ""))

    # Load existing DB phones/emails/domains into seen sets for fast lookup
    try:
        seen_phones = repo.get_all_known_phones()
        cur = repo.conn.cursor()
        cur.execute("SELECT email FROM leads WHERE email IS NOT NULL AND email != '' AND email != 'None'")
        seen_emails = {r[0].strip().lower() for r in cur.fetchall() if r[0]}
        cur.execute("SELECT website FROM leads WHERE website IS NOT NULL AND website != ''")
        seen_domains = {normalize_url_domain(clean_website(r[0])) for r in cur.fetchall() if r[0]}
        seen_domains.discard("")
    except Exception as e:
        warning(f"Could not pre-load seen sets: {e}")

    source_generators = []
    for source in sources:
        if cancel_check and cancel_check():
            break
        if source == "overpass":
            if city:
                gen = overpass_discovery.search_city(
                    city=city, country=country, business_type=business_type,
                    cancel_check=cancel_check,
                )
            else:
                gen = overpass_discovery.search_country(
                    country=country, business_type=business_type,
                    cancel_check=cancel_check, progress_cb=progress_cb,
                )
            source_generators.append(("overpass", gen))
        elif source == "wikidata":
            gen = wikidata_discovery.search_businesses(
                country=country, cancel_check=cancel_check, progress_cb=progress_cb,
            )
            source_generators.append(("wikidata", gen))

    total_seen = 0
    pending_batch = []

    def _flush_batch():
        nonlocal pending_batch
        for lead in pending_batch:
            if cancel_check and cancel_check():
                break
            if _is_duplicate_in_db(lead, repo):
                stats["skipped_dups"] += 1
            else:
                try:
                    repo.insert_lead(
                        business_name=lead["business_name"],
                        phone=lead.get("phone", ""),
                        address=lead.get("address", ""),
                        website=lead.get("website", ""),
                        industry=lead.get("industry", ""),
                        city=lead.get("city", ""),
                        source=lead.get("source", "overpass"),
                        language="English",
                        score=0,
                    )
                    # Update V3 columns via update_lead_fields
                    lead_row = repo.get_lead_by_phone(lead.get("phone", "")) or \
                               repo.get_lead_by_website(lead.get("website", ""))
                    if not lead_row:
                        cur2 = repo.conn.cursor()
                        cur2.execute(
                            "SELECT id FROM leads WHERE business_name = ? AND city = ? ORDER BY id DESC LIMIT 1",
                            (lead["business_name"], lead.get("city", "")),
                        )
                        row2 = cur2.fetchone()
                        if row2:
                            lead_id = row2[0]
                            update_fields = {
                                k: v for k, v in lead.items()
                                if k in (
                                    "latitude", "longitude", "coord_source", "coord_verified",
                                    "country", "continent", "collected_at", "source_url",
                                    "data_confidence", "email",
                                )
                                and v is not None and v != ""
                            }
                            if update_fields:
                                repo.update_lead_fields(lead_id, **update_fields)
                    stats["inserted"] += 1
                    src = lead.get("source", "overpass")
                    stats["sources"][src] = stats["sources"].get(src, 0) + 1
                    _record_in_buffer(lead, seen_phones, seen_emails, seen_domains, seen_names)
                except Exception as e:
                    logger.error(f"Insert error for '{lead.get('business_name')}': {e}")
                    stats["errors"] += 1
        pending_batch = []

    for src_name, gen in source_generators:
        if cancel_check and cancel_check():
            break
        _emit(0.1, f"📡 Source: {src_name} — {country}")
        checkpoint_key = f"{src_name}:{country}:{city}:{business_type}"
        source_count = 0

        for lead in gen:
            if cancel_check and cancel_check():
                break
            total_seen += 1
            source_count += 1

            if _is_duplicate_in_buffer(lead, seen_phones, seen_emails, seen_domains, seen_names):
                stats["skipped_dups"] += 1
                _record_in_buffer(lead, seen_phones, seen_emails, seen_domains, seen_names)
                continue

            pending_batch.append(lead)

            if len(pending_batch) >= batch_size:
                _flush_batch()
                _emit(
                    min(0.9, stats["inserted"] / max(total_seen, 1)),
                    f"✅ {stats['inserted']} inserted, {stats['skipped_dups']} deduped [{src_name}:{source_count}]",
                )
                repo.save_checkpoint(checkpoint_key, source=src_name, last_offset=source_count, total_found=source_count)

        _flush_batch()
        repo.save_checkpoint(checkpoint_key, source=src_name, last_offset=source_count, total_found=source_count)

    repo.close()
    result_msg = f"🏁 Discovery done: {stats['inserted']} new leads, {stats['skipped_dups']} duplicates skipped."
    _emit(1.0, result_msg)
    return stats
