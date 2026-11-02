"""Regenera el candidato ya seleccionado; no vuelve a elegir algoritmo con test.

Uso: python -m scripts.rebuild_model [--csv data/bitext.csv]
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import urllib.request

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from app.preprocessing import clean_text

ROOT = Path(__file__).resolve().parents[1]
REV = '430d1a89bd93bd1fa23c16f29dd53e73f0087443'
EXPECTED = '6f81102b0100b97b8468eb04368033a23206bf1fde9d53500d5806ec1001a434'
URL = f'https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset/resolve/{REV}/Bitext_Sample_Customer_Support_Training_Dataset_27K_responses-v11.csv'
FINANCIAL = {'INVOICE', 'PAYMENT', 'REFUND', 'CANCEL'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare(raw):
    audit = raw.copy()
    audit.insert(0, 'source_row', np.arange(len(audit)))
    audit['text_clean'] = audit.instruction.fillna('').map(clean_text)
    audit['intent_clean'] = audit.intent.fillna('').str.strip().str.lower()
    audit['text_sha256'] = audit.text_clean.map(lambda t: hashlib.sha256(t.encode()).hexdigest())
    audit['exclusion_reason'] = ''
    invalid = audit.text_clean.eq('') | audit.intent_clean.eq('') | audit.category.fillna('').str.strip().eq('')
    audit.loc[invalid, 'exclusion_reason'] = 'texto_o_etiqueta_vacios'
    conflicts = audit.loc[~invalid].groupby('text_sha256').intent_clean.nunique()
    audit.loc[~invalid & audit.text_sha256.isin(conflicts[conflicts > 1].index), 'exclusion_reason'] = 'etiquetas_contradictorias'
    eligible = audit.exclusion_reason.eq('')
    dup = audit.loc[eligible].duplicated('text_sha256', keep='first')
    audit.loc[dup[dup].index, 'exclusion_reason'] = 'texto_duplicado'
    clean = audit.loc[audit.exclusion_reason.eq(''), ['source_row', 'text_clean', 'text_sha256', 'intent_clean', 'category']].copy()
    clean['y'] = clean.category.isin(FINANCIAL).astype(int)
    assert len(raw) == 26872 and len(clean) == 24014
    return clean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', type=Path, default=ROOT / 'data/bitext.csv')
    args = parser.parse_args()
    if not args.csv.exists():
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.csv.with_suffix('.part')
        with urllib.request.urlopen(URL, timeout=120) as response:
            temporary.write_bytes(response.read())
        temporary.replace(args.csv)
    if sha(args.csv) != EXPECTED:
        raise ValueError('El CSV no coincide con la revisión de actividad 6')
    clean = prepare(pd.read_csv(args.csv, dtype=str))
    dev, test = train_test_split(clean, test_size=.2, random_state=42, stratify=clean.intent_clean)
    fit, val = train_test_split(dev, test_size=.25, random_state=42, stratify=dev.intent_clean)
    for a, b in [(fit, val), (fit, test), (val, test)]:
        assert set(a.text_sha256).isdisjoint(b.text_sha256)
    model = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True)),
        ('clf', MultinomialNB(alpha=.1)),
    ])
    model.fit(fit.text_clean, fit.y)
    validation_score = model.predict_proba(val.text_clean)[:, list(model.classes_).index(1)]
    candidates = []
    for threshold in np.round(np.arange(.01, 1, .01), 2):
        pred = (validation_score >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(val.y, pred, labels=[0, 1]).ravel()
        candidates.append({'threshold': float(threshold), 'cost': int(5*fn+fp),
                           'precision': precision_score(val.y, pred, zero_division=0),
                           'recall': recall_score(val.y, pred, zero_division=0)})
    table = pd.DataFrame(candidates)
    eligible = table[(table.recall >= .95) & (table.precision >= .90)]
    assert not eligible.empty
    best = eligible.assign(distance=(eligible.threshold-.5).abs()).sort_values(['cost', 'distance', 'threshold']).iloc[0]
    threshold = float(best.threshold)
    assert threshold == .24, 'La reconstrucción cambió el umbral: revisar antes de desplegar'
    scores = model.predict_proba(test.text_clean)[:, list(model.classes_).index(1)]
    predictions = (scores >= threshold).astype(int)
    matrix = confusion_matrix(test.y, predictions, labels=[0, 1]).tolist()
    assert matrix == [[3333, 8], [0, 1462]], 'La matriz difiere de actividad 6'
    out = ROOT / 'models'
    out.mkdir(exist_ok=True)
    artifact = out / 'financial_nb.joblib'
    joblib.dump(model, artifact, compress=3)
    restored = joblib.load(artifact)
    np.testing.assert_allclose(restored.predict_proba(test.text_clean), model.predict_proba(test.text_clean), atol=0, rtol=0)
    parts = pd.concat([fit.assign(split='fit'), val.assign(split='validation'), test.assign(split='test')])
    split_csv = parts[['source_row', 'text_sha256', 'split', 'y']].to_csv(index=False)
    timestamp = datetime.now(timezone.utc).isoformat()
    metadata = {
        'model_version': 'act6-nb-financial-v1', 'algorithm': 'TF-IDF + MultinomialNB(alpha=0.1)',
        'threshold': threshold, 'financial_categories': sorted(FINANCIAL),
        'scope': 'synthetic_english_retrospective', 'created_at_utc': timestamp,
        'origin': 'Regeneración del candidato seleccionado en actividad 6; no es el archivo binario histórico.',
        'model_sha256': sha(artifact), 'raw_sha256': EXPECTED, 'dataset_revision': REV,
        'dataset_url': URL, 'dataset_license': 'CDLA-Sharing-1.0 (según ficha del dataset)',
        'split_sha256': hashlib.sha256(split_csv.encode()).hexdigest(),
        'preprocessing_sha256': sha(ROOT / 'app/preprocessing.py'),
        'training_script_sha256': sha(Path(__file__)),
        'environment': {'python': platform.python_version(), 'scikit-learn': sklearn.__version__,
                        'numpy': np.__version__, 'scipy': scipy.__version__, 'joblib': joblib.__version__, 'pandas': pd.__version__},
        'n_fit': len(fit), 'n_validation': len(val), 'n_test': len(test),
    }
    write_json(out / 'metadata.json', metadata)
    evidence = {
        'kind': 'new_local_reconstruction_not_historical_mlflow_run', 'created_at_utc': timestamp,
        'threshold_selected_on_validation': threshold, 'validation_cost': int(best.cost),
        'confusion_matrix': matrix, 'accuracy': accuracy_score(test.y, predictions),
        'precision': precision_score(test.y, predictions), 'recall': recall_score(test.y, predictions),
        'f1': f1_score(test.y, predictions), 'roc_auc': roc_auc_score(test.y, scores),
        'prediction_count': len(test), 'reload_probabilities_identical': True,
        'historical_test_reused': True, 'external_spanish_validation': False,
        'model_sha256': metadata['model_sha256'], 'environment': metadata['environment'],
    }
    write_json(ROOT / 'evidence/model_reconstruction.json', evidence)
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
