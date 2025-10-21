from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Device

compliance_bp = Blueprint('compliance', __name__)

@compliance_bp.route('/devices')
@login_required
def list_devices():
    if not current_user.is_admin:
        return "Access denied."
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@compliance_bp.route('/approve/<int:device_id>')
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied."
    device = Device.query.get(device_id)
    if device:
        device.compliant = True
        db.session.commit()
    return redirect(url_for('compliance.list_devices'))
