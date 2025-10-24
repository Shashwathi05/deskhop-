from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from models import db, Booking, Device, User

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/dashboard')
@login_required
def dashboard():
    # If the logged-in user is an admin, show admin dashboard
    if current_user.is_admin:
        devices = Device.query.all()
        users = User.query.all()
        bookings = Booking.query.all()
        return render_template('admin_dashboard.html', devices=devices, users=users, bookings=bookings)
    
    # Otherwise normal user dashboard logic
    device_id = session.get('device_id')
    device = Device.query.get(device_id)
    if not device or not device.compliant:
        return "⚠️ Device not approved. Cannot book desk."

    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', bookings=bookings)

@booking_bp.route('/book', methods=['POST'])
@login_required
def book():
    if current_user.is_admin:
        return "Admins can't book desks. 😤"

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
