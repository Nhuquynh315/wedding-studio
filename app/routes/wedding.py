from flask import Blueprint

wedding_bp = Blueprint('wedding', __name__)


@wedding_bp.route('/dashboard')
def dashboard():
    pass
