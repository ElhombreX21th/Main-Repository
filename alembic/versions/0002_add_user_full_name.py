"""Store the user's full name."""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("full_name", sa.String(160), nullable=True))


def downgrade():
    op.drop_column("users", "full_name")