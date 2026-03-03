import csv
import io

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.services.db import results_collection


def export_results_csv(candidate_id: str = None):
    query = {"candidate_id": candidate_id} if candidate_id else {}
    docs = list(results_collection.find(query))

    if not docs:
        raise HTTPException(status_code=404, detail="Результаты не найдены")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "result_id", "candidate_id", "task_id", "reference_answer_id",
        "score", "score_rationale",
        "correctness_score", "correctness_comment",
        "completeness_score", "completeness_comment",
        "style_score", "style_comment",
        "edge_cases_score", "edge_cases_comment",
        "feedback_for_team", "feedback_for_candidate",
        "created_at"
    ])

    for doc in docs:
        criteria = doc.get("criteria", {})
        writer.writerow([
            str(doc.get("_id")),
            doc.get("candidate_id"),
            doc.get("task_id"),
            doc.get("reference_answer_id"),
            doc.get("score"),
            doc.get("score_rationale"),
            criteria.get("correctness", {}).get("score"),
            criteria.get("correctness", {}).get("comment"),
            criteria.get("completeness", {}).get("score"),
            criteria.get("completeness", {}).get("comment"),
            criteria.get("style", {}).get("score"),
            criteria.get("style", {}).get("comment"),
            criteria.get("edge_cases", {}).get("score"),
            criteria.get("edge_cases", {}).get("comment"),
            doc.get("feedback_for_team"),
            doc.get("feedback_for_candidate"),
            doc.get("created_at"),
        ])

    filename = f"candidate_{candidate_id}_results.csv" if candidate_id else "all_results.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
