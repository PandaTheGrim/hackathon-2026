import json
import os
import pathlib

from ollama import Client

from app.models.AssessmentResult import AssessmentResult

ollama_client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

def load_file(folder: str, file_id: str) -> str:
    path = pathlib.Path(f"./data/{folder}/{file_id}.json")
    if path.suffix == ".txt":
        return path.read_text()
    return json.loads(path.read_text())


def run_check(task_id: str, ref_id: str, prompt_id: str, candidate_answer: str) -> AssessmentResult:
    task = load_file("tasks", task_id)
    reference = load_file("reference_answers", ref_id)
    prompt_template = pathlib.Path(f"data/prompts/{prompt_id}.txt").read_text()

    prompt = prompt_template.format(
        task=task["task_text"],  # noqa
        reference=json.dumps(reference, ensure_ascii=False),
        candidate_answer=candidate_answer
    )

    response = ollama_client.chat(
        model="qwen2.5-coder:7b",
        messages=[
            {
                "role": "system",
                "content": "Ты русскоязычный эксперт-проверяющий. Все ответы ТОЛЬКО на русском языке. Оценки строго от 1 до 10."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        format=AssessmentResult.model_json_schema(),
        options={"temperature": 0}
    )

    return AssessmentResult.model_validate_json(response.message.content)
