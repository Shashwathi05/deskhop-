from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Device

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/devices")
@login_required
def devices():
    if not current_user.is_admin:
        return "Access denied"
    pending_devices = Device.query.filter_by(compliant=False).all()
    return render_template("admin_devices.html", devices=pending_devices)

@admin_bp.route("/approve_device/<int:device_id>")
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied"
    device = Device.query.get(device_id)
    if device:
        device.compliant = True
        db.session.commit()
    return redirect(url_for("admin.devices"))
