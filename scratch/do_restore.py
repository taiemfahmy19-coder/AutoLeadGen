import os
import shutil
import traceback

local_scratch = r"d:\AI feed\AutoLeadGen\scratch"
brain_scratch = r"C:\Users\taiem\.gemini\antigravity\brain\f258fb07-25b0-4983-bd13-c80d0fa68f57\scratch"

print("--- Running Sep 17 Restoration ---")

# 1. app.py
shutil.copyfile(os.path.join(local_scratch, "app_sep17_replayed.py"), "app.py")
print("SUCCESS: app.py")

# 2. search_view.py
with open(os.path.join(brain_scratch, "write_search_view.py"), "r", encoding="utf-8") as f:
    text = f.read()
code_start = text.find("CODE = '''") + len("CODE = '''")
code_end = text.rfind("'''")
with open("ui/views/search_view.py", "w", encoding="utf-8") as f:
    f.write(text[code_start:code_end])
print("SUCCESS: ui/views/search_view.py")

# 3. settings_view.py
with open(os.path.join(brain_scratch, "write_settings.py"), "r", encoding="utf-8") as f:
    text = f.read()
code_start = text.find("CODE = '''") + len("CODE = '''")
code_end = text.rfind("'''")
with open("ui/views/settings_view.py", "w", encoding="utf-8") as f:
    f.write(text[code_start:code_end])
print("SUCCESS: ui/views/settings_view.py")

# 4. dashboard_view.py
shutil.copyfile(os.path.join(local_scratch, "dashboard_view_sep17_replayed.py"), "ui/views/dashboard_view.py")
print("SUCCESS: ui/views/dashboard_view.py")

# 5. ui/views/__init__.py
shutil.copyfile(os.path.join(local_scratch, "ui_views___init__.py_sep17.py"), "ui/views/__init__.py")
print("SUCCESS: ui/views/__init__.py")

# 6. maps_scraper.py
shutil.copyfile(os.path.join(local_scratch, "maps_scraper_sep17.py"), "integrations/maps_scraper.py")
print("SUCCESS: integrations/maps_scraper.py")

# 7. database/repository.py
shutil.copyfile(os.path.join(local_scratch, "database_repository.py_sep17.py"), "database/repository.py")
print("SUCCESS: database/repository.py")

# 8. config/constants.py
shutil.copyfile(os.path.join(local_scratch, "config_constants.py_sep17.py"), "config/constants.py")
print("SUCCESS: config/constants.py")

# 9. Delete files added after Sep 17
files_to_delete = [
    "core/config_manager.py",
    "core/system_controller.py",
    "core/scheduler.py",
    "core/deduplication.py",
    "ui/views/lead_discovery_protection_view.py",
    "ui/views/leads_view.py",
    "tests/test_config_manager.py",
    "tests/test_system_controller.py",
    "tests/test_crm_lifecycle.py",
    "tests/test_smart_scheduler.py",
    "data/app_config.json",
]

for rel_f in files_to_delete:
    if os.path.exists(rel_f):
        try:
            os.remove(rel_f)
            print("DELETED:", rel_f)
        except Exception as e:
            print("FAILED DELETING:", rel_f, e)

print("--- Restoration Complete! ---")
