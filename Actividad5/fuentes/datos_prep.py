import pandas as pd
import re, unicodedata

def clean_text(value):
    if pd.isna(value): return ''
    text = unicodedata.normalize('NFKC', str(value)).strip().lower()
    text = re.sub(r'\{\{.*?\}\}', ' entity ', text)
    text = re.sub(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', ' email ', text)
    text = re.sub(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)', ' phone ', text)
    return re.sub(r'\s+', ' ', text).strip()

