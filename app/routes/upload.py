import pathlib
import shutil
from datetime import datetime, timezone

from fastapi import HTTPException, UploadFile, File, Form

from app.services.db import submissions
from app.services.extractor import extract_text
from app.services.parser import parse_submission

UPLOAD_DIR = pathlib.Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def upload_submission(
        candidate_id: str = Form(...),
        file: UploadFile = File(...)
):
    suffix = pathlib.Path(file.filename).suffix
    tmp_path = UPLOAD_DIR / f"{candidate_id}{suffix}"

    with tmp_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        raw_text = extract_text(str(tmp_path))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    answers = parse_submission(raw_text)
    if not answers:
        raise HTTPException(status_code=422, detail="Не удалось выделить задания из файла")

    doc = {
        "candidate_id": str(candidate_id),
        "raw_text": raw_text,
        "answers": answers,
        "created_at": datetime.now(timezone.utc)
    }

    submissions.insert_one(doc)

    doc.pop("_id", None)
    return {
        "candidate_id": candidate_id,
        "questions_found": list(answers.keys()),
        "answers": answers
    }
