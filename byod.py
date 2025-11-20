from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Device, User
import hashlib
from datetime import datetime

byod_bp = Blueprint('byod', __name__, url_prefix='/device')

def calc_fingerprint(payload: dict) -> str:
    raw = (
        (payload.get('userAgent') or '') +
        (payload.get('platform') or '') +
        str(payload.get('cpuThreads') or '') +
        (payload.get('screen') or '') +
        (payload.get('timezone') or '')
    )
    return hashlib.sha256(raw.encode()).hexdigest()

def risk_score_from(payload: dict) -> int:
    score = 0
    ua = (payload.get('userAgent') or '').lower()

    if "headless" in ua or "phantom" in ua or "selenium" in ua:
        score += 50

    try:
        cpu = int(payload.get('cpuThreads') or 0)
    except:
        cpu = 0

    screen = payload.get('screen') or ''
    if screen:
        try:
            w, h = map(int, screen.split('x'))
            if w <= 800 or h <= 600:
                score += 10
        except:
            pass

    if cpu <= 1:
        score += 10
    if payload.get('timezone') in (None, '', 'UTC'):
        score += 5
    if "msie" in ua or "trident" in ua:
        score += 10

    return score


# -----------------------
# DEVICE REGISTER
# -----------------------
# byod.py - REVISED
@byod_bp.route('/register', methods=['POST'])
@login_required
def register_device():
    # ✅ Remove the approval check - let users register devices even if not approved yet
    # The admin will approve both together
    
    payload = request.get_json() or {}
    ip = request.remote_addr
    fp = calc_fingerprint(payload)
    score = risk_score_from(payload)

    # Check if device with this fingerprint already exists for this user
    existing = Device.query.filter_by(user_id=current_user.id, fingerprint=fp).first()
    
    if existing:
        # Update existing device and reset to Pending if it was rejected
        existing.user_agent = payload.get('userAgent')
        existing.platform = payload.get('platform')
        existing.cpu_threads = payload.get('cpuThreads')
        existing.screen = payload.get('screen')
        existing.timezone = payload.get('timezone')
        existing.ip_address = ip
        existing.risk_score = score
        existing.status = "Pending"  # Always reset to pending
        existing.compliant = False
        existing.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"status": "updated", "device_id": existing.id})

    # Create new device
    d = Device(
        name=payload.get('name') or f"Device_{current_user.id}",
        os_version=payload.get('osVersion') or payload.get('platform'),
        user_agent=payload.get('userAgent'),
        platform=payload.get('platform'),
        cpu_threads=payload.get('cpuThreads'),
        screen=payload.get('screen'),
        timezone=payload.get('timezone'),
        fingerprint=fp,
        ip_address=ip,
        compliant=False,
        status='Pending',
        risk_score=score,
        user_id=current_user.id
    )
    db.session.add(d)
    db.session.commit()
    return jsonify({"status": "created", "device_id": d.id})


@byod_bp.route('/register_page')
@login_required
def register_page():
    return render_template('device_register.html')



@byod_bp.route('/admin_list')
@login_required
def admin_list():
    if not current_user.is_admin:
          return "Access denied", 403
    devices = Device.query.order_by(Device.id.desc()).all()
    return render_template('admin_device_list.html', devices=devices)


@byod_bp.route('/approve/<int:device_id>', methods=['POST'])
@login_required
def admin_approve(device_id):
    if not current_user.is_admin:
        return "Access denied", 403
    device = Device.query.get_or_404(device_id)
    device.compliant = True
    device.status = 'Approved'
    db.session.commit()
    flash(f"Device {device.name or device.id} approved.", "success")
    return redirect(url_for('admin.dashboard'))


@byod_bp.route('/reject/<int:device_id>', methods=['POST'])
@login_required
def admin_reject(device_id):
    if not current_user.is_admin:
        return "Access denied", 403
    device = Device.query.get_or_404(device_id)
    device.status = 'Rejected'
    device.compliant = False
    db.session.commit()
    flash(f"Device {device.name or device.id} rejected.", "warning")
    return redirect(url_for('admin.dashboard'))


