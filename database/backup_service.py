"""AutoLeadGen v2 - Native SQLite Backup and Restore Service using SQLite Online Backup API."""
import os
import sqlite3
from datetime import datetime
from config.settings import DB_PATH, BACKUP_DIR
from utils.logger import info, error


class BackupService:
    def __init__(self, db_path=DB_PATH, backup_dir=BACKUP_DIR):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, custom_name: str = None) -> str:
        """
        Create a 100% consistent online snapshot of SQLite database using native backup API.
        Never causes file corruption or locks active queries.
        """
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found at: {self.db_path}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = custom_name or f"leads_{timestamp}.db"
        if not filename.endswith(".db"):
            filename += ".db"

        backup_path = os.path.join(self.backup_dir, filename)

        try:
            # Use SQLite native backup API
            src = sqlite3.connect(self.db_path)
            dst = sqlite3.connect(backup_path)
            with dst:
                src.backup(dst, pages=100)
            dst.close()
            src.close()
            info(f"Backup created successfully: {backup_path}")
            return backup_path
        except Exception as e:
            error(f"Failed to create SQLite backup: {e}")
            raise

    def list_backups(self) -> list[dict]:
        """List all backups sorted newest first."""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for fname in os.listdir(self.backup_dir):
            if fname.endswith(".db"):
                full_path = os.path.join(self.backup_dir, fname)
                try:
                    stat = os.stat(full_path)
                    backups.append({
                        "name": fname,
                        "path": full_path,
                        "size_kb": round(stat.st_size / 1024, 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })
                except Exception:
                    pass

        backups.sort(key=lambda x: x["modified"], reverse=True)
        return backups

    def restore_backup(self, backup_filename_or_path: str) -> bool:
        """
        Restore database from a selected backup using native online backup API.
        Takes a safety snapshot first.
        """
        if os.path.isabs(backup_filename_or_path):
            backup_path = backup_filename_or_path
        else:
            backup_path = os.path.join(self.backup_dir, backup_filename_or_path)

        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Selected backup does not exist: {backup_path}")

        # Safety snapshot
        if os.path.exists(self.db_path):
            safety_name = f"pre_restore_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.db"
            self.create_backup(safety_name)

        try:
            src = sqlite3.connect(backup_path)
            dst = sqlite3.connect(self.db_path)
            with dst:
                src.backup(dst, pages=100)
            dst.close()
            src.close()
            info(f"Database restored successfully from: {backup_path}")
            return True
        except Exception as e:
            error(f"Failed to restore database: {e}")
            raise
