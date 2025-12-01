# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    emp_id = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    devices = db.relationship('Device', back_populates='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    os_version = db.Column(db.String(100))
    antivirus_installed = db.Column(db.Boolean, default=False)
    compliant = db.Column(db.Boolean, default=False)
    user_agent = db.Column(db.String(300))
    ip_address = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', back_populates='devices')

    fingerprint = db.Column(db.String(128), unique=False, nullable=True)
    platform = db.Column(db.String(80), nullable=True)
    cpu_threads = db.Column(db.String(20), nullable=True)
    screen = db.Column(db.String(40), nullable=True)
    timezone = db.Column(db.String(80), nullable=True)
    risk_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    desk_number = db.Column(db.String(80), nullable=False)

    date = db.Column(db.String(20), nullable=False)
    timeslot = db.Column(db.String(30), nullable=False)

    floor = db.Column(db.Integer, nullable=False, default=1)

    status = db.Column(db.String(20), default="Upcoming")   # <-- UPDATED
    session_start = db.Column(db.DateTime, nullable=True)  # <-- NEW
    session_end = db.Column(db.DateTime, nullable=True)    # <-- NEW

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='bookings', lazy=True)



class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=True)
    event = db.Column(db.String(80), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs', lazy=True)
    device = db.relationship('Device', backref='activity_logs', lazy=True)

    def __repr__(self):
        return f"<ActivityLog {self.event} user={self.user_id} device={self.device_id}>"
