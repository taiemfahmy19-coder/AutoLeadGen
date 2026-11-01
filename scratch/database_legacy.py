"""Backward compatibility shim for database.py."""
from database.repository import LeadRepository, ALLOWED_UPDATE_COLUMNS
from database.connection import get_raw_connection, DatabaseManager
from config.constants import *

# Legacy class alias
Database = LeadRepository