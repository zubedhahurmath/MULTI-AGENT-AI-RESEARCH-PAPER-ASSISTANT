from typing import TypedDict, Optional, List, Dict, Any


class AgentState(TypedDict, total=False):
    """Centralized shared state dictionary passed across agents in the LangGraph workflow."""

    paper_id: int
    file_path: str
    paper_metadata: Dict[str, Any]
    raw_sections: Dict[str, str]
    summary_data: Dict[str, Any]
    ppt_file_path: Optional[str]
    ppt_outline: Optional[List[Dict[str, Any]]]
    email_drafts: Optional[List[Dict[str, Any]]]
    code_solution: Optional[Dict[str, Any]]
    agent_logs: List[Dict[str, Any]]
    current_step: str
    error: Optional[str]
