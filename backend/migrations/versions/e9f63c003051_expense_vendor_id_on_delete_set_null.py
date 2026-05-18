"""expense.vendor_id ON DELETE SET NULL

Revision ID: e9f63c003051
Revises: 42b1c5398bcd
Create Date: 2026-05-18 20:39:54.809305

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e9f63c003051"
down_revision = "42b1c5398bcd"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("fk_expenses_vendor_id", "expenses", type_="foreignkey")
    op.create_foreign_key(
        "fk_expenses_vendor_id",
        "expenses",
        "vendors",
        ["vendor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_expenses_vendor_id", "expenses", type_="foreignkey")
    op.create_foreign_key(
        "fk_expenses_vendor_id",
        "expenses",
        "vendors",
        ["vendor_id"],
        ["id"],
    )
