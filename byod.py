# byod.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Device
from utils.logging import log_event
import hashlib
import re
from datetime import datetime

byod_bp = Blueprint("byod", __name__, url_prefix="/device")


# -------------------------
# calc_fingerprint(payload)
# JS registration collects userAgent, platform, cpuThreads, screen, timezone
# This must match client-side concatenation exactly.
# -------------------------
def calc_fingerprint(payload):
    ua = (payload.get("userAgent") or "").lower()
    platform = (payload.get("platform") or "").lower()

    # Normalise mobile platform noise
    if "android" in ua:
        platform = "android"
    if "iphone" in ua or "ios" in ua:
        platform = "ios"

    # Normalise screen to just aspect ratio (avoid DP variations)
    screen = payload.get("screen") or ""
    try:
        w, h = map(int, screen.split("x"))
        ratio = round(w/h, 2)
    except:
        ratio = "unknown"

    # Normalise timezone (mobile changes it sometimes)
    tz = payload.get("timezone") or ""
    if tz.upper() in ["UTC", ""]:
        tz = "unstable"

    # CPU threads on phones fluctuate → ignore it
    raw = "|".join([
        ua,
        platform,
        str(ratio),
        tz
    ])

    return hashlib.sha256(raw.encode()).hexdigest()


# -------------------------
# Register device (client sends JSON)
@byod_bp.route("/register", methods=["POST"])
@login_required
def register_device():
    payload = request.get_json() or {}
    ip = request.remote_addr

    # compute fingerprint and risk
    fp = calc_fingerprint(payload)
    score = risk_score_from(payload)

    try:
        # If there's an existing device with same fingerprint, update it
        existing = Device.query.filter_by(user_id=current_user.id, fingerprint=fp).first()
        if existing:
            # preserve Approved if already approved
            if existing.status == "Approved":
                return jsonify({"status": "already_approved", "device_id": existing.id}), 200

            existing.name = payload.get("name") or existing.name
            existing.os_version = payload.get("osVersion") or existing.os_version
            existing.user_agent = payload.get("userAgent")
            existing.platform = payload.get("platform")
            existing.cpu_threads = payload.get("cpuThreads")
            existing.screen = payload.get("screen")
            existing.timezone = payload.get("timezone")
            existing.ip_address = ip
            existing.risk_score = score
            existing.status = "Pending"
            existing.compliant = False
            existing.updated_at = datetime.utcnow()

            db.session.commit()
            log_event("device_register_update", user_id=current_user.id, device_id=existing.id)
            return jsonify({"status": "updated", "device_id": existing.id}), 200

        # If a very recent device was created by this user (same IP) within the last few seconds,
        # treat the new request as an "update" to avoid duplicates caused by double-posts.
        recent = Device.query.filter_by(user_id=current_user.id).order_by(Device.created_at.desc()).first()
        if recent:
            try:
                age = (datetime.utcnow() - recent.created_at).total_seconds() if recent.created_at else 9999
            except Exception:
                age = 9999
            if recent.ip_address == ip and age < 5:
                # update the recent record instead of creating a new one
                recent.name = payload.get("name") or recent.name
                recent.os_version = payload.get("osVersion") or recent.os_version
                recent.user_agent = payload.get("userAgent")
                recent.platform = payload.get("platform")
                recent.cpu_threads = payload.get("cpuThreads")
                recent.screen = payload.get("screen")
                recent.timezone = payload.get("timezone")
                recent.fingerprint = fp or recent.fingerprint
                recent.risk_score = score
                recent.status = "Pending"
                recent.compliant = False
                recent.ip_address = ip
                recent.updated_at = datetime.utcnow()
                db.session.commit()
                log_event("device_register_dedup", user_id=current_user.id, device_id=recent.id)
                return jsonify({"status": "dedup_updated", "device_id": recent.id}), 200

        # create new device record (Pending) — allow multiple devices per user
        d = Device(
            name=payload.get("name") or f"Device_{current_user.id}",
            os_version=payload.get("osVersion") or payload.get("platform"),
            user_agent=payload.get("userAgent"),
            platform=payload.get("platform"),
            cpu_threads=payload.get("cpuThreads"),
            screen=payload.get("screen"),
            timezone=payload.get("timezone"),
            fingerprint=fp,
            ip_address=ip,
            risk_score=score,
            status="Pending",
            compliant=False,
            user_id=current_user.id,
            created_at=datetime.utcnow()
        )

        db.session.add(d)
        db.session.commit()
        log_event("device_registered", user_id=current_user.id, device_id=d.id)
        return jsonify({"status": "created", "device_id": d.id}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "server_error", "detail": str(e)}), 500


# -------------------------
# Register page - shows latest device status
# -------------------------
@byod_bp.route("/register_page")
@login_required
def register_page():
    devices = Device.query.filter_by(user_id=current_user.id).order_by(Device.created_at.desc()).all()
    return render_template("device_register.html", devices=devices)


# -------------------------
# Admin approve / reject
# -------------------------
@byod_bp.route("/approve/<int:device_id>", methods=["POST"])
@login_required
def admin_approve(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    device.status = "Approved"
    device.compliant = True
    device.updated_at = datetime.utcnow()
    db.session.commit()

    log_event("device_approved", user_id=device.user_id, device_id=device.id)
    flash("Device approved.", "success")
    return redirect(url_for("admin.dashboard"))


@byod_bp.route("/reject/<int:device_id>", methods=["POST"])
@login_required
def admin_reject(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    device.status = "Rejected"
    device.compliant = False
    device.updated_at = datetime.utcnow()
    db.session.commit()

    log_event("device_rejected", user_id=device.user_id, device_id=device.id)
    flash("Device rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@byod_bp.route('/delete/<int:device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    d = Device.query.get_or_404(device_id)
    # allow owner or admin to delete
    if d.user_id != current_user.id and not current_user.is_admin:
        return "Not allowed", 403
    db.session.delete(d)
    db.session.commit()
    flash("Device removed.", "success")
    return redirect(url_for('byod.register_page'))
