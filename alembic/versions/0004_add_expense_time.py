"""Store the receipt time."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("expenses", sa.Column("expense_time", sa.Time(), nullable=True))


def downgrade():
    op.drop_column("expenses", "expense_time")
