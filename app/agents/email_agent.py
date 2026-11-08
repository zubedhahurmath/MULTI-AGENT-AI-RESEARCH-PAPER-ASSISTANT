import time
import logging
from typing import Dict, Any, List
from app.agents.state import AgentState
from app.services.gemini_client import gemini_service

logger = logging.getLogger("email_agent")


def email_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Email Generator Agent:
    Drafts 3 distinct professional persona-based emails (Advisor, Peer, Author)
    synthesizing the research paper's findings.
    """
    start_time = time.time()
    logs = list(state.get("agent_logs", []))

    if state.get("error"):
        return {"current_step": "SKIPPED_DUE_TO_ERROR"}

    summary = state.get("summary_data", {})
    metadata = state.get("paper_metadata", {})
    title = metadata.get("title") or "Recent Research Paper"
    authors = metadata.get("authors") or "Authors"

    logger.info(f"Email Generator Agent drafting correspondence for paper: {title}")

    system_instruction = (
        "You are an academic communication specialist. Draft three distinct, professional emails "
        "concerning a research paper. Respond with a valid JSON array of 3 email objects."
    )

    prompt = f"""
Draft 3 tailored emails about the following research paper:

Paper Title: {title}
Authors: {authors}
Executive Summary: {summary.get('tldr', '')}
Key Contributions: {summary.get('key_contributions', '')}
Methodology: {summary.get('methodology', '')}

Generate a JSON array of 3 objects with keys:
- "email_type": "advisor_briefing" | "peer_discussion" | "author_inquiry"
- "target_audience": string
- "subject": string
- "body": string

Personas:
1. "advisor_briefing": Formal email to a thesis advisor / research supervisor explaining how this paper is relevant to your ongoing lab work and why it is worth discussing.
2. "peer_discussion": Collaborative, engaging email to a student study group or colleague highlighting the core takeaways and practical implications.
3. "author_inquiry": Courteous, scholarly outreach to the paper's primary author praising their contribution and politely asking a question regarding implementation or dataset availability.
"""

    email_drafts: List[Dict[str, Any]] = []

    try:
        if gemini_service.is_configured():
            raw_emails = gemini_service.generate_json(prompt=prompt, system_instruction=system_instruction)
            if isinstance(raw_emails, list):
                email_drafts = raw_emails
            elif isinstance(raw_emails, dict) and "emails" in raw_emails:
                email_drafts = raw_emails["emails"]

        # Robust fallbacks if unconfigured
        if not email_drafts:
            email_drafts = [
                {
                    "email_type": "advisor_briefing",
                    "target_audience": "Research Advisor / Thesis Guide",
                    "subject": f"Research Update: Key Findings from '{title[:50]}...'",
                    "body": (
                        f"Dear Professor,\n\n"
                        f"I recently reviewed the paper titled \"{title}\" by {authors}. "
                        f"The authors tackle {summary.get('problem_statement', 'a central challenge in the field')}.\n\n"
                        f"Key Contributions:\n{summary.get('key_contributions', 'Significant architectural innovations.')}\n\n"
                        f"I believe this methodology could provide useful insights for our current project. "
                        f"I would appreciate your guidance during our next lab meeting.\n\n"
                        f"Best regards,\n[Your Name]"
                    )
                },
                {
                    "email_type": "peer_discussion",
                    "target_audience": "Colleagues / Lab Peers",
                    "subject": f"Interesting paper for reading group: {title[:50]}...",
                    "body": (
                        f"Hi Team,\n\n"
                        f"Check out this interesting paper: \"{title}\".\n\n"
                        f"Quick TL;DR:\n{summary.get('tldr', 'Important findings.')}\n\n"
                        f"The way they designed the methodology ({summary.get('methodology', 'novel pipeline')[:120]}...) "
                        f"is quite clean and might be worth implementing in our benchmarks.\n\n"
                        f"Let me know your thoughts!\n[Your Name]"
                    )
                },
                {
                    "email_type": "author_inquiry",
                    "target_audience": "Paper Authors",
                    "subject": f"Question regarding your paper '{title[:50]}...'",
                    "body": (
                        f"Dear {authors},\n\n"
                        f"I am writing to express my appreciation for your paper titled \"{title}\". "
                        f"Your approach towards {summary.get('problem_statement', 'the subject problem')[:100]} is insightful.\n\n"
                        f"I am replicating the experiments described in Section 4 and had a brief question regarding "
                        f"the hyperparameter tuning and reproducibility script.\n\n"
                        f"Thank you for your valuable contribution to the research community.\n\n"
                        f"Sincerely,\n[Your Name]\n[Your Affiliation]"
                    )
                }
            ]

        logs.append({
            "agent_name": "Email Generator Agent",
            "log_level": "INFO",
            "message": f"Successfully drafted {len(email_drafts)} persona-based emails.",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })

        return {
            "email_drafts": email_drafts,
            "current_step": "EMAILS_GENERATED",
            "agent_logs": logs
        }

    except Exception as e:
        logger.error(f"Error in Email Generator Agent: {e}")
        logs.append({
            "agent_name": "Email Generator Agent",
            "log_level": "ERROR",
            "message": f"Email drafting failed: {str(e)}",
            "execution_time_ms": int((time.time() - start_time) * 1000)
        })
        return {
            "error": f"Email Generator Agent failed: {str(e)}",
            "current_step": "EMAIL_ERROR",
            "agent_logs": logs
        }
