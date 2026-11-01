"""AutoLeadGen v2 - Application Settings and System Paths."""
import os

PROJECT_NAME = "AutoLeadGen & AI Advertising Outreach Suite"
VERSION = "2.0.0"

# Directories & Files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "leads.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
WHATSAPP_PROFILE_DIR = os.path.join(DATA_DIR, "whatsapp_profile")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Ensure all essential directories exist
for folder in [DATA_DIR, BACKUP_DIR, WHATSAPP_PROFILE_DIR, LOG_DIR]:
    os.makedirs(folder, exist_ok=True)

# UI Settings
PAGE_TITLE = "AutoLeadGen"
PAGE_ICON = "🎯"
PORT = 8501
URL = f"http://localhost:{PORT}"
