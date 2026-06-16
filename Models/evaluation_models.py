from pydantic import BaseModel


class ToulminEvaluationResult(BaseModel):

    total_score: float

    claim_score: float
    data_score: float
    warrant_score: float
    backing_score: float
    rebuttal_score: float

    completeness: float

    level: str
    feedback: list[str] = []
