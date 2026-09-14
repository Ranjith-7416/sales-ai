"""Create the initial Sales AI schema.

Revision ID: 0001_initial_schema
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_name", sa.String(length=255)),
        sa.Column("inquiry_text", sa.Text(), nullable=False),
        sa.Column("industry", sa.String(length=100)),
        sa.Column("company_size", sa.String(length=50)),
        sa.Column("budget", sa.String(length=50)),
        sa.Column("timeline", sa.String(length=100)),
        sa.Column("additional_context", sa.Text()),
        sa.Column("lead_status", sa.String(length=50), nullable=False),
        sa.Column("composite_score", sa.Float()),
        sa.Column("research_result", sa.JSON()),
        sa.Column("requirements_result", sa.JSON()),
        sa.Column("qualification_result", sa.JSON()),
        sa.Column("solution_matching_result", sa.JSON()),
        sa.Column("proposal_result", sa.JSON()),
        sa.Column("reviewer_result", sa.JSON()),
        sa.Column("pipeline_result", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("pipeline_duration_seconds", sa.Float()),
        sa.Column("created_by", sa.String(length=255)),
    )
    op.create_index("ix_leads_company_name", "leads", ["company_name"])
    op.create_index("ix_leads_industry", "leads", ["industry"])
    op.create_index("ix_leads_lead_status", "leads", ["lead_status"])
    op.create_index("ix_leads_created_at", "leads", ["created_at"])

    op.create_table(
        "knowledge_base_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("entry_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("features", sa.JSON()),
        sa.Column("pricing", sa.JSON()),
        sa.Column("certifications", sa.JSON()),
        sa.Column("delivery_timeline", sa.String(length=255)),
        sa.Column("embedding_id", sa.String(length=255)),
        sa.Column("embedding_vector", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("is_active", sa.Boolean()),
    )
    op.create_index("ix_knowledge_base_entries_entry_type", "knowledge_base_entries", ["entry_type"])
    op.create_index("ix_knowledge_base_entries_name", "knowledge_base_entries", ["name"])
    op.create_index("ix_knowledge_base_entries_embedding_id", "knowledge_base_entries", ["embedding_id"])
    op.create_index("ix_knowledge_base_entries_is_active", "knowledge_base_entries", ["is_active"])

    op.create_table(
        "proposals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lead_id", sa.String(length=36), nullable=False),
        sa.Column("executive_summary", sa.Text()),
        sa.Column("implementation_roadmap", sa.JSON()),
        sa.Column("pricing_proposal", sa.JSON()),
        sa.Column("success_metrics", sa.JSON()),
        sa.Column("proposal_html", sa.Text()),
        sa.Column("proposal_markdown", sa.Text()),
        sa.Column("status", sa.String(length=50)),
        sa.Column("approved_by", sa.String(length=255)),
        sa.Column("approved_at", sa.DateTime()),
        sa.Column("sent_to", sa.String(length=255)),
        sa.Column("sent_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_proposals_lead_id", "proposals", ["lead_id"])

    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lead_id", sa.String(length=36), nullable=False),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("input_data", sa.JSON()),
        sa.Column("output_data", sa.JSON()),
        sa.Column("llm_model", sa.String(length=100)),
        sa.Column("execution_time_seconds", sa.Float()),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("cost_estimate", sa.Float()),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_agent_executions_lead_id", "agent_executions", ["lead_id"])
    op.create_index("ix_agent_executions_agent_name", "agent_executions", ["agent_name"])
    op.create_index("ix_agent_executions_created_at", "agent_executions", ["created_at"])

    op.create_table(
        "user_activities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=255)),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("lead_id", sa.String(length=36)),
        sa.Column("details", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_user_activities_lead_id", "user_activities", ["lead_id"])
    op.create_index("ix_user_activities_created_at", "user_activities", ["created_at"])

    op.create_table(
        "lead_memory",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lead_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lead_memory_lead_id", "lead_memory", ["lead_id"])
    op.create_index("ix_lead_memory_created_at", "lead_memory", ["created_at"])


def downgrade() -> None:
    op.drop_table("lead_memory")
    op.drop_table("user_activities")
    op.drop_table("agent_executions")
    op.drop_table("proposals")
    op.drop_table("knowledge_base_entries")
    op.drop_table("leads")
