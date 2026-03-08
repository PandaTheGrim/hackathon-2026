import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROMAN_TO_ARABIC = {
    "I": "1", "II": "2", "III": "3", "IV": "4", "V": "5",
    "VI": "6", "VII": "7", "VIII": "8", "IX": "9", "X": "10",
}

TASK_HEADER_PATTERN = r"(?mi)^\s*(?:задание\s+(\d+)|№\s*(\d+))\s*$"

NUMBER_HEADER_PATTERN = r"(?mi)^\s*№\s*(\d+)\s*$"


def _calculate_similarity(text1: str, text2: str) -> float:
    """Коэффициент похожести двух строк от 0 до 1."""
    return SequenceMatcher(None, text1, text2).ratio()


def _load_task_texts() -> dict[str, str]:
    """Грузим тексты заданий из data/tasks/*.json: {"1": "...", "2": "..."}."""
    tasks_dir = Path("data/tasks")

    task_texts: dict[str, str] = {}
    for task_file in tasks_dir.glob("*.json"):
        with task_file.open("r", encoding="utf-8") as f:
            task = json.load(f)
        task_num = str(task["task_number"])
        task_texts[task_num] = task["task_text"]

    return task_texts


def _parse_by_task_texts(raw_text: str, task_texts: dict[str, str]) -> dict[str, str]:
    """Ищем в ответе фрагменты, похожие на тексты заданий."""
    text = raw_text.replace("\xa0", " ")
    words = text.split()

    found_positions: list[tuple[str, int, int]] = []
    for num, task_text in task_texts.items():
        task_words = task_text.split()
        task_len = len(task_words)
        if task_len == 0 or len(words) < task_len:
            continue

        best_pos = -1
        best_ratio = 0.0

        for i in range(len(words) - task_len + 1):
            part = " ".join(words[i:i + task_len])
            ratio = _calculate_similarity(task_text, part)
            if ratio > best_ratio:
                best_ratio = ratio
                best_pos = i

        if best_ratio >= 0.9 and best_pos >= 0:  # выбраны произвольно
            found_positions.append((num, best_pos, best_pos + task_len))

    if not found_positions:
        return {}

    found_positions.sort(key=lambda x: x[1])

    result: dict[str, str] = {}
    for i, (num, start, end) in enumerate(found_positions):
        if i + 1 < len(found_positions):
            next_start = found_positions[i + 1][1]
        else:
            next_start = len(words)

        answer_words = words[end:next_start]
        answer = " ".join(answer_words).strip()
        if answer:
            result[num] = answer

    return result


def _parse_by_arabic_numbers(raw_text: str) -> dict[str, str]:
    """делим по 'Задание 1', '1.' и т.п. (арабские цифры)."""
    pattern = r"(?mi)^\s*(?:задание|task)?\s*(\d+)[.)]\s*"
    parts = re.split(pattern, raw_text.strip())

    result: dict[str, str] = {}
    it = iter(parts[1:])
    for num, block in zip(it, it):
        block = block.strip()
        if block:
            result[str(num)] = block

    return result


def _parse_by_roman_numbers(raw_text: str) -> dict[str, str]:
    """делим по 'I', 'II', ... 'X'."""

    pattern = r"(?mi)^\s*(?:задание|task)?\s*([ivx]+)[.)]?\s*"
    parts = re.split(pattern, raw_text.strip())

    result: dict[str, str] = {}
    it = iter(parts[1:])
    for num, block in zip(it, it):
        block = block.strip()
        key = num.upper()
        if block and key in ROMAN_TO_ARABIC:
            result[ROMAN_TO_ARABIC[key]] = block

    return result


def _parse_submission_by_roman_new_lines(raw_text: str) -> dict[str, str]:
    """делим по 'I', 'II', ... 'X' с отбивкой новой строкой"""
    lines = raw_text.replace("\xa0", " ").splitlines()
    positions = []

    for index, line in enumerate(lines):
        token = line.strip().upper()
        if token in ROMAN_TO_ARABIC:
            positions.append((ROMAN_TO_ARABIC[token], index))

    if not positions:
        return {}

    result: dict[str, str] = {}
    for i, (question_number, start_idx) in enumerate(positions):
        if i + 1 < len(positions):
            end_idx = positions[i + 1][1]
        else:
            end_idx = len(lines)

        block_lines = lines[start_idx + 1:end_idx]
        answer = "\n".join(l.rstrip() for l in block_lines).strip()
        if answer:
            result[question_number] = answer

    return result


def _parse_by_task_headers(raw_text: str) -> dict[str, str]:
    """
    Делим текст по заголовкам вида 'Задание 1' или '№1' на отдельной строке
    """
    lines = raw_text.splitlines()
    headers: list[tuple[int, int]] = []  # (line_idx, task_num)

    for i, line in enumerate(lines):
        m = re.search(TASK_HEADER_PATTERN, line)
        if m:
            num_str = m.group(1) or m.group(2)
            headers.append((i, int(num_str)))

    if not headers:
        return {}

    result: dict[str, str] = {}
    for idx, (line_idx, task_num) in enumerate(headers):
        start = line_idx + 1
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        block = "\n".join(lines[start:end]).strip()
        if block:
            result[str(task_num)] = block

    return result


def parse_submission(raw_text: str) -> dict[str, str]:
    """
    Разделяем текст ответов кандидата на отдельные задания.
    Возвращает: {"1": "ответ на 1", "2": "ответ на 2", ...}
    """
    task_texts = _load_task_texts()

    by_headers = _parse_by_task_headers(raw_text)
    if by_headers:
        return by_headers

    by_tasks = _parse_by_task_texts(raw_text, task_texts)
    if by_tasks:
        return by_tasks

    by_roman_blocks = _parse_submission_by_roman_new_lines(raw_text)
    if by_roman_blocks:
        return by_roman_blocks

    by_arabic = _parse_by_arabic_numbers(raw_text)
    if by_arabic:
        return by_arabic

    return _parse_by_roman_numbers(raw_text)
