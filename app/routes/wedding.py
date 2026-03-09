from flask import Blueprint, render_template
from flask_login import login_required

wedding_bp = Blueprint('wedding', __name__)


@wedding_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
