from pydantic import BaseModel, Field
from enum import Enum

# categories
class TicketCategory(str, Enum):
    SUBSCRIPTION_BILLING = "subscription_billing"
    BUG_REPORT = "bug_report"
    EXPERT_COMPLAINT = "expert_complaint"
    REFUND_REQUEST = "refund_request"
    GENERAL_QUESTION = "general_question"
    OTHER = "other"

# prioritets
class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# list of actions
class NextStepAction(str, Enum):
    ROUTE_TO_BILLING = "route_to_billing"
    ROUTE_TO_TECH = "route_to_tech"
    ROUTE_TO_REFUNDS = "route_to_refunds"
    AUTO_REPLY = "auto_reply"
    ESCALATE_TO_HUMAN = "escalate_to_human"

# final schema (output data)
class TicketClassificationResult(BaseModel):
    category: TicketCategory = Field(
        description="Категорія звернення. Якщо користувач просить повернути гроші, це завжди refund_request."
    )
    priority: TicketPriority = Field(
        description="Пріоритет. Critical - лише для погроз судом, серйозної шкоди або масових збоїв."
    )
    next_step: NextStepAction = Field(
        description="Рекомендований наступний крок системи."
    )
    requires_human_review: bool = Field(
        description="True, якщо тон надто агресивний, є погрози, або якщо запит складний і ШІ не впевнений."
    )
    human_review_reason: str | None = Field(
        default=None, 
        description="Якщо requires_human_review=True, коротко поясни чому (напр. 'Погроза судом' або 'Складна скарга на експерта')."
    )

# input data
class TicketRequest(BaseModel):
    text: str

class ReplyOption(BaseModel):
    tone: str = Field(description="Тон відповіді: 'Formal', 'Empathetic' або 'Short'.")
    text: str = Field(description="Згенерований текст відповіді для клієнта.")

class CopilotResponse(BaseModel):
    summary: str = Field(description="Коротке саммарі тікету (1-2 речення).")
    replies: list[ReplyOption] = Field(description="Рівно 3 варіанти відповіді різного тону.")
    kb_citation: str = Field(description="Правило з бази знань, на яке спирався ШІ при генерації відповідей.")