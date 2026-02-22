from pydantic import BaseModel


class CriterionResult(BaseModel):
    score: int
    comment: str