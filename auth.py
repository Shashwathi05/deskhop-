from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user
from werkzeug.security import check_password_hash
from models import db, User, Device
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for('auth.signup'))
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=False,
            is_approved=False
        )
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully. Waiting for admin approval.", "info")
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        print("🧩 Attempting login for:", username)

        if not user:
            flash("Invalid username.", "danger")
            return render_template('login.html')

        if not check_password_hash(user.password_hash, password):
            flash("Invalid password.", "danger")
            return render_template('login.html')

        if not user.is_approved:
            flash("Your account has not been approved by admin yet.", "warning")
            return render_template('login.html')

        # Login the user
        login_user(user)
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin

        # BYOD Device Registration and Compliance Check
        useragent = request.headers.get('User-Agent')
        ip = request.remote_addr
        device = Device.query.filter_by(user_id=user.id, user_agent=useragent).first()

        if not device:
            device = Device(user_id=user.id, user_agent=useragent, ip_address=ip, compliant=False)
            db.session.add(device)
            db.session.commit()

        session['deviceid'] = device.id

        # Admin shortcut — skip compliance
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))

        # BYOD compliance check for normal users
        if not device.compliant:
            return render_template('device_not_approved.html')

        return redirect(url_for('booking.dashboard'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('auth.login'))
