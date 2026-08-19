
import logging
import os

import instructor
from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("nebula.llm")

PRIMARY_MODEL = os.environ.get("PRIMARY_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
FALLBACK_MODEL = os.environ.get("FALLBACK_MODEL", "google/gemini-2.0-flash-lite-preview-02-05:free")

REQUEST_TIMEOUT_SECONDS = 30.0
MAX_NETWORK_ATTEMPTS = 3      
VALIDATION_RETRIES_PER_CALL = 2  

_raw_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    timeout=REQUEST_TIMEOUT_SECONDS,
    max_retries=0,
)

client = instructor.from_openai(_raw_client, mode=instructor.Mode.JSON)

RETRIABLE_EXCEPTIONS = (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError)


class LLMUnavailableError(Exception):

    def __init__(self, primary_model: str, fallback_model: str, primary_error: Exception, fallback_error: Exception):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        super().__init__(
            f"Обидві моделі недоступні. "
            f"{primary_model}: {primary_error!r}; {fallback_model}: {fallback_error!r}"
        )


def _log_retry(retry_state):
    exc = retry_state.outcome.exception()
    logger.warning(
        "LLM call attempt %s failed (%s: %s), retrying...",
        retry_state.attempt_number, type(exc).__name__, exc,
    )


@retry(
    reraise=True,
    stop=stop_after_attempt(MAX_NETWORK_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(RETRIABLE_EXCEPTIONS),
    before_sleep=_log_retry,
)
async def _call_model(model_name: str, **kwargs):
    return await client.chat.completions.create(
        model=model_name,
        max_retries=VALIDATION_RETRIES_PER_CALL,
        **kwargs,
    )


async def call_with_fallback(**kwargs):
    try:
        return await _call_model(PRIMARY_MODEL, **kwargs)
    except RETRIABLE_EXCEPTIONS as primary_error:
        logger.error(
            "Primary model '%s' unavailable after %s attempts: %s. Falling back to '%s'.",
            PRIMARY_MODEL, MAX_NETWORK_ATTEMPTS, primary_error, FALLBACK_MODEL,
        )
        try:
            return await _call_model(FALLBACK_MODEL, **kwargs)
        except RETRIABLE_EXCEPTIONS as fallback_error:
            logger.critical(
                "Fallback model '%s' also unavailable after %s attempts: %s",
                FALLBACK_MODEL, MAX_NETWORK_ATTEMPTS, fallback_error,
            )
            raise LLMUnavailableError(PRIMARY_MODEL, FALLBACK_MODEL, primary_error, fallback_error) from fallback_error
        