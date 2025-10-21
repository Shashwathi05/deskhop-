from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, Booking, Device

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/dashboard')
@login_required
def dashboard():
    device_id = session.get('device_id')
    device = Device.query.get(device_id)
    if not device or not device.compliant:
        return "⚠️ Device not approved. Cannot book desk."

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', bookings=bookings)

@booking_bp.route('/book', methods=['POST'])
@login_required
def book():
    device_id = session.get('device_id')
    device = Device.query.get(device_id)
    if not device or not device.compliant:
        return "⚠️ Device not approved. Cannot book desk."

    desk_number = request.form['desk_number']
    date = request.form['date']

    new_booking = Booking(user_id=current_user.id, desk_number=desk_number, date=date)
    db.session.add(new_booking)
    db.session.commit()
    return redirect(url_for('booking.dashboard'))
