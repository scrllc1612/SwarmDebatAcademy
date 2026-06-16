from pydantic import BaseModel, Field
from Models.moderator_models import DebateSummary
from uuid import uuid4


class ToulminArgument(BaseModel):

    claim: str
    data: str
    warrant: str
    backing: str
    rebuttal: str
    speech: str = ""

    stance: str

    round_number: int


class DebateRound(BaseModel):

    round_number: int

    pro_argument: ToulminArgument

    contra_argument: ToulminArgument

    moderator_summary: DebateSummary | None = None


class DebateState(BaseModel):

    debate_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    topic: str

    current_round: int = 1

    rounds: list[DebateRound] = Field(
        default_factory=list
    )

    is_finished: bool = False
