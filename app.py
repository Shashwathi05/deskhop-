from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user
from models import db, User
from auth import auth_bp
from booking import booking_bp
from compliance import compliance_bp
from werkzeug.security import generate_password_hash
import os
from byod import byod_bp
# ---------------------------------------------------
# APP INITIALIZATION
# ---------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deskhop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database setup
db.init_app(app)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# ---------------------------------------------------
# USER LOADER
# ---------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------
# ROOT ROUTE
# ---------------------------------------------------
@app.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("booking.dashboard"))
    return redirect(url_for("auth.login"))

# ---------------------------------------------------
# BLUEPRINT REGISTRATION
# ---------------------------------------------------
# Register all blueprints here (import admin inside function to avoid circular import)
def register_blueprints(app):
    from admin import admin_bp  # moved import here to break circular import
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(booking_bp, url_prefix="/booking")
    app.register_blueprint(byod_bp)
    app.register_blueprint(compliance_bp, url_prefix="/device")
       # prefix already configured in blueprint


register_blueprints(app)

# ---------------------------------------------------
# DB INIT & DEFAULT ADMIN
# ---------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()


        # Default admin auto-setup
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                is_admin=True,
                is_approved=True,
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin created: username='admin', password='admin123'")
        else:
            print("✅ Admin user already exists!")

        # Pending approvals log
        pending_users = User.query.filter_by(is_approved=False).all()
        if pending_users:
            print("\n🕒 Pending User Approvals:")
            for u in pending_users:
                print(f" - {u.username}")
        else:
            print("\n✅ No pending user approvals.")

    print("📁 Database path:", os.path.abspath("deskhop.db"))
    app.run(debug=True)
