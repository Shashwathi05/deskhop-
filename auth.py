# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from models import db, User, Device
from utils.logging import log_event
from utils.emailer import send_verification_email
from datetime import datetime

auth_bp = Blueprint("auth", __name__)

# token serializer (email verification)
serializer = URLSafeTimedSerializer("supersecretkey")


def generate_token(user_id):
    return serializer.dumps(user_id, salt="email-verify")


def verify_token(token, max_age=900):
    try:
        return serializer.loads(token, salt="email-verify", max_age=max_age)
    except Exception:
        return None


# -------------------------
# REGISTER / SIGNUP
# -------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/signup", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("Please fill all fields.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("auth.register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=False,
            is_verified=False,
            is_approved=False
        )
        db.session.add(new_user)
        db.session.commit()

        # send verification email
        token = generate_token(new_user.id)
        verify_url = url_for("auth.verify_email", token=token, _external=True)
        try:
            send_verification_email(email, verify_url)
        except Exception:
            # don't fail registration if email sending fails locally
            log_event("email_send_failed", user_id=new_user.id)

        flash("Registered! Check your email to verify your account.", "info")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


# -------------------------
# EMAIL VERIFICATION
# -------------------------
@auth_bp.route("/verify/<token>")
def verify_email(token):
    user_id = verify_token(token)
    if not user_id:
        flash("Verification link invalid or expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    db.session.commit()

    flash("Email verified! Wait for admin approval.", "success")
    return redirect(url_for("auth.login"))


# -------------------------
# LOGIN
# -------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # GET -> show form
    if request.method == "GET":
        return render_template("login.html")

    # POST -> process credentials + device fingerprint
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Missing username or password.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        log_event("login_failed", details=f"Invalid login for {username}")
        flash("Invalid credentials.", "danger")
        return redirect(url_for("auth.login"))

    # email verification + account approval checks
    if not user.is_verified:
        flash("Please verify your email before logging in.", "warning")
        return redirect(url_for("auth.login"))

    if user.is_admin:
        login_user(user)
        session["user_id"] = user.id
        log_event("admin_login", user_id=user.id)
        return redirect(url_for("admin.dashboard"))

    if not user.is_approved:
        flash("Account awaiting admin approval.", "warning")
        log_event("login_blocked_unapproved", user_id=user.id)
        return redirect(url_for("auth.login"))

    # --------------------------
    # DEVICE CHECK (fingerprint expected from client JS)
    # --------------------------
    # Expecting client to post the computed fingerprint + some helper fields
    device_fp = request.form.get("device_fp")
    device_userAgent = request.form.get("device_userAgent")
    device_platform = request.form.get("device_platform")
    device_cpuThreads = request.form.get("device_cpuThreads")
    device_screen = request.form.get("device_screen")
    device_timezone = request.form.get("device_timezone")

    if not device_fp:
        # If your client doesn't send fingerprint, deny and request proper client
        flash("Device fingerprint missing. Please log in from the supported client.", "danger")
        return redirect(url_for("auth.login"))

    # try to find device by fingerprint for this user
    device = Device.query.filter_by(user_id=user.id, fingerprint=device_fp).first()

    if not device:
        # first time this device logs in -> create pending device record
        new_device = Device(
            name=f"Device_{user.username}",
            os_version=device_platform,
            user_agent=device_userAgent,
            platform=device_platform,
            cpu_threads=device_cpuThreads or None,
            screen=device_screen,
            timezone=device_timezone,
            fingerprint=device_fp,
            ip_address=request.remote_addr,
            risk_score=5,
            status="Pending",
            compliant=False,
            user_id=user.id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_device)
        db.session.commit()

        login_user(user)
        session["user_id"] = user.id

        flash("New device detected. Registration submitted and awaiting admin approval.", "warning")
        log_event("device_auto_registered_pending", user_id=user.id, device_id=new_device.id)
        return redirect(url_for("byod.register_page"))

    # device exists → check status
    if device.status == "Pending":
        login_user(user)
        session["user_id"] = user.id
        session["device_id"] = device.id
        flash("Device approval pending from admin.", "info")
        return redirect(url_for("byod.register_page"))

    if device.status == "Rejected":
        flash("This device has been rejected by admin. Please register again.", "danger")
        log_event("login_device_rejected", user_id=user.id, device_id=device.id)
        return redirect(url_for("byod.register_page"))

    # APPROVED device
    login_user(user)
    session["user_id"] = user.id
    session["device_id"] = device.id
    log_event("login_success", user_id=user.id, device_id=device.id)
    return redirect(url_for("booking.dashboard"))


# -------------------------
# LOGOUT
# -------------------------
@auth_bp.route("/logout")
@login_required
def logout():
    log_event("logout", user_id=current_user.id)
    logout_user()
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("auth.login"))
