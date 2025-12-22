import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.repositories.audit_repository import AuditRepository


class AuditService:

    def __init__(self):
        self.repository = AuditRepository()

    def log_create(
        self,
        entity_type: str,
        entity_id: int,
        new_values: Dict[str, Any],
        user_id: Optional[str],
        request_context: Dict[str, str]
    ):
        self._log(
            entity_type,
            entity_id,
            "CREATE",
            None,
            new_values,
            user_id,
            request_context
        )

    def log_update(
        self,
        entity_type: str,
        entity_id: int,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any],
        user_id: Optional[str],
        request_context: Dict[str, str]
    ):
        self._log(
            entity_type,
            entity_id,
            "UPDATE",
            old_values,
            new_values,
            user_id,
            request_context
        )

    def log_delete(
        self,
        entity_type: str,
        entity_id: int,
        old_values: Dict[str, Any],
        user_id: Optional[str],
        request_context: Dict[str, str]
    ):
        self._log(
            entity_type,
            entity_id,
            "DELETE",
            old_values,
            None,
            user_id,
            request_context
        )

    def _log(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]],
        user_id: Optional[str],
        request_context: Dict[str, str]
    ):
        audit_entry = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "old_values": json.dumps(old_values, default=str) if old_values else None,
            "new_values": json.dumps(new_values, default=str) if new_values else None,
            "user_id": user_id,
            "ip_address": request_context.get("ip_address"),
            "user_agent": request_context.get("user_agent"),
            "request_id": request_context.get("request_id"),
            "created_at": datetime.utcnow()
        }

        self.repository.create(audit_entry)
