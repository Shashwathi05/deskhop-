from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user
from werkzeug.security import check_password_hash
from models import db, User, Device

auth_bp = Blueprint('auth', __name__)

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
            device = Device.query.filter_by(user_id=user.id, user_agent=user_agent, ip_address=ip_address).first()
            if not device:
                # New device = not compliant
                device = Device(user_id=user.id, user_agent=user_agent, ip_address=ip_address, compliant=False)
                db.session.add(device)
                db.session.commit()

            # Zero Trust check
            if not device.compliant:
                return "⚠️ Device not approved. Please contact admin."

            login_user(user)
            session['device_id'] = device.id
            return redirect(url_for('booking.dashboard'))

        return "Invalid username or password."
    return render_template('login.html')
