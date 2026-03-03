from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.CheckRequest import CheckRequest
from app.services.db import results_collection, submissions
from app.services.llm import run_check


def check_assignment(request: CheckRequest):
    candidate_id = request.candidate_id
    submission = submissions.find_one({"candidate_id": candidate_id})
    if not submission:
        raise HTTPException(status_code=404, detail=f"Результаты для кандидата {candidate_id} не найдены")

    candidate_answer = submission.get("answers", {}).get(request.question_number)
    if not candidate_answer:
        raise HTTPException(status_code=404, detail=f"Ответ на задание {request.question_number} не найден")

    try:
        result = run_check(request.task_id, request.reference_answer_id, request.prompt_id, candidate_answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    doc = result.model_dump()
    doc.update({
        "candidate_id": request.candidate_id,
        "question_number": request.question_number,
        "task_id": request.task_id,
        "reference_answer_id": request.reference_answer_id,
        "prompt_id": request.prompt_id,
        "created_at": datetime.now(timezone.utc)
    })

    results_collection.insert_one(doc)
    doc.pop("_id", None)

    return doc
