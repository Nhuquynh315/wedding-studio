from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


def utcnow():
    return datetime.now(timezone.utc)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


WEDDING_STYLES = ('rustic', 'modern', 'luxury', 'beach', 'vintage', 'minimalist')


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    weddings = db.relationship('Wedding', back_populates='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

    def set_password(self, password):
        """
        Set password by hashing it

        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if provided password matches the hash

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)


class Wedding(db.Model):
    """Wedding model storing planning details and AI-generated theme"""
    __tablename__ = 'weddings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    partner1_name = db.Column(db.String(120), nullable=False)
    partner2_name = db.Column(db.String(120), nullable=False)
    wedding_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    venue_name = db.Column(db.String(255), nullable=False)
    style = db.Column(db.String(20), nullable=False)
    primary_color = db.Column(db.String(20), nullable=False)
    secondary_color = db.Column(db.String(20), nullable=False)
    ai_generated_theme = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship('User', back_populates='weddings')
    guests = db.relationship('Guest', back_populates='wedding', lazy='dynamic')
    designs = db.relationship('Design', back_populates='wedding', lazy='dynamic')

    def __repr__(self):
        return f'<Wedding {self.partner1_name} & {self.partner2_name} on {self.wedding_date}>'


class Guest(db.Model):
    """Guest model for wedding attendee management"""
    __tablename__ = 'guests'

    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    group_name = db.Column(db.String(100), nullable=True)
    meal_preference = db.Column(db.String(100), nullable=True)
    rsvp_status = db.Column(db.String(20), nullable=False, default='pending')
    table_number = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding = db.relationship('Wedding', back_populates='guests')

    def __repr__(self):
        return f'<Guest {self.full_name} ({self.rsvp_status})>'


class Design(db.Model):
    """Design model for wedding invitation and thank-you card templates"""
    __tablename__ = 'designs'

    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    design_type = db.Column(db.String(50), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    pdf_file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding = db.relationship('Wedding', back_populates='designs')

    def __repr__(self):
        return f'<Design {self.design_type} for wedding {self.wedding_id}>'
