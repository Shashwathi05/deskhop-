from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, Booking, Device, User

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/dashboard')
@login_required
def dashboard():
    deviceid = session.get('deviceid')
    device = Device.query.get(deviceid)
    if not device or not device.compliant:
        return "Device not approved. Cannot book desk."
    bookings = Booking.query.filter_by(userid=current_user.id).all()
    return render_template('dashboard.html', bookings=bookings)

@booking_bp.route('/book', methods=['POST'])
@login_required
def book():
    if current_user.isadmin:
        return "Admins cannot book desks."
    deviceid = session.get('deviceid')
    device = Device.query.get(deviceid)
    if not device or not device.compliant:
        return "Device not approved. Cannot book desk."
    desknumber = request.form['desknumber']
    date = request.form['date']
    newbooking = Booking(userid=current_user.id, desknumber=desknumber, date=date)
    db.session.add(newbooking)
    db.session.commit()
    return redirect(url_for('booking.dashboard'))
