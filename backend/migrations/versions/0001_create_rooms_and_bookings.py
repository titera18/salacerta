"""Cria as tabelas de salas e reservas.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ux_rooms_name_lower", "rooms", [sa.text("lower(name)")], unique=True)

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("room_id", sa.String(36), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("organizer", sa.String(254), nullable=False),
        sa.Column("attendees", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_index("ix_bookings_room_period", "bookings", ["room_id", "starts_at", "ends_at"])


def downgrade() -> None:
    op.drop_table("bookings")
    op.drop_table("rooms")
