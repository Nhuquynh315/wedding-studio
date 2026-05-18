from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    return datetime.now(UTC)


WEDDING_STYLES = ("rustic", "modern", "luxury", "beach", "vintage", "minimalist")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    avatar_color = Column(String(7), nullable=False, default="#c9687a")
    phone = Column(String(50), nullable=True)
    timezone = Column(String(50), nullable=False, default="UTC")
    email_notifications = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    weddings = relationship("Wedding", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Wedding(Base):
    __tablename__ = "weddings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    partner1_name = Column(String(120), nullable=False)
    partner2_name = Column(String(120), nullable=False)
    wedding_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)
    venue_name = Column(String(255), nullable=False)
    style = Column(String(20), nullable=False)
    primary_color = Column(String(20), nullable=False)
    secondary_color = Column(String(20), nullable=False)
    ai_generated_theme = Column(Text, nullable=True)
    rsvp_contact = Column(String(255), nullable=True)
    total_budget = Column(Float, nullable=True, default=None)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="weddings")
    guests = relationship("Guest", back_populates="wedding", cascade="all, delete-orphan")
    designs = relationship("Design", back_populates="wedding", cascade="all, delete-orphan")
    checklist_items = relationship(
        "ChecklistItem", back_populates="wedding", cascade="all, delete-orphan"
    )
    budget_categories = relationship(
        "BudgetCategory", back_populates="wedding", cascade="all, delete-orphan"
    )
    expenses = relationship("Expense", back_populates="wedding", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="wedding", cascade="all, delete-orphan")
    wedding_tables = relationship(
        "WeddingTable", back_populates="wedding", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Wedding {self.partner1_name} & {self.partner2_name} on {self.wedding_date}>"


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=True)
    phone = Column(String(30), nullable=True)
    group_name = Column(String(100), nullable=True)
    meal_preference = Column(String(100), nullable=True)
    rsvp_status = Column(String(20), nullable=False, default="pending")
    table_number = Column(Integer, nullable=True)
    table_id = Column(Integer, ForeignKey("wedding_tables.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="guests")
    seating_table = relationship("WeddingTable", back_populates="guests", foreign_keys=[table_id])

    def __repr__(self):
        return f"<Guest {self.full_name} ({self.rsvp_status})>"


CHECKLIST_CATEGORIES = (
    "Venue",
    "Catering",
    "Attire",
    "Photography",
    "Flowers",
    "Music",
    "Stationery",
    "Transport",
    "Honeymoon",
    "Other",
)
CHECKLIST_PRIORITIES = ("low", "medium", "high")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), default="Other")
    due_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    priority = Column(String(20), default="medium")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="checklist_items")

    def __repr__(self):
        return f"<ChecklistItem {self.title!r} ({self.category})>"


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    allocated_amount = Column(Float, default=0)
    color = Column(String(7), default="#c9687a")
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="budget_categories")
    expenses = relationship("Expense", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BudgetCategory {self.name!r} ${self.allocated_amount}>"


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=True, index=True)
    vendor_id = Column(
        Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title = Column(String(200), nullable=False)
    estimated_cost = Column(Float, default=0)
    actual_cost = Column(Float, nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    paid_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="expenses")
    category = relationship("BudgetCategory", back_populates="expenses")
    vendor = relationship("Vendor", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.title!r} ${self.estimated_cost}>"


VENDOR_CATEGORIES = (
    "Venue",
    "Catering",
    "Photography",
    "Videography",
    "Flowers",
    "Music",
    "Hair & Makeup",
    "Transport",
    "Cake",
    "Stationery",
    "Officiant",
    "Other",
)
VENDOR_STATUSES = ("considering", "booked", "rejected", "backup")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="Other")
    business_name = Column(String(200), nullable=False)
    contact_name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(300), nullable=True)
    quoted_price = Column(Float, nullable=True)
    deposit_amount = Column(Float, nullable=True)
    deposit_paid = Column(Boolean, default=False, nullable=False)
    deposit_due_date = Column(Date, nullable=True)
    contracted = Column(Boolean, default=False, nullable=False)
    contract_signed_date = Column(Date, nullable=True)
    contract_url = Column(String(500), nullable=True)
    rating = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="considering", nullable=False)
    final_payment_amount = Column(Float, nullable=True)
    final_payment_paid = Column(Boolean, default=False, nullable=False)
    final_payment_due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="vendors")
    expenses = relationship("Expense", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor {self.business_name!r} ({self.category})>"


class WeddingTable(Base):
    __tablename__ = "wedding_tables"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    table_number = Column(Integer, nullable=False)
    table_name = Column(String(100), nullable=True)
    capacity = Column(Integer, default=8, nullable=False)
    shape = Column(String(20), default="round", nullable=False)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    wedding = relationship("Wedding", back_populates="wedding_tables")
    guests = relationship("Guest", back_populates="seating_table", foreign_keys="Guest.table_id")

    def display_name(self):
        return self.table_name or f"Table {self.table_number}"


class Design(Base):
    __tablename__ = "designs"

    id = Column(Integer, primary_key=True)
    wedding_id = Column(Integer, ForeignKey("weddings.id"), nullable=False, index=True)
    design_type = Column(String(50), nullable=False)
    html_content = Column(Text, nullable=False)
    pdf_file_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    wedding = relationship("Wedding", back_populates="designs")

    def __repr__(self):
        return f"<Design {self.design_type} for wedding {self.wedding_id}>"
