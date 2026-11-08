import json
import logging
from datetime import datetime
from typing import Dict, Any
from app.agents.state import AgentState
from app.database import SessionLocal
from app.models import Paper, PaperMetadata, PaperSummary, GeneratedAsset, AgentLog

logger = logging.getLogger("manager_agent")


def manager_supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    Manager Agent (Supervisor):
    Consolidates state from all worker agents, performs consistency validation,
    and persists structured data, summaries, generated assets, and audit logs into SQLite.
    """
    paper_id = state.get("paper_id")
    error = state.get("error")
    logs = list(state.get("agent_logs", []))

    logger.info(f"Manager Agent finalizing workflow for paper_id={paper_id}")

    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error(f"Paper with id={paper_id} not found in database.")
            return {"current_step": "MANAGER_ERROR", "error": "Paper record not found."}

        # If fatal error occurred during workflow
        if error:
            paper.status = "FAILED"
            paper.error_message = error
            paper.completed_at = datetime.utcnow()
            db.commit()
            return {"current_step": "FAILED"}

        # 1. Persist Paper Metadata
        metadata = state.get("paper_metadata", {})
        if metadata:
            existing_meta = db.query(PaperMetadata).filter(PaperMetadata.paper_id == paper_id).first()
            if not existing_meta:
                existing_meta = PaperMetadata(paper_id=paper_id)
                db.add(existing_meta)

            existing_meta.title = metadata.get("title") or paper.original_filename
            existing_meta.authors = metadata.get("authors")
            existing_meta.total_pages = metadata.get("total_pages", 0)
            existing_meta.abstract_text = state.get("raw_sections", {}).get("abstract")

        # 2. Persist Paper Summary
        summary = state.get("summary_data", {})
        if summary:
            existing_summary = db.query(PaperSummary).filter(PaperSummary.paper_id == paper_id).first()
            if not existing_summary:
                existing_summary = PaperSummary(paper_id=paper_id)
                db.add(existing_summary)

            existing_summary.tldr = summary.get("tldr")
            existing_summary.problem_statement = summary.get("problem_statement")
            existing_summary.key_contributions = summary.get("key_contributions")
            existing_summary.methodology = summary.get("methodology")
            existing_summary.experimental_results = summary.get("experimental_results")
            existing_summary.limitations_future_work = summary.get("limitations_future_work")
            existing_summary.raw_json = json.dumps(summary)

        # 3. Persist PPT Presentation Asset
        ppt_path = state.get("ppt_file_path")
        if ppt_path:
            ppt_asset = GeneratedAsset(
                paper_id=paper_id,
                asset_type="presentation",
                title=f"Presentation: {metadata.get('title') or paper.original_filename}",
                file_path=ppt_path,
                metadata_json=json.dumps({"slides": state.get("ppt_outline", [])})
            )
            db.add(ppt_asset)

        # 4. Persist Email Assets
        email_drafts = state.get("email_drafts", [])
        for draft in email_drafts:
            email_asset = GeneratedAsset(
                paper_id=paper_id,
                asset_type="email",
                title=draft.get("subject", "Research Paper Email"),
                content_text=draft.get("body", ""),
                metadata_json=json.dumps({
                    "email_type": draft.get("email_type"),
                    "target_audience": draft.get("target_audience"),
                    "subject": draft.get("subject")
                })
            )
            db.add(email_asset)

        # 5. Persist Code Implementation Asset
        code_sol = state.get("code_solution", {})
        if code_sol and "code" in code_sol:
            code_asset = GeneratedAsset(
                paper_id=paper_id,
                asset_type="code",
                title=f"Implementation: {code_sol.get('framework', 'Python Algorithm')}",
                content_text=code_sol.get("code"),
                metadata_json=json.dumps({
                    "language": code_sol.get("language", "python"),
                    "framework": code_sol.get("framework"),
                    "explanation": code_sol.get("explanation"),
                    "dependencies": code_sol.get("dependencies", [])
                })
            )
            db.add(code_asset)

        # 6. Persist Agent Logs
        for log_entry in logs:
            db_log = AgentLog(
                paper_id=paper_id,
                agent_name=log_entry.get("agent_name", "Unknown Agent"),
                log_level=log_entry.get("log_level", "INFO"),
                message=log_entry.get("message", ""),
                execution_time_ms=log_entry.get("execution_time_ms", 0)
            )
            db.add(db_log)

        # Mark paper as completed
        paper.status = "COMPLETED"
        paper.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Manager Agent successfully committed all assets for paper_id={paper_id}")
        return {"current_step": "COMPLETED"}

    except Exception as e:
        logger.error(f"Error in Manager Agent database commit: {e}")
        db.rollback()
        return {"current_step": "MANAGER_COMMIT_ERROR", "error": str(e)}
    finally:
        db.close()
