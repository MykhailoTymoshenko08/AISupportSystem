import os
from pathlib import Path
import instructor
from openai import AsyncOpenAI
from backend.schemas import CopilotResponse

client = instructor.from_openai(
    AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY"),
    ),
    mode=instructor.Mode.JSON,
)


KB_DIR = Path(__file__).parent.parent / "kb"

def load_kb_article(filename: str, default_text: str) -> str:
    """Читає файл бази знань. Якщо файлу немає, повертає дефолтний текст (щоб нічого не впало)."""
    filepath = KB_DIR / filename
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return default_text

MOCK_KB = {
    "refund": load_kb_article("refund_policy.txt", "Refund Policy: 14 days limit."),
    "bug": load_kb_article("bug_rules.txt", "Bug Reports: Apologize and ask for app version."),
    "expert": load_kb_article("expert_rules.txt", "Expert Complaints: Offer replacement session."),
    "default": load_kb_article("default_policy.txt", "General Policy: Be polite.")
}

def retrieve_knowledge(text: str) -> str:
    text_lower = text.lower()
    if "refund" in text_lower or "money" in text_lower or "pay" in text_lower:
        return MOCK_KB["refund"]
    elif "bug" in text_lower or "crash" in text_lower or "not working" in text_lower:
        return MOCK_KB["bug"]
    elif "expert" in text_lower or "session" in text_lower or "consultant" in text_lower:
        return MOCK_KB["expert"]
    return MOCK_KB["default"]

# 4. Головна функція
async def generate_copilot_response(ticket_text: str) -> CopilotResponse:
    # Дістаємо статтю з бази знань (Retrieval)
    kb_article = retrieve_knowledge(ticket_text)
    
    # Готуємо промпт
    prompt = f"User Ticket: '{ticket_text}'\n\nCompany Policy to follow: '{kb_article}'"
    
    # Викликаємо модель
    model_name = 'nvidia/nemotron-3-ultra-550b-a55b:free' 
    
    result = await client.chat.completions.create(
        model=model_name,
        response_model=CopilotResponse,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI Copilot for support agents at 'Nebula'. "
                    "Your goal is to help agents reply to users by providing a summary, "
                    "3 drafted replies (Formal, Empathetic, Short).\n\n"
                    "RULES FOR REPLIES:\n"
                    "- Formal: Professional, direct, using company tone.\n"
                    "- Empathetic: Warm, validating user's feelings, apologetic if needed.\n"
                    "- Short: Maximum 2 sentences, straight to the point.\n"
                    "- LIMITATION: NEVER promise money back unless the provided policy explicitly allows it."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1500,
    )
    
    # Надійно прикріплюємо цитату з бази знань напряму, щоб ШІ її не вигадав
    result.kb_citation = kb_article
    
    return result