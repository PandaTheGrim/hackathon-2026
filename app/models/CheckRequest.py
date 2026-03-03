from pydantic import BaseModel


class CheckRequest(BaseModel):
    candidate_id: str
    task_id: str
    reference_answer_id: str
    prompt_id: str
    question_number: str