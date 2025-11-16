from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Device, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --------------------------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------------------------
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403

    # Pending users
    users = User.query.filter_by(is_approved=False).all()

    # Pending + Rejected devices (anything not Approved)
    devices = Device.query.filter(Device.status != "Approved").all()

    return render_template("admin_dashboard.html", users=users, devices=devices)

# --------------------------------------------------------------------
# APPROVE USER
# --------------------------------------------------------------------
@admin_bp.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403

    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()

    flash(f"User '{user.username}' approved.", "success")
    return redirect(url_for('admin.dashboard'))

# --------------------------------------------------------------------
# REJECT USER
# --------------------------------------------------------------------
@admin_bp.route('/reject_user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("User rejected.", "danger")
    return redirect(url_for('admin.dashboard'))

# --------------------------------------------------------------------
# APPROVE DEVICE
# --------------------------------------------------------------------
@admin_bp.route('/approve_device/<int:device_id>', methods=['POST'])
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    device.status = "Approved"
    device.compliant = True
    db.session.commit()

    flash(f"Device '{device.name or device.id}' approved.", "success")
    return redirect(url_for('admin.dashboard'))

# --------------------------------------------------------------------
# REJECT DEVICE
# --------------------------------------------------------------------
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
