from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Booking
from datetime import date

booking_bp = Blueprint('booking', __name__)


# ---------------------------------------------------------
# DASHBOARD (Shows all bookings)
# ---------------------------------------------------------
@booking_bp.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date.desc()).all()
    return render_template('dashboard.html', bookings=bookings)


# ---------------------------------------------------------
# BOOK A DESK
# ---------------------------------------------------------
@booking_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        desk_number = request.form.get('desk_number')
        selected_date = request.form.get('date')

        new_booking = Booking(
            user_id=current_user.id,
            desk_number=desk_number,
            date=selected_date,
            status="Booked"
        )

        db.session.add(new_booking)
        db.session.commit()

        flash("Desk booked successfully!", "success")
        return redirect(url_for('booking.dashboard'))

    return render_template('booking.html')


# ---------------------------------------------------------
# ACCESS RESOURCES (Check for booked desks)
# ---------------------------------------------------------
@booking_bp.route('/resources')
@login_required
def resources():
    booking = Booking.query.filter_by(
        user_id=current_user.id,
        status="Booked"
    ).order_by(Booking.date.asc()).first()

    return render_template('resources.html', booking=booking)


# ---------------------------------------------------------
# STEP 1: PRE-SESSION PAGE
# ---------------------------------------------------------
@booking_bp.route('/prepare_session/<int:booking_id>')
@login_required
def prepare_session(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        return "Not your booking.", 403

    return render_template('start_session.html', booking=booking)


# ---------------------------------------------------------
# STEP 2: START SESSION IN FULLSCREEN
# ---------------------------------------------------------
@booking_bp.route('/fullscreen_workspace/<int:booking_id>')
@login_required
def fullscreen_workspace(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        return "Not your booking.", 403

    session['isolated'] = True
    session['booking_id'] = booking_id  # IMPORTANT: save booking ID

    booking.status = "In Use"
    db.session.commit()

    return render_template('workspace.html', booking=booking)


# ---------------------------------------------------------
# STEP 3: END SESSION
# ---------------------------------------------------------
@booking_bp.route('/end_session')
@login_required
def end_session():
    booking_id = session.get('booking_id')

    if booking_id:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.status = "Completed"
            db.session.commit()

    session.clear()
    flash("Session ended successfully.", "info")
    return redirect(url_for('booking.dashboard'))
