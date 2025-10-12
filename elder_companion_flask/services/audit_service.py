from flask import g, jsonify
from datetime import datetime
from sqlalchemy.orm import Session
import json
from ..models import AuditLog, ActionEnum, TableNameEnum

def create_audit_log(
        db: Session, 
        elderly_id: str, 
        table_name: TableNameEnum, 
        old_data: dict, 
        new_data: dict, 
        action: ActionEnum
    ):

    try: 
        # Track changes
        changes = {}
        if action == ActionEnum.add:
            changes = {key: {"old": None, "new": value} for key, value in new_data.items()}
        elif action == ActionEnum.update:
            for key, new_val in new_data.items():
                old_val = (old_data or {}).get(key)
                if old_val != new_val:
                    changes[key] = {"old": old_val, "new": new_val}

        # For DEBUG:
        # print(f"Changes: {changes}")

        audit_entry = AuditLog(
            user_id=g.get('user_id'),
            elderly_id=elderly_id,
            table_name=table_name,
            action=action,
            changes=json.dumps(changes),
        )

        db.add(audit_entry)
        ## Do not db commit here in case parent transaction fails
    except Exception as e:
        print("Audit log creation failed:", e)
        raise
