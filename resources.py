from flask import Blueprint

resources_bp = Blueprint("resources", __name__)

@resources_bp.route("/resources")
def resources():
    return "Office resources access will go here 🔒"
