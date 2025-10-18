from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, Booking, Device
from datetime import datetime

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/dashboard')
@login_required
def dashboard():
    device_id = session.get('device_id')
    device = Device.query.get(device_id)

    if not device or not device.compliant:
        return "🚫 Access denied. Unapproved device."

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', bookings=bookings)

@booking_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book_desk():
    device_id = session.get('device_id')
    device = Device.query.get(device_id)

    if not device or not device.compliant:
        return "🚫 Cannot book desk. Device not approved."

    if request.method == 'POST':
        desk_number = request.form['desk_number']
        date_str = request.form['booking_date']  # "YYYY-MM-DD"
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        new_booking = Booking(
            user_id=current_user.id,
            desk_number=desk_number,
            booking_date=booking_date,
            device_id=device.id
        )
        db.session.add(new_booking)
        db.session.commit()
        return redirect(url_for('booking.dashboard'))

    return render_template('book_desk.html')
