import json
import logging
import hashlib
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from pathlib import Path

# Create logs directory
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_LOG_FILE = LOG_DIR / "audit_trail.jsonl"

class StructuredLogger:
    def __init__(self, name: str = "enterprise_ai"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _generate_checksum(self, record: dict) -> str:
        serialized = json.dumps(record, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def log_audit_event(
        self,
        event_type: str,
        user: str,
        role: str,
        action: str,
        resource: str,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        record = {
            "timestamp": timestamp,
            "event_type": event_type,
            "user": user,
            "role": role,
            "action": action,
            "resource": resource,
            "status": status,
            "request_id": request_id or hashlib.md5(f"{time.time()}_{user}".encode()).hexdigest()[:12],
            "details": details or {}
        }
        record["integrity_hash"] = self._generate_checksum(record)

        # Write to JSONL audit log
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to persist audit log: {e}")

        self.logger.info(f"AUDIT | {event_type} | {user} ({role}) -> {action} on {resource} [{status}]")
        return record

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        logs = []
        if not AUDIT_LOG_FILE.exists():
            return logs
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if line.strip():
                        logs.append(json.loads(line.strip()))
                    if len(logs) >= limit:
                        break
        except Exception as e:
            self.logger.error(f"Error reading audit logs: {e}")
        return logs

structured_logger = StructuredLogger()

