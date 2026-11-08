import os
import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Depends,
    BackgroundTasks,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, init_db
from app.models import Paper, PaperMetadata, PaperSummary, GeneratedAsset, AgentLog
from app.schemas import (
    HealthResponse,
    PaperUploadResponse,
    ProcessingStatusResponse,
    PaperResultsResponse,
    PaperMetadataSchema,
    PaperSummarySchema,
    GeneratedAssetSchema,
    AgentLogSchema
)
from app.services.gemini_client import gemini_service
from app.services.pdf_extractor import pdf_extractor_service
from app.agents.workflow import run_multi_agent_pipeline

# Configure logger
logging.basicConfig(level=logging.INFO if settings.DEBUG else logging.WARNING)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event to initialize database tables and directories on startup."""
    settings.ensure_directories()
    init_db()
    logger.info("Database and runtime storage directories initialized.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Multi-Agent AI Research Paper Assistant backend powered by LangGraph, Gemini, and PyMuPDF.",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets and Templates
static_dir = Path(__file__).resolve().parent / "static"
templates_dir = Path(__file__).resolve().parent / "templates"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

templates = Jinja2Templates(directory=str(templates_dir)) if templates_dir.exists() else None


# Global Exception Handler (Prevents internal server stack leaks to users)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing your request. Please try again."}
    )


# --- Basic & Health Endpoints ---
@app.get("/", summary="Root Dashboard or Index View")
async def root(request: Request):
    """Serves the main dashboard page."""
    if templates and (templates_dir / "index.html").exists():
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"app_name": settings.APP_NAME}
        )
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", response_model=HealthResponse, summary="System Health and Configuration Check")
async def health_check():
    """Checks application health and verifies if Gemini API key is configured."""
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        gemini_configured=gemini_service.is_configured(),
        version="1.0.0"
    )


# --- Paper Upload Endpoint ---
@app.post("/api/upload", response_model=PaperUploadResponse, status_code=status.HTTP_201_CREATED, summary="Upload Research Paper PDF")
async def upload_paper(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    auto_process: bool = True,
    db: Session = Depends(get_db)
):
    """
    Accepts, validates, and stores a research paper in PDF format.
    Ensures safe unique filenames, validates PDF magic bytes, enforces size limits,
    and optionally auto-triggers the multi-agent pipeline in the background.
    """
    original_filename = file.filename or "unknown.pdf"
    file_ext = Path(original_filename).suffix.lower()

    # 1. Extension Validation
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF research papers (.pdf) are supported."
        )

    # 2. Read file content with size limit enforcement
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # 3. Security: Validate PDF Magic Bytes (%PDF-)
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF structure. File does not contain standard PDF header bytes."
        )

    # 4. Generate Safe Unique Filename (Prevent Path Traversal)
    safe_stored_name = f"paper_{uuid.uuid4().hex}.pdf"
    destination_path = settings.UPLOAD_DIR / safe_stored_name

    try:
        with open(destination_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store the uploaded file on the server."
        )

    # 5. Record Paper in SQLite
    new_paper = Paper(
        original_filename=original_filename,
        stored_filename=safe_stored_name,
        file_path=str(destination_path),
        file_size_bytes=file_size,
        status="PROCESSING" if auto_process else "PENDING"
    )
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)

    # 6. Auto-trigger multi-agent processing in background if requested
    if auto_process and background_tasks is not None:
        background_tasks.add_task(run_multi_agent_pipeline, new_paper.id, str(destination_path))

    return PaperUploadResponse(
        paper_id=new_paper.id,
        original_filename=new_paper.original_filename,
        stored_filename=new_paper.stored_filename,
        file_size_bytes=new_paper.file_size_bytes,
        status=new_paper.status,
        message="Paper uploaded successfully. Multi-agent processing initiated." if auto_process else "Paper uploaded successfully.",
        uploaded_at=new_paper.uploaded_at
    )


# --- Process Paper Endpoint ---
@app.post("/api/process/{paper_id}", summary="Trigger Multi-Agent Analysis Pipeline")
async def process_paper(
    paper_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Manually trigger or re-run the LangGraph multi-agent analysis for an uploaded paper."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper with ID {paper_id} not found.")

    if not os.path.exists(paper.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Underlying paper file is missing on the server.")

    paper.status = "PROCESSING"
    paper.error_message = None
    db.commit()

    background_tasks.add_task(run_multi_agent_pipeline, paper.id, paper.file_path)

    return {"paper_id": paper.id, "status": "PROCESSING", "message": "Multi-agent processing launched in background."}


# --- Status Endpoint ---
@app.get("/api/status/{paper_id}", response_model=ProcessingStatusResponse, summary="Get Paper Processing Status")
async def get_paper_status(paper_id: int, db: Session = Depends(get_db)):
    """Check live status of the paper processing and review recent agent execution logs."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper with ID {paper_id} not found.")

    recent_logs = (
        db.query(AgentLog)
        .filter(AgentLog.paper_id == paper_id)
        .order_by(AgentLog.created_at.desc())
        .limit(10)
        .all()
    )

    return ProcessingStatusResponse(
        paper_id=paper.id,
        status=paper.status,
        error_message=paper.error_message,
        completed_at=paper.completed_at,
        recent_logs=[AgentLogSchema.model_validate(log) for log in recent_logs]
    )


