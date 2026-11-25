"""AutoLeadGen V3 — User Management & Authentication Service."""
from typing import Optional, Dict, Any

from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    has_permission,
)
from database.repository import LeadRepository
from utils.logger import info, warning


class UserManager:
    def __init__(self, repo: Optional[LeadRepository] = None):
        self.repo = repo or LeadRepository()

    def has_any_users(self) -> bool:
        return self.repo.count_users() > 0

    def create_user(
        self,
        username: str,
        plain_password: str,
        role: str = "operator",
        email: str = "",
    ) -> Dict[str, Any]:
        username = (username or "").strip()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if role not in ("admin", "operator", "viewer"):
            raise ValueError("Invalid role. Must be admin, operator, or viewer.")
        if self.repo.get_user_by_username(username):
            raise ValueError(f"User '{username}' already exists.")

        pw_hash = hash_password(plain_password)
        user_id = self.repo.create_user(username=username, email=email, password_hash=pw_hash, role=role)
        self.repo.insert_audit_log("USER_CREATED", f"Created user '{username}' with role '{role}'")
        return {"id": user_id, "username": username, "email": email, "role": role}

    def authenticate_user(self, username: str, plain_password: str) -> Optional[Dict[str, Any]]:
        user = self.repo.get_user_by_username(username)
        if not user or not user.get("is_active", 1):
            return None
        if not verify_password(plain_password, user["password_hash"]):
            return None
        self.repo.update_user_last_login(user["id"])
        token = create_access_token(user_id=user["id"], username=user["username"], role=user["role"])
        self.repo.insert_audit_log("USER_LOGIN", f"User '{user['username']}' logged in")
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
            "role": user["role"],
            "access_token": token,
        }

    def ensure_default_admin(self) -> bool:
        """Create default admin if DB has zero users (first-run bootstrap)."""
        if self.has_any_users():
            return False
        self.create_user("admin", "admin123", role="admin", email="admin@autoleadgen.local")
        warning("V3 Bootstrap: Created default admin account ('admin' / 'admin123'). Please change password immediately!")
        info("Default admin account ready.")
        return True

    def check_permission(self, role: str, permission: str) -> bool:
        return has_permission(role, permission)
