from fastapi import HTTPException
from app.services.db import results_collection
from bson import ObjectId


def get_results(candidate_id: str, result_id: str = None):
    if result_id:
        try:
            doc = results_collection.find_one({"_id": ObjectId(result_id), "candidate_id": candidate_id})
        except Exception:
            raise HTTPException(status_code=400, detail="Некорректный result_id")

        if not doc:
            raise HTTPException(status_code=404, detail="Результат не найден")

        doc["_id"] = str(doc["_id"])

        return doc

    docs = list(results_collection.find({"candidate_id": candidate_id}))
    if not docs:
        raise HTTPException(status_code=404, detail="Результаты кандидата не найдены")

    for doc in docs:
        doc["_id"] = str(doc["_id"])

    return docs
