"""Carga una vez; verifica integridad y aplica la política histórica de actividad 6."""
import hashlib
import json
from pathlib import Path
import joblib
import sklearn
from .preprocessing import clean_text


class InferenceError(ValueError):
    pass


class Predictor:
    def __init__(self, model_dir: Path):
        self.metadata = json.loads((model_dir / 'metadata.json').read_text())
        model_path = model_dir / 'financial_nb.joblib'
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != self.metadata['model_sha256']:
            raise RuntimeError('La huella del modelo no coincide con metadata.json')
        if sklearn.__version__ != self.metadata['environment']['scikit-learn']:
            raise RuntimeError('Versión de scikit-learn incompatible con el modelo')
        self.model = joblib.load(model_path)
        self.threshold = float(self.metadata['threshold'])
        if not 0 < self.threshold < 1:
            raise RuntimeError('Umbral fuera de rango')
        self.positive_index = list(self.model.classes_).index(1)

    def predict(self, text: str, language: str) -> dict:
        # Idioma declarado por quien envía; no pretende ser detección automática.
        if language != 'en':
            raise InferenceError('El modelo está validado sólo con inglés sintético. Requiere revisión humana.')
        cleaned = clean_text(text)
        if not cleaned:
            raise InferenceError('El texto está vacío después de normalizarlo.')
        features = self.model.named_steps['tfidf'].transform([cleaned])
        if features.nnz == 0:
            raise InferenceError('No hay vocabulario reconocido. Requiere revisión humana.')
        score = float(self.model.predict_proba([cleaned])[0, self.positive_index])
        positive = score >= self.threshold
        return {
            'label': int(positive),
            'route': 'atencion_financiera_humana' if positive else 'otra_ruta_soporte',
            'financial_score': score,
            'threshold': self.threshold,
            'model_version': self.metadata['model_version'],
            'human_review_required': True,
            'scope': 'synthetic_english_retrospective',
        }
