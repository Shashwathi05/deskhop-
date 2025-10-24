from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import db, User, Device

auth_bp = Blueprint('auth', __name__)

# -----------------------------
# LOGIN ROUTE
# -----------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr

            # Check if device exists
            device = Device.query.filter_by(user_id=user.id, user_agent=user_agent).first()
            if not device:
                # New device
                device = Device(user_id=user.id, user_agent=user_agent, ip_address=ip_address)
                if user.is_admin:
                    device.compliant = True  # Auto-approve admin devices
                else:
                    device.compliant = False
                db.session.add(device)
                db.session.commit()

            # If device not approved and user is not admin
            if not device.compliant and not user.is_admin:
                return render_template('device_not_approved.html')  # show warning page

            login_user(user)
            session['device_id'] = device.id
            return redirect(url_for('booking.dashboard'))

        return "Invalid username or password."
    return render_template('login.html')

# -----------------------------
# SIGNUP ROUTE
# -----------------------------
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists."

        # Create new user
        user = User(username=username, password_hash=generate_password_hash(password), is_admin=False)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('signup.html')



@auth_bp.route('/logout')
def logout():
    from flask_login import logout_user
    logout_user()
    session.pop('device_id', None)
    return redirect(url_for('auth.login'))
