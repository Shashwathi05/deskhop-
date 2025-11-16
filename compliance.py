from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Device

compliance_bp = Blueprint('compliance', __name__)

@compliance_bp.route('/devices')
@login_required
def list_devices():
    if not current_user.is_admin:
        return "Access denied", 403
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@compliance_bp.route('/approve/<int:device_id>')
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403

    device = Device.query.get_or_404(device_id)
    user = device.user

    device.compliant = True
    db.session.commit()

    # auto-approve user if not approved
    if not user.is_approved:
        user.is_approved = True
        db.session.commit()

    flash(f"✅ Device {device.name or device.id} approved successfully!", "success")
    return redirect(url_for('compliance.list_devices'))
