from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    emp_id = db.Column(db.String(50))
    is_approved = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    devices = db.relationship('Device', backref='owner', lazy=True)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    os_version = db.Column(db.String(100))
    antivirus_installed = db.Column(db.Boolean, default=False)
    compliant = db.Column(db.Boolean, default=False)
    user_agent = db.Column(db.String(300))
    ip_address = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    desk_number = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Booked')
