from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, Booking

booking_bp = Blueprint("booking", __name__)

@booking_bp.route("/dashboard")
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", bookings=bookings)

@booking_bp.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "POST":
        desk_number = request.form["desk_number"]
        date = request.form["date"]
        booking = Booking(user_id=current_user.id, desk_number=desk_number, date=date)
        db.session.add(booking)
        db.session.commit()
        return redirect(url_for("booking.dashboard"))
    return render_template("booking.html")
