from flask import Flask, render_template
from flask_login import LoginManager
from models import db, User
from auth import auth_bp
from booking import booking_bp
from compliance import compliance_bp
from resources import resources_bp
from admin import admin_bp   


app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///deskhop.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("base.html")

# ✅ Register all blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(booking_bp, url_prefix="/booking")
app.register_blueprint(compliance_bp, url_prefix="/device")
app.register_blueprint(resources_bp, url_prefix="/resources")
app.register_blueprint(admin_bp, url_prefix="/admin")  # 👈 this one’s new!

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
