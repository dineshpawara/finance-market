"""create_security_notifications_table

Revision ID: fcd03f18fbd4
Revises: e9a2ad8b38d2
Create Date: 2026-10-16 17:40:26.383483

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "fcd03f18fbd4"
down_revision: Union[str, Sequence[str], None] = "e9a2ad8b38d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Creates the security_notifications table and associated indexes if not exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "security_notifications" not in tables:
        op.create_table(
            "security_notifications",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=100), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("is_dismissed", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.id"],
                name=op.f("fk_security_notifications_user_id_users"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_security_notifications")),
        )
        op.create_index(
            op.f("ix_security_notifications_id"),
            "security_notifications",
            ["id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_security_notifications_user_id"),
            "security_notifications",
            ["user_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_security_notifications_is_dismissed"),
            "security_notifications",
            ["is_dismissed"],
            unique=False,
        )


def downgrade() -> None:
    """Drops the security_notifications table and associated indexes if exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "security_notifications" in tables:
        op.drop_index(
            op.f("ix_security_notifications_is_dismissed"),
            table_name="security_notifications",
        )
        op.drop_index(
            op.f("ix_security_notifications_user_id"),
            table_name="security_notifications",
        )
        op.drop_index(
            op.f("ix_security_notifications_id"),
            table_name="security_notifications",
        )
        op.drop_table("security_notifications")
