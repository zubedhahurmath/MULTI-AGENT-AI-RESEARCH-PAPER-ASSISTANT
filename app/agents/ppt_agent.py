import time
import logging
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.services.gemini_client import gemini_service
from app.services.ppt_builder import ppt_builder_service

logger = logging.getLogger("ppt_agent")


def ppt_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    PPT Generator Agent:
    Transforms research insights into a slide deck outline via Gemini,
    then compiles a downloadable .pptx file using python-pptx.
    """
    start_time = time.time()
    logs = list(state.get("agent_logs", []))

    if state.get("error"):
        return {"current_step": "SKIPPED_DUE_TO_ERROR"}

    summary = state.get("summary_data", {})
    metadata = state.get("paper_metadata", {})
    title = metadata.get("title") or "Academic Research Presentation"
    authors = metadata.get("authors")
    paper_id = state.get("paper_id")

    logger.info(f"PPT Generator Agent processing paper_id={paper_id}")

    system_instruction = (
        "You are an academic presentation designer. Create a clean, engaging 7-8 slide conference presentation outline "
        "based on the provided paper summary. Respond with a valid JSON array of slide objects."
    )

    prompt = f"""
Create a PowerPoint presentation structure for the following research paper:

Title: {title}
Authors: {authors or 'N/A'}

Summary:
- TL;DR: {summary.get('tldr', '')}
- Problem: {summary.get('problem_statement', '')}
- Methodology: {summary.get('methodology', '')}
- Results: {summary.get('experimental_results', '')}
- Limitations & Future: {summary.get('limitations_future_work', '')}

Return a JSON array where each object has:
- "title": string (concise slide title)
- "category": string (e.g., "MOTIVATION", "ARCHITECTURE", "EVALUATION", "CONCLUSION")
- "bullets": array of 3-4 concise string takeaway points
- "speaker_notes": string (brief talking points for the presenter)

Standard Slides to include:
1. Motivation & Problem Statement
2. Research Gap & Prior Limitations
3. Proposed System Architecture / Methodology
4. Algorithmic Workflow & Key Formulations
5. Experimental Setup & Benchmarks
6. Quantitative Results & Key Findings
7. Limitations & Future Directions
8. Conclusion & Takeaways
"""

    slides_outline: List[Dict[str, Any]] = []

    try:
        if gemini_service.is_configured():
            raw_outline = gemini_service.generate_json(prompt=prompt, system_instruction=system_instruction)
            if isinstance(raw_outline, list):
                slides_outline = raw_outline
            elif isinstance(raw_outline, dict) and "slides" in raw_outline:
                slides_outline = raw_outline["slides"]
            else:
                slides_outline = []

        # Fallback slides outline if Gemini is not configured or returns empty list
        if not slides_outline:
            slides_outline = [
                {
                    "title": "Motivation & Problem Statement",
                    "category": "PROBLEM",
                    "bullets": [
                        summary.get("problem_statement", "Critical challenges in the problem domain.")[:120],
                        "Need for reproducible and scalable algorithmic formulations.",
                        "Existing state-of-the-art approaches face scalability limitations."
                    ],
                    "speaker_notes": "Introduce the motivation and core challenge."
                },
                {
                    "title": "Proposed Methodology",
                    "category": "METHODOLOGY",
                    "bullets": [
                        summary.get("methodology", "Core architecture and algorithmic steps.")[:120],
                        "Engineered for computational efficiency and robust generalization.",
                        "Integrated end-to-end processing pipeline."
                    ],
                    "speaker_notes": "Explain the architectural components."
                },
                {
                    "title": "Experimental Results",
                    "category": "RESULTS",
                    "bullets": [
                        summary.get("experimental_results", "Quantitative findings and benchmark comparisons.")[:120],
                        "Demonstrates performance gains across standard metrics.",
                        "Validation on benchmark datasets confirms theoretical claims."
                    ],
                    "speaker_notes": "Highlight empirical findings."
                },
                {
                    "title": "Conclusion & Future Work",
                    "category": "CONCLUSION",
                    "bullets": [
                        summary.get("limitations_future_work", "Promising avenues for future expansion.")[:120],
                        "Paves the way for improved research automation.",
                        "Open questions for subsequent academic exploration."
                    ],
                    "speaker_notes": "Conclude and open for questions."
                }
            ]

        # Build .pptx presentation file
        file_path = ppt_builder_service.create_presentation(
            paper_title=title,
            authors=authors,
            slides_data=slides_outline,
            paper_id=paper_id
        )

        logs.append({
            "agent_name": "PPT Generator Agent",
            "log_level": "INFO",
            "message": f"Successfully created presentation deck with {len(slides_outline) + 1} slides.",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })

        return {
            "ppt_file_path": file_path,
            "ppt_outline": slides_outline,
            "current_step": "PPT_GENERATED",
            "agent_logs": logs
        }

    except Exception as e:
        logger.error(f"Error in PPT Generator Agent: {e}")
        logs.append({
            "agent_name": "PPT Generator Agent",
            "log_level": "ERROR",
            "message": f"Presentation creation failed: {str(e)}",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })
        return {
            "error": f"PPT Generator Agent failed: {str(e)}",
            "current_step": "PPT_ERROR",
            "agent_logs": logs
        }
