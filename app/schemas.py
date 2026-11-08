from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Health & Diagnostic Schemas ---
class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    gemini_configured: bool
    version: str = "1.0.0"


# --- Paper Upload & Status Schemas ---
class PaperUploadResponse(BaseModel):
    paper_id: int
    original_filename: str
    stored_filename: str
    file_size_bytes: int
    status: str
    message: str
    uploaded_at: datetime


class AgentLogSchema(BaseModel):
    agent_name: str
    log_level: str
    message: str
    execution_time_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingStatusResponse(BaseModel):
    paper_id: int
    status: str
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    recent_logs: List[AgentLogSchema] = []


# --- Content Detail Schemas ---
class PaperMetadataSchema(BaseModel):
    title: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[str] = None
    journal_conference: Optional[str] = None
    abstract_text: Optional[str] = None
    total_pages: int = 0

    model_config = ConfigDict(from_attributes=True)


class PaperSummarySchema(BaseModel):
    tldr: Optional[str] = None
    problem_statement: Optional[str] = None
    key_contributions: Optional[str] = None
    methodology: Optional[str] = None
    experimental_results: Optional[str] = None
    limitations_future_work: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GeneratedAssetSchema(BaseModel):
    id: int
    asset_type: str  # 'presentation', 'email', 'code'
    title: str
    content_text: Optional[str] = None
    file_path: Optional[str] = None
    metadata_json: Optional[str] = None
    download_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperResultsResponse(BaseModel):
    paper_id: int
    original_filename: str
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Optional[PaperMetadataSchema] = None
    summary: Optional[PaperSummarySchema] = None
    assets: List[GeneratedAssetSchema] = []
    logs: List[AgentLogSchema] = []


# --- Process Trigger Schema ---
class ProcessPaperRequest(BaseModel):
    generate_summary: bool = True
    generate_ppt: bool = True
    generate_emails: bool = True
    generate_code: bool = True
