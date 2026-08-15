"""Add approvals, refresh tokens and receipt metadata."""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    decision = sa.Enum("pending", "approved", "rejected", name="approvaldecision")
    op.add_column("expenses", sa.Column("cost_center", sa.String(80), nullable=True))
    op.add_column("expenses", sa.Column("receipt_path", sa.String(500), nullable=True))
    op.create_index("ix_expenses_cost_center", "expenses", ["cost_center"])
    op.create_table(
        "approvals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("expense_id", sa.Uuid(), sa.ForeignKey("expenses.id"), nullable=False),
        sa.Column("approver_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("decision", decision, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("expense_id", "level", name="uq_approval_expense_level"),
    )
    op.create_index("ix_approvals_organization_id", "approvals", ["organization_id"])
    op.create_index("ix_approvals_expense_id", "approvals", ["expense_id"])
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)


def downgrade():
    op.drop_table("refresh_tokens")
    op.drop_table("approvals")
    op.drop_index("ix_expenses_cost_center", table_name="expenses")
    op.drop_column("expenses", "receipt_path")
    op.drop_column("expenses", "cost_center")
    sa.Enum(name="approvaldecision").drop(op.get_bind(), checkfirst=True)
