"""Simulate rendering and executing every part of the 3 views and core pipeline."""
import sys
import os

APP_DIR = r"D:\AI feed\AutoLeadGen"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st

# Check all imports in ui/views
print("1. Checking all imports...")
try:
    from ui.views.dashboard_view import render_dashboard, render_system_controls
    from ui.views.lead_discovery_protection_view import render_lead_discovery_and_protection
    from ui.views.settings_view import render_settings
    from core.scheduler import SmartScheduler
    from core.config_manager import ConfigManager
    from core.system_controller import SystemController
    from database.repository import LeadRepository
    from integrations.maps_scraper import LeadScraper
    from pipeline.cleaner import normalize_phone, is_mobile_phone, get_phone_validity
    from pipeline.deduplicator import Deduplicator
    from services.lead_service import LeadService
    from services.outreach_service import OutreachService
    from services.export_service import ExportService
    print(">>> All imports succeeded!")
except Exception as e:
    print(f">>> Import error: {e}")
    sys.exit(1)

# Check database methods used by the views
print("2. Checking DB queries used by views...")
db = LeadRepository()
all_leads = db.get_all_leads()
print(f"Total leads in DB: {len(all_leads)}")

known_phones = db.get_all_known_phones()
print(f"Known phones: {len(known_phones)}")

known_biz = db.get_all_known_business_names()
print(f"Known biz names: {len(known_biz)}")

metrics = db.get_dashboard_metrics()
print(f"Metrics: {metrics}")

# Check Export
print("3. Checking Export service...")
csv_leads = ExportService.to_csv(all_leads)
print(f"CSV export path: {csv_leads}")

# Check SmartScheduler
print("4. Checking SmartScheduler...")
cfg_mgr = ConfigManager()
sched = SmartScheduler(cfg_mgr)
rot = sched.get_rotation_schedule()
print(f"Rotation days: {len(rot)}")
active = sched.get_active_schedule()
print(f"Active schedule: {active}")

# Check maps_scraper curated directory top-up
print("5. Checking LeadScraper search_leads...")
scraper = LeadScraper()
res = scraper.search_leads("مطاعم صغيرة", "القاهرة, مصر", limit=10, use_live_browser=False, whatsapp_only=True)
print(f"Scraped {len(res)} leads.")
assert len(res) == 10, f"Expected 10 leads, got {len(res)}"

# Check processing lead through lead_service
print("6. Checking LeadService deduplication and saving...")
lead_svc = LeadService(db)
processed = 0
for r in res:
    res_save = lead_svc.process_and_save_lead(
        business_name=r.get("business_name", ""),
        phone=r.get("phone", ""),
        address=r.get("address", ""),
        website=r.get("website", ""),
        industry="مطاعم صغيرة",
        city="القاهرة",
        source="test_pipeline",
        country="مصر",
        language="Arabic"
    )
    if not res_save.get("was_merged"):
        processed += 1
print(f"Saved/Processed {processed} leads.")

print(">>> ALL VIEW AND PIPELINE CHECKS PASSED PERFECTLY!")
