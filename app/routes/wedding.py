from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Wedding

wedding_bp = Blueprint('wedding', __name__)


@wedding_bp.route('/dashboard')
@login_required
def dashboard():
    weddings = Wedding.query.filter_by(user_id=current_user.id).order_by(Wedding.created_at.desc()).all()
    return render_template('dashboard.html', weddings=weddings)
