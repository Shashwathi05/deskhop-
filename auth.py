from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Device
import platform
import psutil
import socket

auth_bp = Blueprint('auth', __name__)

# ===================== SIGNUP =====================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return redirect(url_for('auth.signup'))  # silently return if exists

        # Hash password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Create user (pending approval)
        new_user = User(username=username, password_hash=hashed_password, is_approved=False)
        db.session.add(new_user)
        db.session.commit()

        # Register device (pending approval)
        os_version = f"{platform.system()} {platform.release()}"
        ip_address = socket.gethostbyname(socket.gethostname())

        new_device = Device(
            name=f"{username}'s Device",
            os_version=os_version,
            antivirus_installed=True,
            compliant=False,  # admin must approve
            user_agent=request.headers.get('User-Agent'),
            ip_address=ip_address,
            user_id=new_user.id
        )

        db.session.add(new_device)
        db.session.commit()

        # After signup just go back to login (no messages)
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


# ===================== LOGIN =====================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        # Validate user existence
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('login.html')

        # Check if admin approved user
        if not user.is_approved:
            return render_template('login.html')

        # Log user in
        login_user(user)
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin

        # Device handling
        useragent = request.headers.get('User-Agent')
        ip = request.remote_addr
        device = Device.query.filter_by(user_id=user.id, user_agent=useragent).first()
        is_compliant = check_compliance()

        if not device:
            device = Device(
                user_id=user.id,
                user_agent=useragent,
                ip_address=ip,
                compliant=False  # needs admin approval
            )
            db.session.add(device)
            db.session.commit()
        else:
            device.compliant = is_compliant
            db.session.commit()

        session['device_id'] = device.id

        # Admin shortcut
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))

        # If device not approved → block login
        if not device.compliant:
            return render_template('device_not_approved.html')

        # Normal user goes to dashboard
        return redirect(url_for('booking.dashboard'))

    return render_template('login.html')


# ===================== COMPLIANCE CHECK =====================
def check_compliance():
    os_ok = platform.system() in ["Windows", "Linux", "Darwin"]
    mem_ok = psutil.virtual_memory().total > 2 * 1024 * 1024 * 1024  # at least 2GB RAM
    return os_ok and mem_ok


# ===================== LOGOUT =====================
@auth_bp.route('/logout')
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))
