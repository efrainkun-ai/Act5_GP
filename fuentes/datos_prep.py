"""Preparación determinista de solicitudes de soporte y auditoría completa."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def limpiar_texto(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = re.sub(r"\{\{.*?\}\}", " entity ", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", " email ", text)
    text = re.sub(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)", " phone ", text)
    return re.sub(r"\s+", " ", text).strip()


def preparar_datos(csv_path, salida, evidencias):
    salida, evidencias = Path(salida), Path(evidencias)
    salida.mkdir(parents=True, exist_ok=True)
    evidencias.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(csv_path, dtype=str)
    audit = raw.copy()
    audit.insert(0, "source_row", np.arange(len(audit)))
    audit["text_clean"] = audit.instruction.map(limpiar_texto)
    audit["intent_clean"] = audit.intent.fillna("").str.strip().str.lower()
    audit["text_sha256"] = audit.text_clean.map(lambda s: hashlib.sha256(s.encode()).hexdigest())
    audit["exclusion_reason"] = ""
    invalid = audit.text_clean.eq("") | audit.intent_clean.eq("") | audit.category.fillna("").str.strip().eq("")
    audit.loc[invalid, "exclusion_reason"] = "texto_o_etiqueta_vacios"
    conflicts = audit.loc[~invalid].groupby("text_sha256").intent_clean.nunique()
    conflict_keys = set(conflicts[conflicts > 1].index)
    audit.loc[~invalid & audit.text_sha256.isin(conflict_keys), "exclusion_reason"] = "etiquetas_contradictorias"
    eligible = audit.exclusion_reason.eq("")
    repeated = audit.loc[eligible].duplicated("text_sha256", keep="first")
    audit.loc[repeated[repeated].index, "exclusion_reason"] = "texto_duplicado"
    clean = audit.loc[audit.exclusion_reason.eq(""), ["source_row", "text_clean", "text_sha256", "intent_clean", "category", "flags"]].copy()
    assert not clean.text_sha256.duplicated().any()
    assert clean.groupby("intent_clean").category.nunique().max() == 1
    assert clean.intent_clean.value_counts().min() >= 10
    clean.to_csv(salida / "tickets_clean_v1.csv", index=False)
    audit[["source_row", "text_sha256", "intent_clean", "exclusion_reason"]].to_csv(salida / "auditoria_v1.csv", index=False)
    quality = {
        "originales": len(raw), "limpios": len(clean), "excluidos": len(raw)-len(clean),
        "motivos": audit.exclusion_reason.replace("", "conservado").value_counts().to_dict(),
        "nulos_originales": raw.isna().sum().astype(int).to_dict(),
        "vacios_originales": {c: int(raw[c].fillna("").str.strip().eq("").sum()) for c in raw},
        "longitud_original": raw.instruction.str.len().describe().to_dict(),
        "longitud_limpia": clean.text_clean.str.len().describe().to_dict(),
        "clases_antes": raw.intent.value_counts().to_dict(),
        "clases_despues": clean.intent_clean.value_counts().to_dict(),
        "conflictos_texto_etiqueta": len(conflict_keys),
    }
    (evidencias / "calidad_datos.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return raw, clean, quality
