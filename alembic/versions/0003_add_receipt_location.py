"""Store the receipt merchant location."""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("expenses", sa.Column("merchant_city", sa.String(120), nullable=True))
    op.add_column("expenses", sa.Column("merchant_state", sa.String(2), nullable=True))


def downgrade():
    op.drop_column("expenses", "merchant_state")
    op.drop_column("expenses", "merchant_city")