import re


def parse_submission(raw_text: str) -> dict[int, str]:
    """
    Разделяем текст ответов кандидата на отдельные составляющие
    :param raw_text: текст ответа
    :return: словарь, где ключ - номер заданий, а значение - текст ответа
    """
    pattern = r'(?mi)^\s*(?:задание|task)?\s*(\d+)[.)]\s*'
    parts = re.split(pattern, raw_text.strip())

    result = {}
    it = iter(parts[1:])
    for num, block in zip(it, it):
        block = block.strip()
        if block:
            result[str(num)] = block

    return result
