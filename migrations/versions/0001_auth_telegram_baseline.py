"""Auth and Telegram baseline.

Revision ID: 0001_auth_telegram
Revises:
Create Date: 2026-06-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_auth_telegram"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("user_token", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("profile_completed", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_user_token"), "user", ["user_token"], unique=True)

    op.create_table(
        "telegram_accounts",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("telegram_user_id", sa.String(length=32), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("photo_url", sa.String(length=512), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column(
            "linked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_auth_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_accounts_telegram_user_id"),
        "telegram_accounts",
        ["telegram_user_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_telegram_accounts_user_id"),
        "telegram_accounts",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "telegram_link_sessions",
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telegram_link_sessions_token"),
        "telegram_link_sessions",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f("ix_telegram_link_sessions_user_id"),
        "telegram_link_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_telegram_link_sessions_user_id"),
        table_name="telegram_link_sessions",
    )
    op.drop_index(
        op.f("ix_telegram_link_sessions_token"),
        table_name="telegram_link_sessions",
    )
    op.drop_table("telegram_link_sessions")
    op.drop_index(op.f("ix_telegram_accounts_user_id"), table_name="telegram_accounts")
    op.drop_index(
        op.f("ix_telegram_accounts_telegram_user_id"),
        table_name="telegram_accounts",
    )
    op.drop_table("telegram_accounts")
    op.drop_index(op.f("ix_user_user_token"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
