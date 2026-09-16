"""LangGraph Orchestrator - Coordinates the sequential agent pipeline"""
from typing import Dict, Any, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, ValidationError
import json
import logging
from datetime import datetime
import asyncio
import uuid

from app.agents.research_agent import run_research_agent
from app.agents.requirements_agent import run_requirements_agent
from app.agents.qualification_agent import run_qualification_agent
from app.agents.solution_agent import run_solution_agent
from app.agents.proposal_agent import run_proposal_agent
from app.agents.reviewer_agent import run_reviewer_agent
from app.database import SessionLocal
from app.models import AgentExecution
from app.services.llm_service import ProviderQuotaError
from app.schemas import (
    ProposalOutput,
    QualificationOutput,
    RequirementOutput,
    ResearchOutput,
    ReviewerOutput,
    SolutionMatchingOutput,
)

logger = logging.getLogger(__name__)


async def _notify_progress(state: Dict[str, Any], stage: str) -> None:
    callback = state.get("_progress_callback")
    if callback:
        await callback(state, stage)


def _has_missing_information(state: Dict[str, Any]) -> bool:
    requirements = state.get("requirements_result") or {}
    missing_information = requirements.get("missing_information") or []
    functional_requirements = requirements.get("functional_requirements") or []
    return bool(missing_information) and not functional_requirements


def _has_provider_quota_error(state: Dict[str, Any]) -> bool:
    return any(error.get("error_type") == "provider_quota" for error in state.get("errors", []))


def _record_provider_quota_error(state: Dict[str, Any], stage: str, error: ProviderQuotaError) -> None:
    message = str(error)
    state["errors"].append({"stage": stage, "error": message, "error_type": "provider_quota"})
    state["pipeline_status"] = "failed"
    state["failure_reason"] = message


_OUTPUT_SCHEMAS = {
    "research_result": ResearchOutput,
    "requirements_result": RequirementOutput,
    "qualification_result": QualificationOutput,
    "solution_matching_result": SolutionMatchingOutput,
    "proposal_result": ProposalOutput,
    "reviewer_result": ReviewerOutput,
}


def _validate_stage_outputs(state: Dict[str, Any]) -> Dict[str, Any]:
    for field_name, schema in _OUTPUT_SCHEMAS.items():
        value = state.get(field_name)
        if value is None:
            continue
        try:
            validated = schema.model_validate(value).model_dump()
            validated.update({
                key: item for key, item in value.items()
                if key not in schema.model_fields
            })
            state[field_name] = validated
        except ValidationError as error:
            state.setdefault("errors", []).append({
                "stage": field_name.removesuffix("_result"),
                "error": "Stage output schema validation failed",
                "details": error.errors(),
            })
    return state


