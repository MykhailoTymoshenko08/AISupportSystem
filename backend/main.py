import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from instructor.core import InstructorRetryException
from openai import AuthenticationError, BadRequestError

from backend.schemas import CopilotResponse, TicketClassificationResult, TicketRequest
from backend.services.classifier import classify_ticket
from backend.services.copilot import generate_copilot_response
from backend.services.llm_client import LLMUnavailableError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nebula.api")

app = FastAPI(
    title="Nebula AI Support Hub",
    description="Internal AI tools for Nebula Support Team",
    version="1.0.0",
)


def _handle_llm_exception(e: Exception, action: str) -> HTTPException:
    if isinstance(e, LLMUnavailableError):
        logger.error("%s: LLM повністю недоступний: %s", action, e)
        return HTTPException(
            status_code=503,
            detail="AI-сервіс тимчасово недоступний (обидві моделі не відповіли). Спробуйте ще раз за кілька хвилин.",
        )
    if isinstance(e, InstructorRetryException):

        logger.error("%s: модель не змогла повернути валідний structured output: %s", action, e)
        return HTTPException(
            status_code=422,
            detail="AI повернув відповідь у неочікуваному форматі навіть після повторних спроб.",
        )
    if isinstance(e, AuthenticationError):
        logger.critical("%s: помилка автентифікації в OpenRouter API: %s", action, e)
        return HTTPException(status_code=500, detail="Помилка конфігурації AI-сервісу (API-ключ).")
    if isinstance(e, BadRequestError):
        logger.warning("%s: некоректний запит до LLM: %s", action, e)
        return HTTPException(status_code=400, detail="Не вдалося обробити текст тікету (можливо, він завеликий).")

    logger.exception("%s: непередбачена помилка", action)
    return HTTPException(status_code=500, detail=f"{action} failed: {e}")


@app.post("/api/v1/tickets/classify", response_model=TicketClassificationResult)
async def api_classify_ticket(request: TicketRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст тікету не може бути порожнім.")
    try:
        return await classify_ticket(request.text)
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_llm_exception(e, "AI Classification")


@app.post("/api/v1/tickets/copilot", response_model=CopilotResponse)
async def api_copilot(request: TicketRequest):
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Текст тікету не може бути порожнім.")
    try:
        return await generate_copilot_response(request.text)
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_llm_exception(e, "Copilot generation")


@app.get("/health")
async def health_check():
    return {"status": "ok"}