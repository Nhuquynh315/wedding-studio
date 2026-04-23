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
    full_name            = db.Column(db.String(200), nullable=False)
    avatar_color         = db.Column(db.String(7),  nullable=False, default='#c9687a')
    phone                = db.Column(db.String(50), nullable=True)
    timezone             = db.Column(db.String(50), nullable=False, default='UTC')
    email_notifications  = db.Column(db.Boolean,    nullable=False, default=True)
    updated_at           = db.Column(db.DateTime,   nullable=True)
    created_at           = db.Column(db.DateTime,   default=utcnow, nullable=False)

    weddings = db.relationship('Wedding', back_populates='user', cascade='all, delete-orphan')

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
    rsvp_contact = db.Column(db.String(255), nullable=True)
    total_budget = db.Column(db.Float, nullable=True, default=None)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = db.relationship('User', back_populates='weddings')
    guests            = db.relationship('Guest',          back_populates='wedding', cascade='all, delete-orphan')
    designs           = db.relationship('Design',         back_populates='wedding', cascade='all, delete-orphan')
    checklist_items   = db.relationship('ChecklistItem',  back_populates='wedding', cascade='all, delete-orphan')
    budget_categories = db.relationship('BudgetCategory', back_populates='wedding', cascade='all, delete-orphan')
    expenses          = db.relationship('Expense',        back_populates='wedding', cascade='all, delete-orphan')
    vendors           = db.relationship('Vendor',         back_populates='wedding', cascade='all, delete-orphan')
    wedding_tables    = db.relationship('WeddingTable',   back_populates='wedding', cascade='all, delete-orphan')

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
    rsvp_status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'confirmed', 'declined'
    table_number = db.Column(db.Integer, nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('wedding_tables.id'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding = db.relationship('Wedding', back_populates='guests')
    seating_table = db.relationship('WeddingTable', back_populates='guests', foreign_keys=[table_id])

    def __repr__(self):
        return f'<Guest {self.full_name} ({self.rsvp_status})>'


CHECKLIST_CATEGORIES = (
    'Venue', 'Catering', 'Attire', 'Photography', 'Flowers',
    'Music', 'Stationery', 'Transport', 'Honeymoon', 'Other',
)
CHECKLIST_PRIORITIES = ('low', 'medium', 'high')


class ChecklistItem(db.Model):
    """Checklist/timeline item for a wedding."""
    __tablename__ = 'checklist_items'

    id           = db.Column(db.Integer, primary_key=True)
    wedding_id   = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    title        = db.Column(db.String(200), nullable=False)
    category     = db.Column(db.String(50), default='Other')
    due_date     = db.Column(db.Date, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    priority     = db.Column(db.String(20), default='medium')
    notes        = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding = db.relationship('Wedding', back_populates='checklist_items')

    def __repr__(self):
        return f'<ChecklistItem {self.title!r} ({self.category})>'


class BudgetCategory(db.Model):
    """A named budget category with an allocated amount for a wedding."""
    __tablename__ = 'budget_categories'

    id               = db.Column(db.Integer, primary_key=True)
    wedding_id       = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    name             = db.Column(db.String(100), nullable=False)
    allocated_amount = db.Column(db.Float, default=0)
    color            = db.Column(db.String(7), default='#c9687a')
    created_at       = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding  = db.relationship('Wedding',  back_populates='budget_categories')
    expenses = db.relationship('Expense',  back_populates='category', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BudgetCategory {self.name!r} ${self.allocated_amount}>'


class Expense(db.Model):
    """An individual expense line item belonging to a wedding budget category."""
    __tablename__ = 'expenses'

    id             = db.Column(db.Integer, primary_key=True)
    wedding_id     = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    category_id    = db.Column(db.Integer, db.ForeignKey('budget_categories.id'), nullable=True, index=True)
    vendor_id      = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True, index=True)
    title          = db.Column(db.String(200), nullable=False)
    estimated_cost = db.Column(db.Float, default=0)
    actual_cost    = db.Column(db.Float, nullable=True)
    is_paid        = db.Column(db.Boolean, default=False, nullable=False)
    paid_date      = db.Column(db.Date, nullable=True)
    due_date       = db.Column(db.Date, nullable=True)
    notes          = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding  = db.relationship('Wedding',        back_populates='expenses')
    category = db.relationship('BudgetCategory', back_populates='expenses')
    vendor   = db.relationship('Vendor',         back_populates='expenses')

    def __repr__(self):
        return f'<Expense {self.title!r} ${self.estimated_cost}>'


VENDOR_CATEGORIES = (
    'Venue', 'Catering', 'Photography', 'Videography', 'Flowers',
    'Music', 'Hair & Makeup', 'Transport', 'Cake', 'Stationery',
    'Officiant', 'Other',
)
VENDOR_STATUSES = ('considering', 'booked', 'rejected', 'backup')


class Vendor(db.Model):
    """A vendor/supplier being considered or booked for a wedding."""
    __tablename__ = 'vendors'

    id                   = db.Column(db.Integer, primary_key=True)
    wedding_id           = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    category             = db.Column(db.String(50), nullable=False, default='Other')
    business_name        = db.Column(db.String(200), nullable=False)
    contact_name         = db.Column(db.String(200), nullable=True)
    email                = db.Column(db.String(200), nullable=True)
    phone                = db.Column(db.String(50),  nullable=True)
    website              = db.Column(db.String(300), nullable=True)
    quoted_price         = db.Column(db.Float,  nullable=True)
    deposit_amount       = db.Column(db.Float,  nullable=True)
    deposit_paid         = db.Column(db.Boolean, default=False, nullable=False)
    deposit_due_date     = db.Column(db.Date, nullable=True)
    contracted           = db.Column(db.Boolean, default=False, nullable=False)
    contract_signed_date = db.Column(db.Date, nullable=True)
    contract_url         = db.Column(db.String(500), nullable=True)
    rating               = db.Column(db.Integer, nullable=True)
    notes                = db.Column(db.Text, nullable=True)
    status                 = db.Column(db.String(20), default='considering', nullable=False)
    final_payment_amount   = db.Column(db.Float,   nullable=True)
    final_payment_paid     = db.Column(db.Boolean, default=False, nullable=False)
    final_payment_due_date = db.Column(db.Date,    nullable=True)
    created_at             = db.Column(db.DateTime, default=utcnow, nullable=False)

    wedding  = db.relationship('Wedding', back_populates='vendors')
    expenses = db.relationship('Expense', back_populates='vendor')

    def to_dict(self):
        return {
            'id':                      self.id,
            'business_name':           self.business_name,
            'category':                self.category,
            'contact_name':            self.contact_name or '',
            'email':                   self.email or '',
            'phone':                   self.phone or '',
            'website':                 self.website or '',
            'quoted_price':            self.quoted_price or '',
            'deposit_amount':          self.deposit_amount or '',
            'deposit_due_date':        self.deposit_due_date.strftime('%Y-%m-%d') if self.deposit_due_date else '',
            'final_payment_amount':    self.final_payment_amount if self.final_payment_amount is not None else '',
            'final_payment_due_date':  self.final_payment_due_date.strftime('%Y-%m-%d') if self.final_payment_due_date else '',
            'contracted':              self.contracted,
            'contract_signed_date':    self.contract_signed_date.strftime('%Y-%m-%d') if self.contract_signed_date else '',
            'contract_url':            self.contract_url or '',
            'status':                  self.status or 'considering',
            'rating':                  self.rating or 0,
            'notes':                   self.notes or '',
        }

    def __repr__(self):
        return f'<Vendor {self.business_name!r} ({self.category})>'


class WeddingTable(db.Model):
    """A physical table at the wedding venue for seating arrangement."""
    __tablename__ = 'wedding_tables'

    id           = db.Column(db.Integer, primary_key=True)
    wedding_id   = db.Column(db.Integer, db.ForeignKey('weddings.id'), nullable=False, index=True)
    table_number = db.Column(db.Integer, nullable=False)
    table_name   = db.Column(db.String(100), nullable=True)
    capacity     = db.Column(db.Integer, default=8, nullable=False)
    shape        = db.Column(db.String(20), default='round', nullable=False)
    position_x   = db.Column(db.Float, nullable=True)
    position_y   = db.Column(db.Float, nullable=True)
    notes        = db.Column(db.Text, nullable=True)

    wedding = db.relationship('Wedding', back_populates='wedding_tables')
    guests  = db.relationship('Guest', back_populates='seating_table',
                              foreign_keys='Guest.table_id')

    def display_name(self):
        return self.table_name or f'Table {self.table_number}'


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
