import time
import logging
from typing import Dict, Any
from app.agents.state import AgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("summarizer_agent")


def summarizer_node(state: AgentState) -> Dict[str, Any]:
    """
    Summarizer Agent:
    Uses Google Gemini to synthesize a structured, academic-grade research summary.
    """
    start_time = time.time()
    logs = list(state.get("agent_logs", []))

    if state.get("error"):
        return {"current_step": "SKIPPED_DUE_TO_ERROR"}

    sections = state.get("raw_sections", {})
    metadata = state.get("paper_metadata", {})
    title = metadata.get("title") or "Academic Research Paper"

    logger.info(f"Summarizer Agent starting analysis for paper: {title}")

    # Prepare context from paper sections
    context_parts = [f"Title: {title}"]
    for sec_name, content in sections.items():
        if sec_name != "references":  # Omit bibliography to keep prompt focused
            context_parts.append(f"\n--- Section: {sec_name.upper()} ---\n{content[:6000]}")

    full_context = "\n".join(context_parts)

    system_instruction = (
        "You are an expert AI Research Scientist and Peer Reviewer. Your role is to thoroughly "
        "analyze academic research papers and generate comprehensive, rigorously structured summaries. "
        "Always respond with valid JSON matching the exact requested keys without markdown fences."
    )

    prompt = f"""
Analyze the following research paper and generate a structured summary in JSON format.

{full_context[:30000]}

Your output must be a single JSON object with the following exact keys:
{{
  "tldr": "A crisp 2-3 sentence executive summary of the paper and its primary breakthrough.",
  "problem_statement": "The core problem, research gap, or challenge the paper aims to resolve.",
  "key_contributions": "Bulleted list or paragraph detailing the 3-5 novel innovations or contributions.",
  "methodology": "Detailed breakdown of the mathematical, architectural, or algorithmic methodology proposed.",
  "experimental_results": "Summary of datasets used, benchmark comparisons, metrics (accuracy, F1, latency), and quantitative findings.",
  "limitations_future_work": "Identified limitations, ethical considerations, or future research directions noted by the authors."
}}
"""

    try:
        if not gemini_service.is_configured():
            warning_msg = "Gemini API key is not configured. Setting placeholder summary."
            logs.append({
                "agent_name": "Summarizer Agent",
                "log_level": "WARNING",
                "message": warning_msg,
                "execution_time_ms": int((time.time() - start_time) * 1000)
            })
            return {
                "summary_data": {
                    "tldr": "Gemini API key is not configured in .env. Please configure GEMINI_API_KEY to generate live AI summaries.",
                    "problem_statement": "Configuration required.",
                    "key_contributions": "Pending Gemini API Key.",
                    "methodology": "Pending Gemini API Key.",
                    "experimental_results": "Pending Gemini API Key.",
                    "limitations_future_work": "Pending Gemini API Key."
                },
                "current_step": "SUMMARIZED_UNCONFIGURED",
                "agent_logs": logs
            }

        summary_json = gemini_service.generate_json(prompt=prompt, system_instruction=system_instruction)

        logs.append({
            "agent_name": "Summarizer Agent",
            "log_level": "INFO",
            "message": "Successfully synthesized academic summary via Gemini.",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })

        return {
            "summary_data": summary_json,
            "current_step": "PAPER_SUMMARIZED",
            "agent_logs": logs
        }

    except Exception as e:
        logger.error(f"Error in Summarizer Agent: {e}")
        logs.append({
            "agent_name": "Summarizer Agent",
            "log_level": "ERROR",
            "message": f"Summary generation failed: {str(e)}",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })
        return {
            "error": f"Summarizer Agent failed: {str(e)}",
            "current_step": "SUMMARIZER_ERROR",
            "agent_logs": logs
        }
