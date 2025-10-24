from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Device
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)

            # if admin, auto-approved
            if user.is_admin:
                return redirect(url_for('booking.dashboard'))
            
            # normal user device check
            device = Device.query.filter_by(user_id=user.id).first()
            if not device:
                flash("Device not registered! Contact admin.")
                return redirect(url_for('auth.login'))
            if not device.compliant:
                flash("Device not approved by admin yet!")
                return redirect(url_for('auth.login'))

            return redirect(url_for('booking.dashboard'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return "Username already exists."

        user = User(username=username, password_hash=generate_password_hash(password), is_admin=False)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('auth.login'))
