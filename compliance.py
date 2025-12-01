from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Device

compliance_bp = Blueprint('compliance', __name__, url_prefix='/compliance')

# -----------------------------------
# DEVICE LIST FOR ADMINS (READ ONLY)
# -----------------------------------
@compliance_bp.route('/devices')
@login_required
def list_devices():
    if not current_user.is_admin:
        return "Access denied", 403

    devices = Device.query.order_by(Device.id.desc()).all()
    return render_template('devices.html', devices=devices)

# -----------------------------------
# USER VIEW: SEE THEIR OWN DEVICES
# -----------------------------------
@compliance_bp.route('/my_devices')
@login_required
def my_devices():
    devices = Device.query.filter_by(user_id=current_user.id).order_by(Device.id.desc()).all()
    return render_template('my_devices.html', devices=devices)
