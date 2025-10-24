from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Device, User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403
    users = User.query.count()
    total = Device.query.count()
    devices = Device.query.filter_by(compliant=False).all()
    return render_template('admin_dashboard.html', users=users, total=total, devices=devices)


@admin_bp.route('/approve/<int:device_id>')
@login_required
def approve_device(device_id):
    if not current_user.is_admin:
        return "Access denied", 403
    
    device = Device.query.get_or_404(device_id)
    device.compliant = True
    db.session.commit()
    return redirect(url_for('admin.dashboard'))



@admin_bp.route('/devices')
@login_required
def view_devices():
    if not current_user.is_admin:
        return "Access denied", 403
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)
