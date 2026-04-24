"""Create core schema (users, weddings, guests, designs)

Revision ID: b8e32f1d9000
Revises:
Create Date: 2026-03-25 10:00:00.000000

The original project used db.create_all() to bootstrap these four tables.
That call was removed during the Phase 1 refactor, leaving the migration
chain unable to run on a fresh database. This migration restores the base
schema so the chain is runnable from scratch.

Each table contains only the columns that existed at the time the first
migration (a6b422fa4c93) was written. Columns added by later migrations
(avatar_color, phone, timezone, email_notifications, updated_at on users;
total_budget and rsvp_contact on weddings; table_id on guests) are
intentionally absent — those migrations add them.

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b8e32f1d9000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "weddings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner1_name", sa.String(length=120), nullable=False),
        sa.Column("partner2_name", sa.String(length=120), nullable=False),
        sa.Column("wedding_date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("venue_name", sa.String(length=255), nullable=False),
        sa.Column("style", sa.String(length=20), nullable=False),
        sa.Column("primary_color", sa.String(length=20), nullable=False),
        sa.Column("secondary_color", sa.String(length=20), nullable=False),
        sa.Column("ai_generated_theme", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("weddings", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_weddings_user_id"), ["user_id"], unique=False)

    op.create_table(
        "guests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wedding_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("group_name", sa.String(length=100), nullable=True),
        sa.Column("meal_preference", sa.String(length=100), nullable=True),
        sa.Column("rsvp_status", sa.String(length=20), nullable=False),
        sa.Column("table_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["wedding_id"], ["weddings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("guests", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_guests_wedding_id"), ["wedding_id"], unique=False)

    op.create_table(
        "designs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("wedding_id", sa.Integer(), nullable=False),
        sa.Column("design_type", sa.String(length=50), nullable=False),
        sa.Column("html_content", sa.Text(), nullable=False),
        sa.Column("pdf_file_path", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["wedding_id"], ["weddings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("designs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_designs_wedding_id"), ["wedding_id"], unique=False)


def downgrade():
    with op.batch_alter_table("designs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_designs_wedding_id"))
    op.drop_table("designs")

    with op.batch_alter_table("guests", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_guests_wedding_id"))
    op.drop_table("guests")

    with op.batch_alter_table("weddings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_weddings_user_id"))
    op.drop_table("weddings")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))
    op.drop_table("users")
