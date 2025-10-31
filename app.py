from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
from auth import auth_bp
from booking import booking_bp
from compliance import compliance_bp
from resources import resources_bp
from admin import admin_bp
from werkzeug.security import generate_password_hash
import os

# Just for sanity check
print("🗂 DB path:", os.path.abspath("deskhop.db"))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deskhop.db'

# Initialize database
db.init_app(app)

# Initialize login manager
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Load user callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("base.html")

# ✅ Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(admin_bp, url_prefix="/admin") 
app.register_blueprint(booking_bp, url_prefix="/booking")
app.register_blueprint(compliance_bp, url_prefix="/device")
app.register_blueprint(resources_bp, url_prefix="/resources")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # ✅ Create default admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_approved=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✨ Default admin created: username='admin', password='admin123'")
        else:
            print("✅ Admin user already exists!")

        # (Optional) Show pending users and devices for debugging
        pending_users = User.query.filter_by(is_approved=False).all()
        if pending_users:
            print("\n🚫 Pending User Approvals:")
            for u in pending_users:
                print(f" - {u.username}")
        else:
            print("\n✅ No pending user approvals.")

    # Start Flask app
    app.run(debug=True)
