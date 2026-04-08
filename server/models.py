from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CITE_POLICY = "cite_policy"
    PROVIDE_EVIDENCE = "provide_evidence"
    ESCALATE = "escalate"
    REQUEST_SUPERVISOR = "request_supervisor"
    ACCEPT_PARTIAL = "accept_partial"
    REJECT_OFFER = "reject_offer"
    REQUEST_ITEMIZED_BILL = "request_itemized_bill"
    FILE_FORMAL_APPEAL = "file_formal_appeal"
    CITE_PRECEDENT = "cite_precedent"
    THREATEN_REGULATORY_COMPLAINT = "threaten_regulatory_complaint"
    PROVIDE_MEDICAL_RECORDS = "provide_medical_records"
    REQUEST_PEER_REVIEW = "request_peer_review"


class Action(BaseModel):
    action_type: ActionType
    argument: str = Field(description="Free-text argument supporting the chosen action")


class InsurerResponse(BaseModel):
    message: str
    offer_amount: float = 0.0
    is_final: bool = False


class Observation(BaseModel):
    step: int
    insurer_response: InsurerResponse
    current_offer: float
    max_recoverable: float
    steps_remaining: int
    done: bool
    reward: float
    cumulative_reward: float


class State(BaseModel):
    task_id: str
    description: str
    claim_amount: float
    denied_amount: float
    max_recoverable: float
    current_offer: float
    step: int
    max_steps: int = 8
    done: bool = False
    history: list[dict] = Field(default_factory=list)
    cumulative_reward: float = 0.0
    difficulty: str = "easy"


class ResetRequest(BaseModel):
    task_id: Optional[str] = None


class StepRequest(BaseModel):
    action: Action
