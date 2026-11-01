"""AutoLeadGen v2 - Database Package."""
from database.connection import get_raw_connection, DatabaseManager
from database.repository import LeadRepository, ALLOWED_UPDATE_COLUMNS
from database.backup_service import BackupService
from database.migrations import run_migrations

# Alias for backward compatibility
Database = LeadRepository
