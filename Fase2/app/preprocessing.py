"""Normalización idéntica a clean_text de la actividad 6 para texto no nulo."""
import re
import unicodedata


def clean_text(value: str) -> str:
    text = unicodedata.normalize('NFKC', value).strip().lower()
    text = re.sub(r'\{\{.*?\}\}', ' entity ', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', ' email ', text)
    text = re.sub(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)', ' phone ', text)
    return re.sub(r'\s+', ' ', text).strip()
