from flask import Blueprint

compliance_bp = Blueprint("compliance", __name__)

@compliance_bp.route("/compliance")
def check_device():
    return "Device compliance check will go here ✅"
