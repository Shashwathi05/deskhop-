from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    emp_id = db.Column(db.String(50))
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    devices = db.relationship('Device', back_populates='user', cascade="all, delete-orphan")

    # Add these ↓↓↓
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
    # inside Device model (models.py), add these fields to the class definition:
    fingerprint = db.Column(db.String(128), unique=False, nullable=True)
    platform = db.Column(db.String(80), nullable=True)
    cpu_threads = db.Column(db.String(20), nullable=True)
    screen = db.Column(db.String(40), nullable=True)       # e.g. "1920x1080"
    timezone = db.Column(db.String(80), nullable=True)
    risk_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default='Pending')    # Pending / Approved / Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    desk_number = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Booked')
