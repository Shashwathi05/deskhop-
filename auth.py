from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Device

auth_bp = Blueprint('auth', __name__)

# ------------------------------
# REGISTER
# ------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists.", "danger")
            return redirect(url_for('auth.register'))

        hashed = generate_password_hash(password)

        new_user = User(
            username=username,
            password_hash=hashed,
            is_admin=False,
            is_approved=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registered successfully! Wait for admin approval.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ------------------------------
# LOGIN
# ------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Invalid username.", "danger")
            return redirect(url_for('auth.login'))

        if not check_password_hash(user.password_hash, password):
            flash("Incorrect password.", "danger")
            return redirect(url_for('auth.login'))

        if not user.is_approved:
            flash("Your account is waiting for admin approval.", "warning")
            return redirect(url_for('auth.login'))

        login_user(user)
        session['user_id'] = user.id

        # Admin login redirect
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))

        # Device check
        approved_device = Device.query.filter_by(
            user_id=user.id,
            compliant=True,
            status="Approved"
        ).first()

        if not approved_device:
            pending = Device.query.filter_by(user_id=user.id).filter(Device.status != "Approved").first()

            if pending:
                flash("Your device approval is pending.", "info")
                return redirect(url_for('booking.dashboard'))

            return redirect(url_for('byod.register_page'))

        session['device_id'] = approved_device.id

        flash("Login successful!", "success")
        return redirect(url_for('booking.dashboard'))

    return render_template('login.html')


# ------------------------------
# SIGNUP (Alternative)
# ------------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed = generate_password_hash(password)

        new_user = User(
            username=username,
            password_hash=hashed,
            is_approved=False
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! Wait for admin approval.", "success")
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


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
