import json
import re
from pathlib import Path

from app.services.llm import ollama_client, read_prompt_optional


def ai_parse_submission(raw_text: str) -> dict[str, str]:
    """
    :type raw_text: str сырой текст из файла с ответами кандидата
    Используем LLM, чтобы разделить ответы кандидата по заданиям.
    Возвращаем: {"1": "ответ на 1", "2": "ответ на 2", ...}
    """
    tasks_dir = Path("data/tasks")
    task_texts: dict[str, str] = {}
    for task_file in tasks_dir.glob("*.json"):
        with task_file.open("r", encoding="utf-8") as f:
            task = json.load(f)
        task_texts[str(task["task_number"])] = task["task_text"]

    prompt_template = read_prompt_optional("data/prompts/default_v1_parse.txt")

    tasks_context = "\n".join(
        f"Задание {num}: {text}"
        for num, text in sorted(task_texts.items(), key=lambda x: int(x[0]))
    )

    prompt = (
        prompt_template
        .replace("{tasks}", tasks_context)
        .replace("{candidate_response}", raw_text)
    )

    response = ollama_client.generate(
        model="qwen2.5-coder:7b",
        prompt=prompt,
        options={"temperature": 0},
    )

    response_text = response["response"].strip()

    json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r"\{.*}", response_text, re.DOTALL)
        json_str = json_match.group(0) if json_match else response_text

    try:
        obj = json.loads(json_str)
        return {str(k): str(v) for k, v in obj.items()}
    except json.JSONDecodeError:
        return {}
