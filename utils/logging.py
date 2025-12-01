from flask import request, current_app
from models import db, ActivityLog
from datetime import datetime

def log_event(event: str, user_id=None, device_id=None, details=None, ip=None):
    """
    Log event to ActivityLog table.
    Keep calls small and consistent:
      log_event("session_pause", user_id=current_user.id, device_id=dev.id, details="fullscreen escape")
    """
    try:
        ip_addr = ip or (request.remote_addr if request else None)
    except Exception:
        ip_addr = None

    entry = ActivityLog(
        user_id=user_id,
        device_id=device_id,
        event=event,
        details=details,
        ip_address=ip_addr,
        created_at=datetime.utcnow()
    )
    db.session.add(entry)
    db.session.commit()
    return entry
