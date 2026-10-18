import getpass
import json

from db import get_connection
from models import AuditLog


class AuditRepository:
    def __init__(self, conn_func=get_connection):
        self.conn_func = conn_func

    def log_change(self, cur, table_name, record_id, action, old_value, new_value, changed_by=None):
        if old_value == new_value:
            return
        actor = str(changed_by or getpass.getuser()).strip()
        if not actor:
            raise ValueError("The name of the person making the change is required.")
        cur.execute(
            "INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (table_name, str(record_id), action,
             json.dumps(old_value, sort_keys=True) if old_value is not None else None,
             json.dumps(new_value, sort_keys=True) if new_value is not None else None, actor),
        )

    def find_all(self):
        conn = self.conn_func()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT log_id, table_name, record_id, action, old_value, new_value, "
                    "changed_by, changed_at FROM audit_log ORDER BY log_id"
                )
                return [AuditLog(*row) for row in cur.fetchall()]
        finally:
            conn.close()
