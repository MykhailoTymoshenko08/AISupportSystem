from pathlib import Path

from backend.schemas import CopilotResponse
from backend.services.llm_client import call_with_fallback

# knowledge base lives in backend/knowledge (the old path pointed to a non-existent "kb" folder,
# so the real policy files were never loaded and hardcoded defaults were used instead)
KB_DIR = Path(__file__).parent.parent / "knowledge"


def load_kb_article(filename: str, default_text: str) -> str:
    """reads a kb file; falls back to default text so the service never crashes on a missing file"""
    filepath = KB_DIR / filename
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return default_text


MOCK_KB = {
    "refund": load_kb_article("refund_policy.txt", "Refund Policy: 14 days limit."),
    "bug": load_kb_article("bug_rules.txt", "Bug Reports: Apologize and ask for app version."),
    "expert": load_kb_article("expert_rules.txt", "Expert Complaints: Offer replacement session."),
    "default": load_kb_article("default_policy.txt", "General Policy: Be polite."),
}

SYSTEM_PROMPT = (
    "You are an AI Copilot for support agents at 'Nebula'. "
    "Your goal is to help agents reply to users by providing a summary, "
    "3 drafted replies (Formal, Empathetic, Short).\n\n"
    "RULES FOR REPLIES:\n"
    "- Formal: Professional, direct, using company tone.\n"
    "- Empathetic: Warm, validating user's feelings, apologetic if needed.\n"
    "- Short: Maximum 2 sentences, straight to the point.\n"
    "- LIMITATION: NEVER promise money back unless the provided policy explicitly allows it."
)


def retrieve_knowledge(text: str) -> str:
    """keyword retrieval - enough for a handful of short policies, swappable for a vector store later"""
    text_lower = text.lower()
    if "refund" in text_lower or "money" in text_lower or "pay" in text_lower:
        return MOCK_KB["refund"]
    if "bug" in text_lower or "crash" in text_lower or "not working" in text_lower:
        return MOCK_KB["bug"]
    if "expert" in text_lower or "session" in text_lower or "consultant" in text_lower:
        return MOCK_KB["expert"]
    return MOCK_KB["default"]


async def generate_copilot_response(ticket_text: str) -> CopilotResponse:
    kb_article = retrieve_knowledge(ticket_text)
    prompt = f"User Ticket: '{ticket_text}'\n\nCompany Policy to follow: '{kb_article}'"

    # same retry + backoff + fallback model path as the classifier
    result = await call_with_fallback(
        response_model=CopilotResponse,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
    )

    # attach the citation from code so the model can't invent it
    result.kb_citation = kb_article
    return result
