"""Add contact metadata to leads.

Revision ID: 0002_lead_contact_fields
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_lead_contact_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("contact_name", sa.String(length=255), nullable=True))
    op.add_column("leads", sa.Column("email", sa.String(length=320), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "email")
    op.drop_column("leads", "contact_name")