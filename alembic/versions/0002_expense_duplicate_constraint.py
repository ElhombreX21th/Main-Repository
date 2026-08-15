"""Enforce composite expense duplicate detection.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_expense_merchant_date_amount",
        "expenses",
        ["organization_id", "merchant_tax_id", "expense_date", "amount"],
    )


def downgrade():
    op.drop_constraint("uq_expense_merchant_date_amount", "expenses", type_="unique")
