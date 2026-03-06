import json
import os
import pathlib

from ollama import Client

from app.models.AssessmentResult import AssessmentResult

ollama_client = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

def load_file(folder: str, file_id: str) -> str:
    path = pathlib.Path(f"./data/{folder}/{file_id}.json")
    return json.loads(path.read_text())

def read_prompt_optional(path: str) -> str | None:
    p = pathlib.Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else None


def safe_json_loads(s: str) -> dict:
    # на случай, если модель обернет JSON в ```...```
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        # иногда внутри есть "json\n{...}"
        s = s[s.find("{"):] if "{" in s else s
    return json.loads(s)


def run_check(task_id: str, ref_id: str, prompt_id: str, candidate_answer: str) -> AssessmentResult:
    task = load_file("tasks", task_id)
    reference = load_file("reference_answers", ref_id)

    # Если есть шаблон для анализа, то сначала получаем анализ, а потом уже передаем его в основной шаблон. Это позволяет не перегружать основной шаблон и при этом использовать результаты анализа в нем.
    analysis_template = read_prompt_optional(f"data/prompts/{prompt_id}_analysis.txt")
    analysis_json = None
    if analysis_template:
        analysis_prompt = analysis_template % {
            "task": task["task_text"],
            "reference": json.dumps(reference, ensure_ascii=False),
            "candidate_answer": candidate_answer
        }
        analysis_resp = ollama_client.chat(
            model="qwen2.5-coder:7b",
            messages=[
                {"role": "system", "content": "Ты русскоязычный ассистент. Верни только JSON."},
                {"role": "user", "content": analysis_prompt},
            ],
            options={"temperature": 0},
        )
        analysis_json = analysis_resp.message.content.strip()

    prompt_template = pathlib.Path(f"data/prompts/{prompt_id}.txt").read_text(encoding="utf-8")

    # формируем основной промпт, передавая в него результаты анализа, если они есть
    prompt = prompt_template.format(
        task=task["task_text"],  # noqa
        reference=json.dumps(reference, ensure_ascii=False),
        candidate_answer=candidate_answer,
        analysis_json=analysis_json or "{}"
    )

    if analysis_json:
        prompt += "\n\n### Результат анализа (JSON)\n" + analysis_json

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

    result = AssessmentResult.model_validate_json(response.message.content)

    # Если есть шаблон для генерации фидбека, то генерируем фидбек на основе оценки и передаем его в результат
    feedback_template = read_prompt_optional(f"data/prompts/{prompt_id}_feedback.txt")
    if feedback_template:
        fb_prompt = feedback_template % {
            "grading_json": result.model_dump_json(ensure_ascii=False)
        }

        fb_resp = ollama_client.chat(
            model="qwen2.5-coder:7b",
            messages=[
                {"role": "system", "content": "Ты русскоязычный редактор. Верни только JSON."},
                {"role": "user", "content": fb_prompt},
            ],
            options={"temperature": 0},
        )
        fb_data = safe_json_loads(fb_resp.message.content)
        result.feedback_for_team = fb_data.get("feedback_for_team", result.feedback_for_team)
        result.feedback_for_candidate = fb_data.get("feedback_for_candidate", result.feedback_for_candidate)

    return result