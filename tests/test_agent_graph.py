import os
import uuid
import tempfile
import pymupdf as fitz
from unittest.mock import patch
from app.database import SessionLocal, init_db
from app.models import Paper
from app.agents.workflow import run_multi_agent_pipeline


def test_agent_graph_execution_with_mocked_gemini():
    """Test full LangGraph pipeline execution with mocked Gemini responses to avoid API costs."""
    init_db()

    # Create dummy PDF
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, f"graph_test_{uuid.uuid4().hex}.pdf")

    doc = fitz.open()
    doc.set_metadata({"title": "Agent Graph Benchmark Paper", "author": "Research Team"})
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "Agent Graph Benchmark Paper\n\n"
        "ABSTRACT\n"
        "Testing multi-agent workflow state transitions and asset generation.\n\n"
        "1. METHODOLOGY\n"
        "We utilize LangGraph StateGraph with supervisor routing and worker nodes.\n\n"
        "2. EXPERIMENTAL RESULTS\n"
        "Zero errors recorded during state machine traversal.\n"
    )
    doc.save(pdf_path)
    doc.close()

    # Create paper record in DB with unique stored_filename
    db = SessionLocal()
    unique_stored_name = f"paper_graph_{uuid.uuid4().hex}.pdf"
    paper = Paper(
        original_filename="graph_test_paper.pdf",
        stored_filename=unique_stored_name,
        file_path=pdf_path,
        file_size_bytes=os.path.getsize(pdf_path),
        status="PROCESSING"
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    paper_id = paper.id
    db.close()

    # Mock Gemini responses
    mock_summary = {
        "tldr": "A benchmark paper testing LangGraph state transitions.",
        "problem_statement": "Ensuring deterministic agent workflows.",
        "key_contributions": "Designed state machine with supervisor node.",
        "methodology": "LangGraph StateGraph with conditional edges.",
        "experimental_results": "100% test pass rate.",
        "limitations_future_work": "Future work involves adding multimodal agents."
    }

    mock_slides = [
        {"title": "Motivation", "category": "PROBLEM", "bullets": ["Point A", "Point B"], "speaker_notes": "Note 1"},
        {"title": "Architecture", "category": "METHOD", "bullets": ["Point C", "Point D"], "speaker_notes": "Note 2"}
    ]

    mock_emails = [
        {"email_type": "advisor_briefing", "target_audience": "Advisor", "subject": "Update", "body": "Dear Professor..."},
        {"email_type": "peer_discussion", "target_audience": "Peers", "subject": "Check this", "body": "Hey team..."},
        {"email_type": "author_inquiry", "target_audience": "Authors", "subject": "Inquiry", "body": "Dear Authors..."}
    ]

    mock_code = {
        "language": "python",
        "framework": "Pure Python",
        "code": "def run_agent():\n    print('Agent executed successfully')\n\nif __name__ == '__main__':\n    run_agent()",
        "explanation": "Simulates basic agent logic.",
        "dependencies": []
    }

    def mock_generate_json(prompt, system_instruction=None, temperature=0.2):
        if "PowerPoint presentation structure" in prompt:
            return mock_slides
        elif "Draft 3 tailored emails" in prompt:
            return mock_emails
        elif "generate a Python implementation" in prompt:
            return mock_code
        else:
            return mock_summary

    with patch("app.services.gemini_client.gemini_service.is_configured", return_value=True), \
         patch("app.services.gemini_client.gemini_service.generate_json", side_effect=mock_generate_json):

        final_state = run_multi_agent_pipeline(paper_id=paper_id, file_path=pdf_path)

        assert final_state["current_step"] == "COMPLETED"
        assert final_state.get("error") is None

        # Verify artifacts
        assert final_state["summary_data"]["tldr"] == mock_summary["tldr"]
        assert final_state["ppt_file_path"] is not None
        assert os.path.exists(final_state["ppt_file_path"])
        assert len(final_state["email_drafts"]) == 3
        assert "def run_agent" in final_state["code_solution"]["code"]

        # Verify DB state
        db_check = SessionLocal()
        updated_paper = db_check.query(Paper).filter(Paper.id == paper_id).first()
        assert updated_paper.status == "COMPLETED"
        assert updated_paper.summary is not None
        assert len(updated_paper.assets) >= 3
        assert len(updated_paper.logs) >= 3
        db_check.close()

    # Cleanup
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    if final_state.get("ppt_file_path") and os.path.exists(final_state["ppt_file_path"]):
        os.remove(final_state["ppt_file_path"])
