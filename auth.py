from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Device

auth_bp = Blueprint('auth', __name__)

# ------------------------------
# REGISTER / SIGNUP
# ------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
@auth_bp.route('/signup', methods=['GET', 'POST'])  # Added alias for signup
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.", "danger")
            return redirect(url_for('auth.register'))

        hashed = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed, is_admin=False, is_approved=False)

        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully! Wait for admin approval.", "success")
        return redirect(url_for('auth.login'))

    # Render signup.html for GET request
    return render_template('signup.html')


# ------------------------------
# LOGIN (FULLY FIXED)
# ------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        # Invalid login
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for('auth.login'))

        # -------------------------
        # ADMIN LOGIN
        # -------------------------
        if user.is_admin:
            login_user(user)
            session['user_id'] = user.id
            flash("Admin login successful!", "success")
            return redirect(url_for('admin.dashboard'))

        # -------------------------
        # USER MUST BE APPROVED
        # -------------------------
        if not user.is_approved:
            flash("Your account is waiting for admin approval.", "warning")
            return redirect(url_for('auth.login'))

        # -------------------------
        # NOW CHECK DEVICE (BEFORE LOGIN)
        # -------------------------
        device = Device.query.filter_by(user_id=user.id)\
                             .order_by(Device.created_at.desc())\
                             .first()

        # No device registered
        if not device:
            flash("Please register your device first.", "info")
            return render_template('login.html')



        # Rejected device
        if device.status == "Rejected":
            login_user(user)
            session['user_id'] = user.id
            flash("Your previous device was rejected. Please re-register.", "warning")
            return redirect(url_for('byod.register_page'))

        # Pending device
        if device.status == "Pending":
            flash("Your device approval is pending.", "warning")
            return redirect(url_for('auth.login'))

        # -------------------------
        # DEVICE APPROVED
        # -------------------------
        login_user(user)
        session['user_id'] = user.id
        session['device_id'] = device.id

        flash("Login successful!", "success")
        return redirect(url_for('booking.dashboard'))

    return render_template('login.html')

# ------------------------------
# LOGOUT
# ------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('auth.login'))