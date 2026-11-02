import hashlib
import json
from pathlib import Path
import shutil
from unittest.mock import patch

from fastapi.testclient import TestClient
import numpy as np
import pytest

from app.main import ROOT, create_app
from app.inference import Predictor
from app.preprocessing import clean_text


@pytest.fixture
def client():
    with TestClient(create_app()) as connection:
        yield connection


def test_contract_and_frontend(client):
    assert client.get('/health').json()['status'] == 'ok'
    assert client.get('/ready').json()['status'] == 'ready'
    assert client.get('/api/v1/model').json()['threshold'] == .24
    assert '/api/v1/predict' in client.get('/openapi.json').json()['paths']
    assert client.get('/docs').status_code == 200
    assert 'ticket-form' in client.get('/').text
    assert "fetch('/api/v1/predict'" in client.get('/static/app.js').text
    assert client.get('/static/style.css').status_code == 200


@pytest.mark.parametrize('text,label', [
    ('Where is my refund?', 1), ('How can I get my invoice?', 1),
    ('I have a payment issue', 1), ('I forgot my password', 0),
    ('I want to create an account', 0), ('Where is my order?', 0),
])
def test_normal_routes(client, text, label):
    response = client.post('/api/v1/predict', json={'text': text, 'language': 'en'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['label'] == label
    assert data['label'] == int(data['financial_score'] >= .24)
    assert data['human_review_required'] is True
    assert len(data['request_id']) == 36
    assert data['latency_ms'] >= 0
    assert text not in response.text


@pytest.mark.parametrize('payload', [
    {}, {'text': 'refund'}, {'language': 'en'},
    {'text': '', 'language': 'en'}, {'text': '   ', 'language': 'en'},
    {'text': None, 'language': 'en'}, {'text': 123, 'language': 'en'},
    {'text': ['refund'], 'language': 'en'}, {'text': 'refund', 'language': 'fr'},
    {'text': 'refund', 'language': 'en', 'threshold': .5},
    {'text': 'x'*4001, 'language': 'en'},
    {'text': 'Quiero un reembolso', 'language': 'es'},
    {'text': '🛵🛵🛵', 'language': 'en'}, {'text': 'zzzxxyyqqq', 'language': 'en'},
])
def test_invalid_and_out_of_scope(client, payload):
    assert client.post('/api/v1/predict', json=payload).status_code == 422


def test_oversized_and_malformed(client):
    assert client.post('/api/v1/predict', content=b'x'*33000).status_code == 413
    assert client.post('/api/v1/predict', content='{', headers={'Content-Type': 'application/json'}).status_code == 422
    assert client.get('/api/v1/predict').status_code == 405
    assert client.post('/api/v1/predict', content=iter([b'x'*20000, b'x'*20000])).status_code == 413


def test_normalization_and_repeatability(client):
    assert clean_text('  MY {{Order}}  test@example.com +52 123 456 7890 ') == 'my entity email phone'
    a = client.post('/api/v1/predict', json={'text': 'WHERE IS MY REFUND?', 'language': 'en'}).json()
    b = client.post('/api/v1/predict', json={'text': '  Where is my refund?  ', 'language': 'en'}).json()
    assert a['financial_score'] == b['financial_score']
    assert a['request_id'] != b['request_id']


@pytest.mark.parametrize('score,label', [(.239999, 0), (.24, 1), (.240001, 1)])
def test_threshold_boundary(score, label):
    predictor = Predictor(ROOT / 'models')
    with patch.object(predictor.model, 'predict_proba', return_value=np.array([[1-score, score]])):
        assert predictor.predict('refund', 'en')['label'] == label


def test_corrupt_model_fails_startup(tmp_path):
    shutil.copy(ROOT / 'models/metadata.json', tmp_path)
    (tmp_path / 'financial_nb.joblib').write_bytes(b'corrupt')
    with pytest.raises(RuntimeError, match='huella'):
        with TestClient(create_app(tmp_path)):
            pass


def test_missing_model_fails_startup(tmp_path):
    with pytest.raises(FileNotFoundError):
        with TestClient(create_app(tmp_path)):
            pass


def test_evidence_and_artifact_match():
    evidence = json.loads((ROOT / 'evidence/model_reconstruction.json').read_text())
    metadata = json.loads((ROOT / 'models/metadata.json').read_text())
    assert evidence['confusion_matrix'] == [[3333, 8], [0, 1462]]
    assert evidence['model_sha256'] == metadata['model_sha256']
    assert metadata['preprocessing_sha256'] == hashlib.sha256((ROOT / 'app/preprocessing.py').read_bytes()).hexdigest()
    assert metadata['training_script_sha256'] == hashlib.sha256((ROOT / 'scripts/rebuild_model.py').read_bytes()).hexdigest()


def test_privacy_headers(client):
    response = client.post('/api/v1/predict', json={'text': 'SECRET-TEXT', 'language': 'fr'})
    assert 'SECRET-TEXT' not in response.text
    assert response.headers['Cache-Control'] == 'no-store'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
