from pydantic import BaseModel


class CheckRequest(BaseModel):
    task_id: str
    reference_answer_id: str
    prompt_id: str
    candidate_answer: str