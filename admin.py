from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Device, ActivityLog, Booking
from utils.logging import log_event
import pytz

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ------------------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------------------
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403

    # Pending users & devices
    users = User.query.filter_by(is_approved=False).all()
    pending_devices = Device.query.filter(Device.status != "Approved").all()
    approved_devices = Device.query.filter_by(status="Approved") \
                                   .order_by(Device.user_id, Device.id).all()

    honeypot_count = ActivityLog.query.filter_by(event="honeypot_triggered").count()
    resume_failures = ActivityLog.query.filter_by(event="resume_auth_failed").count()
    idle_pauses = ActivityLog.query.filter_by(event="session_pause").count()

    # Top 5 risky devices
    risky_devices = Device.query.order_by(Device.risk_score.desc()).limit(5).all()

    analytics = {
        "honeypot": honeypot_count,
        "resume_failures": resume_failures,
        "idle_pauses": idle_pauses,
        "risky_devices": risky_devices
    }

    # Return template with analytics included
    return render_template(
        "admin_dashboard.html",
        users=users,
        pending_devices=pending_devices,
        approved_devices=approved_devices,
        analytics=analytics
    )


# ------------------------------------------------------------
# APPROVE USER
# ------------------------------------------------------------
@admin_bp.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    log_event("user_approved", user_id=user.id, details=f"Admin {current_user.username} approved user")
    flash(f"User '{user.username}' approved.", "success")
    return redirect(url_for('admin.dashboard'))


# ------------------------------------------------------------
# REJECT USER (simple delete)
# ------------------------------------------------------------
@admin_bp.route('/reject_user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("User rejected & removed.", "danger")
    return redirect(url_for('admin.dashboard'))


# ------------------------------------------------------------
# FULL USER DELETE (NUKE USER)
# ------------------------------------------------------------
@admin_bp.route('/nuke_user/<int:user_id>', methods=['POST'])
@login_required
def nuke_user(user_id):
    if not current_user.is_admin:
        return "Forbidden", 403

    user = User.query.get_or_404(user_id)

    # delete logs
    ActivityLog.query.filter_by(user_id=user.id).delete()

    # delete bookings
    Booking.query.filter_by(user_id=user.id).delete()

    # delete devices
    Device.query.filter_by(user_id=user.id).delete()

    # delete user
    db.session.delete(user)
    db.session.commit()

    flash("User, devices, bookings & logs permanently removed.", "danger")
    return redirect(url_for("admin.dashboard"))


# ------------------------------------------------------------
# APPROVE DEVICE
# ------------------------------------------------------------
@admin_bp.route('/approve_device/<int:device_id>', methods=['POST'])
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    device.status = "Approved"
    device.compliant = True
    db.session.commit()

    flash(f"Device '{device.name}' approved.", "success")
    return redirect(url_for('admin.dashboard'))


# ------------------------------------------------------------
# REJECT DEVICE
# ------------------------------------------------------------
@admin_bp.route('/reject_device/<int:device_id>', methods=['POST'])
@login_required
def reject_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    device.status = "Rejected"
    device.compliant = False
    db.session.commit()

    flash("Device rejected.", "danger")
    return redirect(url_for('admin.dashboard'))


# ------------------------------------------------------------
# DEVICE LOG VIEW
# ------------------------------------------------------------
@admin_bp.route('/device_logs/<int:device_id>')
@login_required
def device_logs(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    import pytz
    ist = pytz.timezone("Asia/Kolkata")

    device = Device.query.get_or_404(device_id)
    logs = ActivityLog.query.filter_by(device_id=device_id).order_by(ActivityLog.created_at.desc()).all()

    # Convert timestamps to IST
    for log in logs:
        if log.created_at:
            log.local_time = log.created_at.astimezone(ist)

    # Alerts (keep your logic)
    from datetime import datetime, timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    alerts = []

    fails = ActivityLog.query.filter(
        ActivityLog.device_id == device_id,
        ActivityLog.event == "resume_auth_failed",
        ActivityLog.created_at >= one_hour_ago
    ).count()
    if fails >= 3:
        alerts.append({"text": f"{fails} failed resume attempts last hour."})

    pauses = ActivityLog.query.filter(
        ActivityLog.device_id == device_id,
        ActivityLog.event == "session_pause",
        ActivityLog.created_at >= one_hour_ago
    ).count()
    if pauses >= 5:
        alerts.append({"text": f"{pauses} pauses last hour."})

    return render_template("device_logs.html", device=device, logs=logs, alerts=alerts)


# ------------------------------------------------------------
# DELETE DEVICE (simple delete)
# ------------------------------------------------------------
@admin_bp.route("/device/delete/<int:device_id>", methods=["POST"])
@login_required
def delete_device_admin(device_id):
    if not current_user.is_admin:
        return "Forbidden", 403

    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()

    flash("Device deleted.", "success")
    return redirect(url_for("admin.dashboard"))


