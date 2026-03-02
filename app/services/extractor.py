import pathlib
from pypdf import PdfReader
from docx import Document


def extract_text(file_path: str) -> str:
    """
    Извлекаем текст из присланных файлов с ответами
    :param file_path: путь до временного файла в папке загрузки
    :return: извлеченный текст строкой
    """
    path = pathlib.Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if suffix in (".docx", ".doc"):
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    raise ValueError(f"Некорректный формат файла: {suffix}")
