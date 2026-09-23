from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, Boolean, Enum, Text, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid
from enum import Enum as PyEnum

Base = declarative_base()


class LeadStatusEnum(PyEnum):
    QUALIFIED = "Qualified"
    NEEDS_INFO = "Needs More Information"
    LOW_PRIORITY = "Low Priority"


class Lead(Base):
    """Lead record in database"""
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=True, index=True)
    inquiry_text = Column(Text, nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(320), nullable=True, index=True)
    industry = Column(String(100), nullable=True, index=True)
    company_size = Column(String(50), nullable=True)
    budget = Column(String(50), nullable=True)
    timeline = Column(String(100), nullable=True)
    additional_context = Column(Text, nullable=True)

    # Pipeline Results
    lead_status = Column(String(50), nullable=False, index=True)
    composite_score = Column(Float, nullable=True, index=True)
    
    __table_args__ = (
        Index("ix_leads_status_created_at", "lead_status", "created_at"),
    )
    
    # JSON storage for full results
    research_result = Column(JSON, nullable=True)
    requirements_result = Column(JSON, nullable=True)
    qualification_result = Column(JSON, nullable=True)
    solution_matching_result = Column(JSON, nullable=True)
    proposal_result = Column(JSON, nullable=True)
    reviewer_result = Column(JSON, nullable=True)
    
    # Full pipeline result
    pipeline_result = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Tracking
    pipeline_duration_seconds = Column(Float, nullable=True)
    created_by = Column(String(255), nullable=True)


class KnowledgeBaseEntry(Base):
    """Product/Service knowledge base entries"""
    __tablename__ = "knowledge_base_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entry_type = Column(String(50), nullable=False, index=True)  # "product", "service", "addon"
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Structured data
    features = Column(JSON, nullable=True)  # List of features
    pricing = Column(JSON, nullable=True)  # Pricing tiers
    certifications = Column(JSON, nullable=True)  # Compliance certs
    delivery_timeline = Column(String(255), nullable=True)
    
    # RAG embedding metadata
    embedding_id = Column(String(255), nullable=True, index=True)
    embedding_vector = Column(JSON, nullable=True)  # For reference
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)


class Proposal(Base):
    """Generated proposals linked to leads"""
    __tablename__ = "proposals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), nullable=False, index=True)  # FK to leads.id
    
    # Proposal content
    executive_summary = Column(Text, nullable=True)
    implementation_roadmap = Column(JSON, nullable=True)
    pricing_proposal = Column(JSON, nullable=True)
    success_metrics = Column(JSON, nullable=True)
    
    # Full proposal HTML/Markdown
    proposal_html = Column(Text, nullable=True)
    proposal_markdown = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default="draft", index=True)  # draft, approved, sent, accepted, rejected
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    sent_to = Column(String(255), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_proposals_lead_created", "lead_id", "created_at"),
    )


class AgentExecution(Base):
    """Track individual agent executions for debugging/audit"""
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    
    # Execution details
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    llm_model = Column(String(100), nullable=True)
    
    # Performance
    execution_time_seconds = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)  # completed, failed, in_progress
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserActivity(Base):
    """Track user actions for audit trail"""
    __tablename__ = "user_activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)  # submit_lead, view_result, approve_proposal, etc
    lead_id = Column(String(36), nullable=True, index=True)
    
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class LeadMemory(Base):
    """Persistent conversation memory associated with a lead."""
    __tablename__ = "lead_memory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), nullable=False, index=True)
    role = Column(String(30), nullable=False)  # user, agent, system
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class User(Base):
    """User account model for persistent registration and authentication"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(320), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="member", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordResetToken(Base):
    """Temporary verification tokens (OTP) for secure password reset."""
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False, index=True)
    otp_code = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

