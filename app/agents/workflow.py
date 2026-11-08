import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.pdf_agent import pdf_processing_node
from app.agents.summarizer_agent import summarizer_node
from app.agents.ppt_agent import ppt_generator_node
from app.agents.email_agent import email_generator_node
from app.agents.code_agent import code_generator_node
from app.agents.manager_agent import manager_supervisor_node

logger = logging.getLogger("workflow")


def check_pdf_error(state: AgentState) -> str:
    """Route to manager if PDF extraction failed, otherwise proceed to summarization."""
    if state.get("error"):
        return "manager_agent"
    return "summarizer_agent"


def check_summary_error(state: AgentState) -> str:
    """Route to manager if summarization failed, otherwise proceed to asset generation."""
    if state.get("error"):
        return "manager_agent"
    return "ppt_agent"


def build_research_graph() -> Any:
    """Constructs and compiles the multi-agent StateGraph using LangGraph."""
    graph = StateGraph(AgentState)

    # 1. Register Agent Nodes
    graph.add_node("pdf_agent", pdf_processing_node)
    graph.add_node("summarizer_agent", summarizer_node)
    graph.add_node("ppt_agent", ppt_generator_node)
    graph.add_node("email_agent", email_generator_node)
    graph.add_node("code_agent", code_generator_node)
    graph.add_node("manager_agent", manager_supervisor_node)

    # 2. Add Transitions and Edges
    graph.add_edge(START, "pdf_agent")

    graph.add_conditional_edges(
        "pdf_agent",
        check_pdf_error,
        {
            "manager_agent": "manager_agent",
            "summarizer_agent": "summarizer_agent"
        }
    )

    graph.add_conditional_edges(
        "summarizer_agent",
        check_summary_error,
        {
            "manager_agent": "manager_agent",
            "ppt_agent": "ppt_agent"
        }
    )

    # Asset Generation Sequence: PPT -> Email -> Code -> Manager
    graph.add_edge("ppt_agent", "email_agent")
    graph.add_edge("email_agent", "code_agent")
    graph.add_edge("code_agent", "manager_agent")
    graph.add_edge("manager_agent", END)

    return graph.compile()


# Compiled LangGraph Workflow Singleton
research_paper_graph = build_research_graph()


def run_multi_agent_pipeline(paper_id: int, file_path: str) -> Dict[str, Any]:
    """
    Executes the multi-agent graph pipeline synchronously or inside a background worker.
    """
    initial_state: AgentState = {
        "paper_id": paper_id,
        "file_path": file_path,
        "paper_metadata": {},
        "raw_sections": {},
        "summary_data": {},
        "ppt_file_path": None,
        "ppt_outline": [],
        "email_drafts": [],
        "code_solution": {},
        "agent_logs": [],
        "current_step": "STARTED",
        "error": None
    }

    logger.info(f"Triggering LangGraph pipeline for paper_id={paper_id}")
    final_state = research_paper_graph.invoke(initial_state)
    logger.info(f"LangGraph pipeline completed for paper_id={paper_id} with step: {final_state.get('current_step')}")
    return final_state
