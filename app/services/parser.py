import re
import json
from pathlib import Path
from difflib import SequenceMatcher

from app.services.llm import ollama_client
from app.services.llm import read_prompt_optional

BASE_DIR = Path(__file__).parent.parent.parent

def similarity(text1: str, text2: str) -> float:
    """Возвращает коэффициент похожести
    :param text1: текст с чем сравниваем
    :param text2: текст, который сравниваем
    :return: коэффициент "похожести"
    """
    return SequenceMatcher(None, text1, text2).ratio()


def parse_submission(raw_text: str) -> dict[int, str]:
    """
    Разделяем текст ответов кандидата на отдельные составляющие
    :param raw_text: текст ответа
    :return: словарь, где ключ - номер заданий, а значение - текст ответа
    """
    # Загружаем тексты заданий

    tasks_dir = BASE_DIR / "data" / "tasks"
    # tasks_dir = Path("data/tasks2")
    task_texts = {}
    for task_file in tasks_dir.glob("*.json"):
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
            task_texts[str(task["task_number"])] = task["task_text"]

    # Разбиваем текст ответа на слова
    raw_text = raw_text.replace('\xa0', ' ') # Убираем неразрывные пробелы
    words = raw_text.split()

    # Ищем в ответе кандидата тексты заданий
    found_positions = []

    for num, task_text in task_texts.items():
        task_words = task_text.split()
        task_len = len(task_words)


        # Ищем по словам
        best_pos = -1
        best_ratio = 0

        for i in range(len(words) - task_len):
            text_part = words[i:i + task_len] # Выделяем предполагаемый текст задания
            part = ' '.join(text_part) # Объединяем слова в текст
            ratio = similarity(task_text, part) # Сравниваем выделенную часть с текстом задания
            if ratio > best_ratio:  # Проверяем, что эта часть самая "похожая"
                best_ratio = ratio
                best_pos = i

        if best_ratio > 0.9: # Если нашли текст задания, записываем границы этого задания
            found_positions.append((num, best_pos, best_pos + len(task_text.split())))

    # Сортируем по позиции
    found_positions.sort(key=lambda x: x[1])

    # Выделяем ответы между найденными заданиями
    result = {}
    for i, (num, start, end) in enumerate(found_positions):
        if i + 1 < len(found_positions): # Берем начало следующего задания как конец текущего ответа, если дальше ещё есть ответы
            next_start = found_positions[i + 1][1]
        else: # Если задание последнее, то ответ идет до конца текста
            next_start = len(words)
        answer_words = words[end:next_start]
        answer = ' '.join(answer_words).strip()
        if answer:
            result[num] = answer

    if result: # Если нашли таким способом ответы кандидата, заканчиваем поиск
        return result



    pattern = r'(?mi)^\s*(?:задание|task)?\s*(\d+)[.)]\s*'
    parts = re.split(pattern, raw_text.strip())

    result = {}
    it = iter(parts[1:])
    for num, block in zip(it, it):
        block = block.strip()
        if block:
            result[str(num)] = block


    # Если не нашли ни одного задания с арабскими цифрами
    if not result:
        # Пробуем найти задания с римскими цифрами (от I до X)
        roman_pattern = r'(?mi)^\s*(?:задание|task)?\s*([ivx]+)[.)]\s*'
        roman_parts = re.split(roman_pattern, raw_text.strip())


        # Словарь римских цифр
        roman_to_arabic = {
            'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
            'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10'
        }

        it = iter(roman_parts[1:])
        for num, block in zip(it, it):
            block = block.strip()
            # Приводим римскую цифру к верхнему регистру для поиска в словаре
            if block and num.upper() in roman_to_arabic:
                result[roman_to_arabic[num.upper()]] = block

    return result


def ai_parse_submission(raw_text: str) -> dict[str, str]:
    """
    Используем ИИ для разделения ответов кандидата по вопросам
    :param raw_text: текст ответа кандидата
    :return: словарь {номер_задания: текст_ответа}
    """
    # Загружаем все задания
    tasks_dir = BASE_DIR / "data" / "tasks"
    task_texts = {}
    for task_file in tasks_dir.glob("*.json"):
        with open(task_file, 'r', encoding='utf-8') as f:
            task = json.load(f)
            task_texts[str(task["task_number"])] = task["task_text"]

    # Загружаем промт для парсинга ответов
    prompt_template = read_prompt_optional(f"data/prompts/default_v1_parse.txt")

    # Формируем контекст с заданиями
    tasks_context = "\n".join([
        f"Задание {task_num}: {task_texts[task_num]}"
        for task_num in sorted(task_texts.keys(), key=int)
    ])

    # Подставляем задания и текст ответа в промт
    prompt = prompt_template.replace("{tasks}", tasks_context)
    prompt = prompt.replace("{candidate_response}", raw_text)

    # Отправляем запрос к LLM
    response = ollama_client.generate(
        model="qwen2.5-coder:7b",
        prompt=prompt,
        options={"temperature": 0}
    )

    # Парсим JSON из ответа
    result = {}
    response_text = response['response'].strip()

    # Ищем JSON в ответе модели (модель может ответить не только json)
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Пробуем найти JSON объект без маркеров
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = response_text

    try:
        result = json.loads(json_str)
        # Убеждаемся, что ключи - строки, значения - строки
        result = {str(k): str(v) for k, v in result.items()}
    except json.JSONDecodeError:
        # Если не удалось распарсить JSON, возвращаем пустой словарь
        result = {}

    return result

