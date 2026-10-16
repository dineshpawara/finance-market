"""make_totp_timestamps_nullable

Revision ID: e9a2ad8b38d2
Revises: 7807a4770f2c
Create Date: 2026-10-12 13:40:50.859019

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e9a2ad8b38d2"
down_revision: Union[str, Sequence[str], None] = "7807a4770f2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: make uninitialized TOTP timestamps nullable."""
    op.alter_column("totp", "locked_until", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column("totp", "enabled_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column("totp", "last_used_at", existing_type=sa.DateTime(timezone=True), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("totp", "last_used_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column("totp", "enabled_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.alter_column("totp", "locked_until", existing_type=sa.DateTime(timezone=True), nullable=False)