def _record_agent_execution(
    lead_id: str,
    agent_name: str,
    stage: str,
    output_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> None:
    db = SessionLocal()
    try:
        db.add(AgentExecution(
            id=str(uuid.uuid4()),
            lead_id=lead_id,
            agent_name=agent_name,
            stage=stage,
            output_data=output_data,
            status="failed" if error_message else "completed",
            error_message=error_message,
        ))
        db.commit()
    except Exception as exc:
        logger.warning(f"Unable to record {stage} execution: {exc}")
        db.rollback()
    finally:
        db.close()


class PipelineState(BaseModel):
    """State that flows through the pipeline"""
    model_config = {"extra": "allow"}

    lead_id: str
    inquiry_text: str
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    additional_context: Optional[str] = None
    conversation_history: Optional[list] = None
    
    # Stage results
    research_result: Optional[Dict[str, Any]] = None
    requirements_result: Optional[Dict[str, Any]] = None
    qualification_result: Optional[Dict[str, Any]] = None
    solution_matching_result: Optional[Dict[str, Any]] = None
    proposal_result: Optional[Dict[str, Any]] = None
    reviewer_result: Optional[Dict[str, Any]] = None
    
    # Execution tracking
    stages_completed: list = []
    errors: list = []
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SalesOrchestrator:
    """Orchestrates the sequential sales pipeline"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow with parallelized independent stages"""
        workflow = StateGraph(dict)

        # Add nodes for each agent
        workflow.add_node("research", self._node_research)
        workflow.add_node("requirements", self._node_requirements)
        workflow.add_node("qualification_and_solution", self._node_qualification_and_solution)
        workflow.add_node("proposal", self._node_proposal)
        workflow.add_node("reviewer", self._node_reviewer)
        workflow.add_node("complete", self._node_complete)

        # Set entry point
        workflow.set_entry_point("research")

        # Add edges - parallel execution of independent qualification & solution matching
        workflow.add_edge("research", "requirements")
        workflow.add_edge("requirements", "qualification_and_solution")
        workflow.add_edge("qualification_and_solution", "proposal")
        workflow.add_edge("proposal", "reviewer")
        workflow.add_edge("reviewer", "complete")
        workflow.add_edge("complete", END)

        return workflow.compile()

    async def _node_research(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Research stage"""
        try:
            logger.info(f"Starting research stage for lead {state.get('lead_id')}")
            
            result = await run_research_agent(
                company_name=state.get("company_name"),
                inquiry_text=state.get("inquiry_text"),
            )
            
            state["research_result"] = result
            state["stages_completed"].append("research")
            await _notify_progress(state, "research")
            _record_agent_execution(state.get("lead_id", ""), "research_agent", "research", result)
            logger.info(f"Research completed for lead {state.get('lead_id')}")
        except Exception as e:
            if isinstance(e, ProviderQuotaError):
                _record_provider_quota_error(state, "research", e)
            logger.error(f"Research stage failed: {str(e)}")
            if not isinstance(e, ProviderQuotaError):
                state["errors"].append({"stage": "research", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "research_agent", "research", error_message=str(e))
        
        return state

    async def _node_requirements(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Requirements analysis stage"""
        if _has_provider_quota_error(state):
            return state
        try:
            logger.info(f"Starting requirements stage for lead {state.get('lead_id')}")
            
            result = await run_requirements_agent(
                inquiry_text=state.get("inquiry_text"),
                research_context=state.get("research_result"),
                conversation_history=state.get("conversation_history"),
                budget=state.get("budget"),
                timeline=state.get("timeline"),
                company_size=state.get("company_size"),
                additional_context=state.get("additional_context"),
            )
            
            state["requirements_result"] = result
            state["stages_completed"].append("requirements")
            await _notify_progress(state, "requirements")
            _record_agent_execution(state.get("lead_id", ""), "requirements_agent", "requirements", result)
            logger.info(f"Requirements analysis completed for lead {state.get('lead_id')}")
        except Exception as e:
            if isinstance(e, ProviderQuotaError):
                _record_provider_quota_error(state, "requirements", e)
            logger.error(f"Requirements stage failed: {str(e)}")
            if not isinstance(e, ProviderQuotaError):
                state["errors"].append({"stage": "requirements", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "requirements_agent", "requirements", error_message=str(e))
        
        return state

    async def _node_qualification_and_solution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute qualification and solution matching concurrently as independent stages"""
        if _has_provider_quota_error(state):
            return state

        lead_data = {
            "lead_id": state.get("lead_id"),
            "company_name": state.get("company_name"),
            "contact_name": state.get("contact_name"),
            "email": state.get("email"),
            "inquiry_text": state.get("inquiry_text"),
            "industry": state.get("industry"),
            "company_size": state.get("company_size"),
            "budget": state.get("budget"),
            "timeline": state.get("timeline"),
            "additional_context": state.get("additional_context"),
        }

        async def _run_qual():
            try:
                logger.info(f"Starting qualification stage for lead {state.get('lead_id')}")
                result = await run_qualification_agent(
                    research_result=state.get("research_result"),
                    requirements_result=state.get("requirements_result"),
                    lead_data=lead_data,
                )
                _record_agent_execution(state.get("lead_id", ""), "qualification_agent", "qualification", result)
                logger.info(f"Qualification completed for lead {state.get('lead_id')}")
                return ("qualification", result, None)
            except Exception as e:
                if isinstance(e, ProviderQuotaError):
                    _record_provider_quota_error(state, "qualification", e)
                logger.error(f"Qualification stage failed: {str(e)}")
                _record_agent_execution(state.get("lead_id", ""), "qualification_agent", "qualification", error_message=str(e))
                return ("qualification", None, e)

        async def _run_solution():
            if _has_missing_information(state):
                logger.info("Skipping solution matching until required customer information is provided")
                return ("solution_matching", None, None)
            try:
                logger.info(f"Starting solution matching stage for lead {state.get('lead_id')}")
                result = await run_solution_agent(
                    requirements_result=state.get("requirements_result"),
                    company_size=state.get("company_size"),
                    budget=state.get("budget"),
                )
                _record_agent_execution(state.get("lead_id", ""), "solution_agent", "solution_matching", result)
                logger.info(f"Solution matching completed for lead {state.get('lead_id')}")
                return ("solution_matching", result, None)
            except Exception as e:
                if isinstance(e, ProviderQuotaError):
                    _record_provider_quota_error(state, "solution_matching", e)
                logger.error(f"Solution matching stage failed: {str(e)}")
                _record_agent_execution(state.get("lead_id", ""), "solution_agent", "solution_matching", error_message=str(e))
                return ("solution_matching", None, e)

        # Run independent stages concurrently!
        qual_res, sol_res = await asyncio.gather(_run_qual(), _run_solution())

        if qual_res[1] is not None:
            state["qualification_result"] = qual_res[1]
            state["stages_completed"].append("qualification")
        elif qual_res[2] is not None and not isinstance(qual_res[2], ProviderQuotaError):
            state["errors"].append({"stage": "qualification", "error": str(qual_res[2])})

        if sol_res[1] is not None:
            state["solution_matching_result"] = sol_res[1]
            state["stages_completed"].append("solution_matching")
        elif sol_res[2] is not None and not isinstance(sol_res[2], ProviderQuotaError):
            state["errors"].append({"stage": "solution_matching", "error": str(sol_res[2])})

        await _notify_progress(state, "qualification")
        await _notify_progress(state, "solution_matching")
        return state

    async def _node_qualification(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Lead qualification stage"""
        if _has_provider_quota_error(state):
            return state
        try:
            logger.info(f"Starting qualification stage for lead {state.get('lead_id')}")
            lead_data = {
                "lead_id": state.get("lead_id"),
                "company_name": state.get("company_name"),
                "contact_name": state.get("contact_name"),
                "email": state.get("email"),
                "inquiry_text": state.get("inquiry_text"),
                "industry": state.get("industry"),
                "company_size": state.get("company_size"),
                "budget": state.get("budget"),
                "timeline": state.get("timeline"),
                "additional_context": state.get("additional_context"),
            }
            
            result = await run_qualification_agent(
                research_result=state.get("research_result"),
                requirements_result=state.get("requirements_result"),
                lead_data=lead_data,
                solution_result=state.get("solution_matching_result"),
            )
            
            state["qualification_result"] = result
            state["stages_completed"].append("qualification")
            await _notify_progress(state, "qualification")
            _record_agent_execution(state.get("lead_id", ""), "qualification_agent", "qualification", result)
            logger.info(f"Qualification completed for lead {state.get('lead_id')}")
        except Exception as e:
            if isinstance(e, ProviderQuotaError):
                _record_provider_quota_error(state, "qualification", e)
            logger.error(f"Qualification stage failed: {str(e)}")
            if not isinstance(e, ProviderQuotaError):
                state["errors"].append({"stage": "qualification", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "qualification_agent", "qualification", error_message=str(e))
        
        return state

    async def _node_solution_matching(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Solution matching stage"""
        if _has_provider_quota_error(state):
            return state
        if _has_missing_information(state):
            logger.info("Skipping solution matching until required customer information is provided")
            return state

        try:
            logger.info(f"Starting solution matching stage for lead {state.get('lead_id')}")
            
            result = await run_solution_agent(
                requirements_result=state.get("requirements_result"),
                company_size=state.get("company_size"),
                budget=state.get("budget"),
            )
            
            state["solution_matching_result"] = result
            state["stages_completed"].append("solution_matching")
            await _notify_progress(state, "solution_matching")
            _record_agent_execution(state.get("lead_id", ""), "solution_agent", "solution_matching", result)
            logger.info(f"Solution matching completed for lead {state.get('lead_id')}")
        except Exception as e:
            if isinstance(e, ProviderQuotaError):
                _record_provider_quota_error(state, "solution_matching", e)
            logger.error(f"Solution matching stage failed: {str(e)}")
            if not isinstance(e, ProviderQuotaError):
                state["errors"].append({"stage": "solution_matching", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "solution_agent", "solution_matching", error_message=str(e))
        
        return state

    async def _node_proposal(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Proposal generation stage"""
        if _has_provider_quota_error(state):
            return state
        solution_result = state.get("solution_matching_result") or {}
        if _has_missing_information(state) or not solution_result.get("primary_solutions"):
            logger.info("Skipping proposal generation until qualification and solution matching are complete")
            return state

        try:
            logger.info(f"Starting proposal generation stage for lead {state.get('lead_id')}")
            
            result = await run_proposal_agent(
                requirements_result=state.get("requirements_result"),
                solution_matching_result=state.get("solution_matching_result"),
                company_name=state.get("company_name"),
            )
            
            state["proposal_result"] = result
            state["stages_completed"].append("proposal")
            await _notify_progress(state, "proposal")
            _record_agent_execution(state.get("lead_id", ""), "proposal_agent", "proposal", result)
            logger.info(f"Proposal generation completed for lead {state.get('lead_id')}")
        except Exception as e:
            if isinstance(e, ProviderQuotaError):
                _record_provider_quota_error(state, "proposal", e)
            logger.error(f"Proposal stage failed: {str(e)}")
            if not isinstance(e, ProviderQuotaError):
                state["errors"].append({"stage": "proposal", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "proposal_agent", "proposal", error_message=str(e))
        
        return state

    async def _node_reviewer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Final review stage"""
        if _has_provider_quota_error(state):
            return state
        proposal_result = state.get("proposal_result") or {}
        if _has_missing_information(state) or not proposal_result:
            logger.info("Skipping final review until qualification and proposal generation are complete")
            return state

        try:
            logger.info(f"Starting reviewer stage for lead {state.get('lead_id')}")
            
            result = await run_reviewer_agent(
                requirements_result=state.get("requirements_result"),
                qualification_result=state.get("qualification_result"),
                solution_matching_result=state.get("solution_matching_result"),
                proposal_result=state.get("proposal_result"),
            )
            
            state["reviewer_result"] = result
            state["stages_completed"].append("reviewer")
            await _notify_progress(state, "reviewer")
            _record_agent_execution(state.get("lead_id", ""), "reviewer_agent", "reviewer", result)
            logger.info(f"Review completed for lead {state.get('lead_id')}")
        except Exception as e:
            logger.error(f"Reviewer stage failed: {str(e)}")
            state["errors"].append({"stage": "reviewer", "error": str(e)})
            _record_agent_execution(state.get("lead_id", ""), "reviewer_agent", "reviewer", error_message=str(e))
        
        return state

    async def _node_complete(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mark pipeline as complete"""
        state["end_time"] = datetime.utcnow()
        state["stages_completed"].append("complete")
        logger.info(f"Pipeline completed for lead {state.get('lead_id')}")
        return state

    async def execute(self, lead_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full pipeline"""
        try:
            # Initialize state
            state = PipelineState(
                lead_id=lead_input.get("lead_id", ""),
                inquiry_text=lead_input.get("inquiry_text", ""),
                company_name=lead_input.get("company_name"),
                contact_name=lead_input.get("contact_name"),
                email=lead_input.get("email"),
                industry=lead_input.get("industry"),
                company_size=lead_input.get("company_size"),
                budget=lead_input.get("budget"),
                timeline=lead_input.get("timeline"),
                additional_context=lead_input.get("additional_context"),
                                conversation_history=lead_input.get("conversation_history", []),
                start_time=datetime.utcnow(),
                stages_completed=[],
                errors=[],
            )

            # Execute graph
            graph_state = state.model_dump()
            graph_state["_progress_callback"] = lead_input.get("_progress_callback")
            result = await self.graph.ainvoke(graph_state)
            result.pop("_progress_callback", None)

            return _validate_stage_outputs(result)
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            raise


# Singleton instance
_orchestrator = None


def get_orchestrator() -> SalesOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SalesOrchestrator()
    return _orchestrator
