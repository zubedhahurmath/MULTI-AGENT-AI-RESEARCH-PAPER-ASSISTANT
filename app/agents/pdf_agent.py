import time
import logging
from typing import Dict, Any
from app.agents.state import AgentState
from app.services.pdf_extractor import pdf_extractor_service

logger = logging.getLogger("pdf_agent")


def pdf_processing_node(state: AgentState) -> Dict[str, Any]:
    """
    PDF Processing Agent:
    Extracts text, structural sections, and metadata from the uploaded research paper PDF.
    """
    start_time = time.time()
    file_path = state.get("file_path", "")
    paper_id = state.get("paper_id")
    logs = list(state.get("agent_logs", []))

    logger.info(f"PDF Processing Agent invoked for paper_id={paper_id}, path={file_path}")

    try:
        extraction_result = pdf_extractor_service.extract_paper(file_path)

        if not extraction_result.get("success"):
            error_msg = extraction_result.get("error", "Failed to extract text from PDF.")
            logs.append({
                "agent_name": "PDF Processing Agent",
                "log_level": "ERROR",
                "message": error_msg,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            })
            return {
                "error": error_msg,
                "current_step": "PDF_EXTRACTION_FAILED",
                "agent_logs": logs
            }

        if extraction_result.get("is_scanned"):
            warning_msg = "PDF contains scanned images with minimal extractable text. OCR is recommended for full accuracy."
            logs.append({
                "agent_name": "PDF Processing Agent",
                "log_level": "WARNING",
                "message": warning_msg,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            })

        metadata = extraction_result.get("metadata", {})
        sections = extraction_result.get("sections", {})
        raw_text = extraction_result.get("raw_text", "")

        logs.append({
            "agent_name": "PDF Processing Agent",
            "log_level": "INFO",
            "message": f"Successfully extracted {metadata.get('total_pages', 0)} pages and {len(sections)} structural sections.",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })

        return {
            "paper_metadata": metadata,
            "raw_sections": sections,
            "current_step": "PDF_EXTRACTED",
            "agent_logs": logs,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error in PDF Processing Agent: {e}")
        logs.append({
            "agent_name": "PDF Processing Agent",
            "log_level": "ERROR",
            "message": f"Extraction exception: {str(e)}",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })
        return {
            "error": str(e),
            "current_step": "PDF_EXTRACTION_ERROR",
            "agent_logs": logs
        }