# --- Results Endpoint ---
@app.get("/api/results/{paper_id}", response_model=PaperResultsResponse, summary="Get Full Paper Analysis Results")
async def get_paper_results(paper_id: int, db: Session = Depends(get_db)):
    """Retrieve full analysis results including metadata, summary, PPT download link, emails, and code."""
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper with ID {paper_id} not found.")

    metadata = db.query(PaperMetadata).filter(PaperMetadata.paper_id == paper_id).first()
    summary = db.query(PaperSummary).filter(PaperSummary.paper_id == paper_id).first()
    assets = db.query(GeneratedAsset).filter(GeneratedAsset.paper_id == paper_id).all()
    logs = db.query(AgentLog).filter(AgentLog.paper_id == paper_id).order_by(AgentLog.created_at.asc()).all()

    # Attach download url to presentation assets
    asset_schemas = []
    for asset in assets:
        schema_dict = GeneratedAssetSchema.model_validate(asset)
        if asset.asset_type == "presentation" and asset.file_path:
            schema_dict.download_url = f"/api/download/{asset.id}"
        asset_schemas.append(schema_dict)

    return PaperResultsResponse(
        paper_id=paper.id,
        original_filename=paper.original_filename,
        status=paper.status,
        error_message=paper.error_message,
        uploaded_at=paper.uploaded_at,
        completed_at=paper.completed_at,
        metadata=PaperMetadataSchema.model_validate(metadata) if metadata else None,
        summary=PaperSummarySchema.model_validate(summary) if summary else None,
        assets=asset_schemas,
        logs=[AgentLogSchema.model_validate(log) for log in logs]
    )


# --- Download Asset Endpoint ---
@app.get("/api/download/{asset_id}", summary="Download Generated Presentation or File Asset")
async def download_asset(asset_id: int, db: Session = Depends(get_db)):
    """Securely downloads a generated asset file (e.g. PowerPoint presentation) while preventing path traversal."""
    asset = db.query(GeneratedAsset).filter(GeneratedAsset.id == asset_id).first()
    if not asset or not asset.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found or contains no downloadable file.")

    target_path = Path(asset.file_path).resolve()

    # Security: Path Traversal Protection
    allowed_dirs = [
        settings.PRESENTATION_DIR.resolve(),
        settings.UPLOAD_DIR.resolve()
    ]

    is_allowed = any(target_path.is_relative_to(allowed_dir) for allowed_dir in allowed_dirs)
    if not is_allowed or not target_path.exists() or not target_path.is_file():
        logger.warning(f"Unauthorized or invalid download path attempt: {target_path}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to the requested file path is forbidden.")

    filename = target_path.name
    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation" if target_path.suffix == ".pptx" else "application/octet-stream"

    return FileResponse(
        path=str(target_path),
        filename=filename,
        media_type=media_type
    )
