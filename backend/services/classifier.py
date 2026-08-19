from backend.schemas import TicketClassificationResult
from backend.services.llm_client import call_with_fallback

SYSTEM_PROMPT = (
    "You are an AI Support Routing Agent for 'Nebula'. "
    "Your task is to analyze customer support tickets and output structured JSON.\n\n"
    "ROUTING RULES:\n"
    "1. If a user explicitly asks for money back, the category MUST be 'refund_request', "
    "even if they mention bugs or bad experts.\n"
    "2. TONE != PRIORITY. An aggressive tone or CAPS LOCK for a trivial issue is STILL low/medium priority. "
    "Only legal threats, mass outages, or lost money justify 'high' or 'critical'.\n"
    "3. AUTOMATION LIMITS (Human-in-the-loop): If the user threatens legal action, mentions harassment, "
    "or if you are unsure, set 'requires_human_review' to True and explain why in 'human_review_reason'."
)


async def classify_ticket(ticket_text: str) -> TicketClassificationResult:
    """
    Викликає ШІ та автоматично парсить відповідь у TicketClassificationResult.

    Надійність: мережеві збої (timeout/rate limit/5xx) і невалідний structured
    output обробляються всередині call_with_fallback (retry + backoff + fallback
    модель). Тут ми лише формуємо запит; помилки, які лишились нерозв'язними,
    підіймаються вище і мапляться в HTTP-статуси в main.py.
    """
    return await call_with_fallback(
        response_model=TicketClassificationResult,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ticket_text},
        ],
        max_tokens=1024,
    )
