"""Pruebas HTTP sobre el proceso o contenedor real, con evidencia JSON."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import httpx


def run(base_url):
    records = []
    with httpx.Client(base_url=base_url, timeout=10, trust_env=False) as client:
        for attempt in range(30):
            try:
                if client.get('/ready').status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            raise RuntimeError('El servicio no quedó disponible en 30 segundos')
        cases = [
            ('GET', '/health', None, 200), ('GET', '/ready', None, 200),
            ('GET', '/', None, 200), ('GET', '/static/app.js', None, 200),
            ('GET', '/openapi.json', None, 200), ('GET', '/api/v1/model', None, 200),
            ('POST', '/api/v1/predict', {'text': 'Where is my refund?', 'language': 'en'}, 200),
            ('POST', '/api/v1/predict', {'text': 'I forgot my password', 'language': 'en'}, 200),
            ('POST', '/api/v1/predict', {'text': '', 'language': 'en'}, 422),
            ('POST', '/api/v1/predict', {'text': 'Quiero un reembolso', 'language': 'es'}, 422),
        ]
        for method, path, payload, expected in cases:
            start = time.perf_counter()
            response = client.request(method, path, **({'json': payload} if payload is not None else {}))
            record = {'method': method, 'path': path, 'expected_status': expected,
                      'actual_status': response.status_code,
                      'elapsed_ms': round((time.perf_counter()-start)*1000, 3)}
            if path == '/api/v1/predict' and response.status_code == 200:
                record['response'] = response.json()
                assert record['response']['label'] == (1 if payload['text'].startswith('Where') else 0)
            if path == '/openapi.json':
                assert '/api/v1/predict' in response.json()['paths']
            records.append(record)
            assert response.status_code == expected, record
        return {'executed_at_utc': datetime.now(timezone.utc).isoformat(),
                'base_url': base_url, 'passed': len(records), 'cases': records}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--output', type=Path, default=Path('evidence/local-http.json'))
    args = parser.parse_args()
    result = run(args.base_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
