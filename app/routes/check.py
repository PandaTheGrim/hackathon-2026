from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.CheckRequest import CheckRequest
from app.services.db import results_collection
from app.services.llm import run_check


def check_assignment(request: CheckRequest):
    try:
        result = run_check(request.task_id, request.reference_answer_id, request.prompt_id, request.candidate_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    doc = result.model_dump()
    doc.update({
        "task_id": request.task_id,
        "reference_answer_id": request.reference_answer_id,
        "prompt_id": request.prompt_id,
        "created_at": datetime.now(timezone.utc)
    })

    results_collection.insert_one(doc)
    doc.pop("_id", None)

    return doc
