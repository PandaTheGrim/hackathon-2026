from pydantic import BaseModel

from app.models.CriterionResult import CriterionResult


class AssessmentResult(BaseModel):
    score: int
    score_rationale: str
    criteria: dict[str, CriterionResult]
    feedback_for_team: str
    feedback_for_candidate: str