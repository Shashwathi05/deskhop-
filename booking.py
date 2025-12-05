from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, current_app, session
from flask_login import login_required, current_user
from models import db, Booking, User
from datetime import datetime
import os
from utils.logging import log_event


booking_bp = Blueprint('booking', __name__, url_prefix='/booking')

# ------------- UI views for Deskhop flow --------------
@booking_bp.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date.desc(), Booking.timeslot).all()
    return render_template('booking.html', bookings=bookings)


@booking_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        date = request.form.get('date')
        slot = request.form.get('slot')
        return redirect(url_for('booking.floor_page', floor_id=1, date=date, slot=slot))
    return render_template('booking_select.html')


@booking_bp.route('/floor/<int:floor_id>')
@login_required
def floor_page(floor_id):
    date = request.args.get('date')
    slot = request.args.get('slot')

    # choose filename (static files must be placed exactly under static/floors/)
    filename = f"floor{floor_id}.html"
    static_path = os.path.join(current_app.root_path, 'static', 'floors')
    file_path = os.path.join(static_path, filename)

    if not os.path.exists(file_path):
        return f"Floor file not found: {filename}", 404
        

    # read the static floor HTML (unchanged) and pass as safe HTML into wrapper
    with open(file_path, 'r', encoding='utf-8') as fh:
        floor_html = fh.read()

    print("SERVING FLOOR HTML FROM:", file_path)
    

    return render_template("floor_wrapper.html",
                           date=date,
                           slot=slot,
                           floor=floor_id,
                           floor_html=floor_html)


# ------------- Internal API (used by floor.html loader) --------------
@booking_bp.route('/api/desks')
@login_required
def api_desks():
    date = request.args.get('date')
    slot = request.args.get('slot')
    floor = request.args.get('floor', type=int) or 1
    if not date or not slot:
        return jsonify({}), 400

    rows = Booking.query.filter_by(date=date, timeslot=slot, floor=floor).all()
    out = {}
    for r in rows:
        out[str(r.desk_number)] = {"user_id": r.user_id, "booking_id": r.id}
    return jsonify(out), 200


@booking_bp.route('/api/book', methods=['POST'])
@login_required
def api_book():
    data = request.get_json() or {}
    desk = data.get('desk') or data.get('desk_number') or data.get('deskId')
    # HONEYPOT DETECTION
    if str(desk).startswith("HP"):
        from utils.logging import log_event
        log_event(
             "honeypot_triggered",
            user_id=current_user.id,
            device_id=session.get("device_id"),
            details=f"User attempted to book hidden desk {desk}"
            )
        return jsonify({"error": "This desk cannot be booked."}), 403

    date = data.get('date')
    slot = data.get('slot')
    floor = int(data.get('floor') or 1)

    if not desk or not date or not slot:
        return jsonify({"error": "missing desk/date/slot"}), 400

    # Prevent desk double-book
    exists = Booking.query.filter_by(desk_number=str(desk), date=date, timeslot=slot, floor=floor).first()
    if exists:
        return jsonify({"error": "Desk already booked for this date+slot"}), 409

    # Prevent user multiple bookings same date+slot
    user_conflict = Booking.query.filter_by(user_id=current_user.id, date=date, timeslot=slot).first()
    if user_conflict:
        return jsonify({"error": "You already have a booking for this date and slot"}), 409

    b = Booking(
    user_id=current_user.id,
    desk_number=str(desk),
    date=date,
    timeslot=slot,
    floor=floor,
    status="Upcoming"
)

    db.session.add(b)
    db.session.commit()
    return jsonify({"ok": True, "booking_id": b.id}), 201


# ------------- Compatibility public API routes (for original friend's UI) --------------
# GET mapping for booked desks used by original UI
@booking_bp.route("/api/bookings")
def get_bookings():
    date = request.args.get("date")
    slot = request.args.get("slot")
    floor = request.args.get("floor", type=int)

    rows = Booking.query.filter_by(
        date=date,
        timeslot=slot,
        floor=floor
    ).all()

    result = {}
    for b in rows:
        result[b.desk_number] = {
            "name": b.user.username if hasattr(b.user, "username") else str(b.user_id),
            "user_id": b.user_id,
            "slot": b.timeslot,
            "floor": b.floor
        }
    return jsonify(result)




# POST to create booking (compat API)
@booking_bp.route('/api/bookings', methods=['POST'])
@login_required
def compat_create_booking():
    payload = request.get_json() or {}
    desk = payload.get('desk') or payload.get('desk_number') or payload.get('deskId')
    date = payload.get('date')
    slot = payload.get('slot')
    floor = int(payload.get('floor') or 1)

    if not desk or not date or not slot:
        return jsonify({"error": "missing fields"}), 400

    # If front-end sent "name" and user is not logged in — we require login => but we enforce current_user
    # Prevent double-booking
    exists = Booking.query.filter_by(desk_number=str(desk), date=date, timeslot=slot, floor=floor).first()
    if exists:
        return jsonify({"error": "Desk already booked"}), 409

    conflict = Booking.query.filter_by(user_id=current_user.id, date=date, timeslot=slot).first()
    if conflict:
        return jsonify({"error": "You already booked a desk for that slot"}), 409

    b = Booking(
    user_id=current_user.id,
    desk_number=str(desk),
    date=date,
    timeslot=slot,
    floor=floor,
    status="Upcoming"
)

    db.session.add(b)
    db.session.commit()
    return jsonify({"ok": True, "booking_id": b.id}), 201


