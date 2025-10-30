from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Device, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403

    pending_users = User.query.filter_by(is_approved=False).all()
    pending_devices = Device.query.filter_by(compliant=False).all()
    total_users = User.query.count()
    total_devices = Device.query.count()

    return render_template(
        'admin_dashboard.html',
        users=total_users,
        total=total_devices,
        pending_users=pending_users,
        devices=pending_devices
    )

@admin_bp.route('/approve_user/<int:user_id>')
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return "Access denied", 403
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f"Approved user {user.username}", "success")
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/approve_device/<int:device_id>')
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403
    device = Device.query.get_or_404(device_id)

    # Example compliance checks
    if device.antivirus_installed and "Windows 10" in device.os_version:
        device.compliant = True
        db.session.commit()
        flash(f"Device {device.name} approved.", "success")
    else:
        flash("Device does not meet compliance requirements.", "error")

    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/pending_users')
@login_required
def pending_users():
    if not current_user.is_admin:
        return "Access denied", 403

    users = User.query.filter_by(is_approved=False).all()
    return render_template('pending_users.html', users=users)


@admin_bp.route('/devices')
@login_required
def view_devices():
    if not current_user.is_admin:
        return "Access denied", 403
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)
