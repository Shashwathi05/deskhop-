from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Device

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied."
    pending_devices = Device.query.filter_by(compliant=False).count()
    total_devices = Device.query.count()
    total_users = len({d.user_id for d in Device.query.all()})
    return render_template('admin_dashboard.html',
                           pending=pending_devices,
                           total=total_devices,
                           users=total_users)

@admin_bp.route('/devices')
@login_required
def view_devices():
    if not current_user.is_admin:
        return "Access denied."
    devices = Device.query.all()
    return render_template('admin_devices.html', devices=devices)

@admin_bp.route('/approve/<int:device_id>')
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied."
    device = Device.query.get(device_id)
    if device:
        device.compliant = True
        db.session.commit()
    return redirect(url_for('admin.view_devices'))