@booking_bp.route('/api/bookings/<desk_id>', methods=['DELETE'])
@login_required
def compat_delete_booking(desk_id):
    date = request.args.get('date')
    slot = request.args.get('slot')
    floor = request.args.get('floor', type=int) or None

    q = Booking.query.filter_by(desk_number=str(desk_id))
    if date:
        q = q.filter_by(date=date)
    if slot:
        q = q.filter_by(timeslot=slot)
    if floor:
        q = q.filter_by(floor=floor)

    b = q.first()
    if not b:
        return jsonify({"error": "Booking not found"}), 404

    # Only allow cancelling by booking owner or admin
    if b.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Not allowed"}), 403

    db.session.delete(b)
    db.session.commit()
    return jsonify({"ok": True}), 200

# ------------------------------------------------------------
# MY BOOKINGS VIEW
# ------------------------------------------------------------
@booking_bp.route('/mybookings')
@login_required
def mybookings():
    # only show bookings that are not completed (Upcoming or Active)
    rows = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status.in_(["Upcoming", "Active"])
    ).order_by(Booking.date.asc(), Booking.timeslot.asc()).all()

    # optional: you can still show completed bookings on a separate page if needed
    return render_template('mybookings.html', bookings=rows)



# ------------------------------------------------------------
# START BOOKING → Redirect to prepare_session
# ------------------------------------------------------------
@booking_bp.route('/start/<int:booking_id>')
@login_required
def start_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)

    if b.user_id != current_user.id:
        return "Not allowed.", 403

    return redirect(url_for('booking.prepare_session', booking_id=booking_id))


# ------------------------------------------------------------
# PREPARE SESSION
# ------------------------------------------------------------
@booking_bp.route('/prepare_session/<int:booking_id>')
@login_required
def prepare_session(booking_id):
    session['current_booking_id'] = booking_id
    return render_template("start_session.html", booking_id=booking_id)


# ------------------------------------------------------------
# START SESSION (enter workspace)
# ------------------------------------------------------------
@booking_bp.route('/start_session/<int:booking_id>')
@login_required
def start_session(booking_id):
    b = Booking.query.get_or_404(booking_id)

    # SECURITY: user must own booking
    if b.user_id != current_user.id:
        return "Not allowed.", 403

    # Booking must be upcoming
    if b.status != "Upcoming":
        flash("Session already started or completed.", "warning")
        return redirect(url_for("booking.dashboard"))

    # Mark active
    b.status = "Active"
    b.session_start = datetime.utcnow()
    db.session.commit()

    

    return redirect(url_for('booking.fullscreen_workspace', booking_id=booking_id))


# ------------------------------------------------------------
# WORKSPACE PAGE
# ------------------------------------------------------------
@booking_bp.route('/fullscreen_workspace/<int:booking_id>')
@login_required
def fullscreen_workspace(booking_id):
    return render_template("workspace.html", booking_id=booking_id)


# ------------------------------------------------------------
# PAUSE SESSION
# ------------------------------------------------------------
@booking_bp.route('/pause_session/<int:booking_id>')
@login_required
def pause_session(booking_id):
    log_event(
    "session_pause",
    user_id=current_user.id,
    device_id=session.get("device_id"),
    details=request.args.get("reason") or "manual_pause"
)
    return redirect(url_for("booking.resume_auth", booking_id=booking_id))


# ------------------------------------------------------------
# RESUME AUTH PAGE
# ------------------------------------------------------------
@booking_bp.route('/resume_auth/<int:booking_id>', methods=["GET", "POST"])
@login_required
def resume_auth(booking_id):
    if request.method == "POST":
        password = request.form.get("password")

        from werkzeug.security import check_password_hash

        if not check_password_hash(current_user.password_hash, password):
            log_event(
                "resume_auth_failed",
                user_id=current_user.id,
                device_id=session.get("device_id"),
                details="incorrect_password"
            )
            flash("Incorrect password.", "danger")
            return redirect(url_for("booking.resume_auth", booking_id=booking_id))

        # SUCCESSFUL RESUME
        log_event(
            "session_resume",
            user_id=current_user.id,
            device_id=session.get("device_id"),
            details="resume_auth_success"
        )

        return redirect(url_for("booking.fullscreen_workspace", booking_id=booking_id))

    return render_template("resume_auth.html", booking_id=booking_id)

@booking_bp.route('/api/log_event', methods=['POST'])
@login_required
def api_log_event():
    data = request.get_json() or {}
    from utils.logging import log_event
    log_event(
        data.get("event"),
        user_id=current_user.id,
        device_id=session.get("device_id"),
        details=data.get("details")
    )
    return {"ok": True}, 200

# ------------------------------------------------------------
# END SESSION
# ------------------------------------------------------------
@booking_bp.route('/end_session/<int:booking_id>')
@login_required
def end_session(booking_id):
    b = Booking.query.get_or_404(booking_id)

    if b.user_id != current_user.id:
        return "Not allowed.", 403

    if b.status != "Active":
        flash("Session not active.", "danger")
        return redirect(url_for("booking.dashboard"))

    b.status = "Completed"
    b.session_end = datetime.utcnow()

    db.session.commit()

    # remove session variables
    session.pop("active_session", None)
    session.pop("session_start", None)

    flash("Session completed.", "success")
    return redirect(url_for("booking.dashboard"))
