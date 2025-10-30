from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Device

compliance_bp = Blueprint('compliance', __name__)

@compliance_bp.route('/devices')
@login_required
def list_devices():
    if not current_user.isadmin:
        return "Access denied", 403
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@compliance_bp.route('/approve/<int:deviceid>')
@login_required
def approve_device(deviceid):
    if not current_user.isadmin:
        return "Access denied", 403
    device = Device.query.get(deviceid)
    device.compliant = True
    db.session.commit()
    return redirect(url_for('compliance.list_devices'))
