# AI SupportAssist Fase 2

Aplicación de triaje financiero de NovaMarket: frontend en HTML/CSS/JavaScript y backend FastAPI que utiliza el Pipeline TF-IDF + MultinomialNB de actividad 6, con umbral **0.24**. Ambos componentes se sirven desde el mismo origen. La ruta financiera siempre exige atención humana.

## Continuidad y alcance

La fase 1 plantea un sistema amplio con IA generativa y RAG. Actividad 5 clasifica 27 intenciones; actividad 6 reduce el problema a derivación financiera binaria. Esta entrega despliega ese último subproblema, sin implementar RAG ni autorizar pagos o reembolsos. La interfaz está en español y la evaluación del modelo corresponde a inglés sintético. Un ticket declarado en español se rechaza con HTTP 422 y se solicita revisión humana; declarar inglés no demuestra que el idioma lo sea.

El modelo incluido fue **regenerado** con las operaciones y particiones de actividad 6, en Python 3.12.14 y scikit-learn 1.8.0. Reproduce el umbral 0.24 y la matriz `[[3333,8],[0,1462]]` sobre 4,803 registros históricos. No se atribuye este nuevo archivo a un run histórico de MLflow. Consulte [la evidencia](evidence/model_reconstruction.json) y [los metadatos](models/metadata.json).

## Archivos principales

| Ruta | Propósito |
|---|---|
| `app/main.py` | API, validación y publicación del frontend |
| `app/inference.py` | Carga del modelo, verificación y decisión con umbral |
| `app/preprocessing.py` | Limpieza heredada |
| `app/static/` | Interfaz y consumo HTTP real mediante fetch |
| `models/` | Pipeline entrenado y metadatos |
| `Dockerfile`, `compose.yaml` | Construcción y ejecución del contenedor |
| `requirements*.txt` | Dependencias de inferencia y desarrollo |
| `scripts/rebuild_model.py` | Regeneración reproducible desde CSV con SHA-256 |
| `scripts/smoke.py` | Consumo del servicio desde otro programa |
| `scripts/browser_check.py` | Prueba del navegador contra la API |
| `tests/` | Pruebas de contrato, errores y consistencia |
| `docs/MANUAL_DESPLIEGUE.md` | Requisitos, Docker, nube, operación y documentación |
| `docs/VERIFICACION_EJEMPLOS.md` | Comparación con demostraciones de temas 15 y 16 |
| `../.github/workflows/fase2.yml` | Construcción y prueba Docker en GitHub Actions |

## Inicio con Docker

Requiere Git, Docker Engine o Docker Desktop en ejecución y Docker Compose v2. Desde una carpeta de trabajo:

```bash
git clone --branch fase2-ai-supportassist https://github.com/efrainkun-ai/Act5_GP.git
cd Act5_GP/Fase2
docker info
docker compose config
docker compose build
docker compose up -d --wait --wait-timeout 90
docker compose ps
```

Abra `http://localhost:8000/`, `http://localhost:8000/ready` y `http://localhost:8000/docs`.
El modelo ya está incluido y no se entrena durante la construcción o el arranque. La inferencia no descarga datos ni llama a servicios externos.

En PowerShell puede probar:

```powershell
$payload = @{text='Where is my refund?'; language='en'} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/v1/predict -Method Post -ContentType application/json -Body $payload
docker compose logs --no-color
docker compose down
```

## API

| Método | Endpoint | Función |
|---|---|---|
| GET | `/` | Interfaz de usuario |
| GET | `/health` | Estado del servicio |
| GET | `/ready` | Modelo cargado y servicio disponible |
| GET | `/api/v1/model` | Versión, umbral y alcance del modelo |
| POST | `/api/v1/predict` | Clasificación a partir de JSON |
| GET | `/docs` | Swagger interactivo |
| GET | `/openapi.json` | Contrato OpenAPI |

Entrada: `{"text":"Where is my refund?","language":"en"}`.
Salida: clase 0/1, ruta, puntuación financiera, umbral, versión, revisión humana, identificador y tiempo de inferencia. El servidor devuelve HTTP 422 por texto inválido, idioma no soportado o ausencia de vocabulario reconocido; HTTP 413 por cuerpo de solicitud demasiado grande. No interpreta una predicción negativa como resolución del ticket.

## Ejecución sin Docker y pruebas

Python **3.12**. En Windows use `py -3.12 -m venv .venv` y `.venv\Scripts\Activate.ps1`; en Linux/macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Después, en cualquier sistema:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --junitxml=evidence/junit-local.xml
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

En otra terminal con el entorno activado:

```bash
python -m scripts.smoke --output evidence/http-local.json
python -m playwright install chromium
python -m scripts.browser_check
```

Detenga Uvicorn con Ctrl+C antes de usar Docker sobre el mismo puerto. Los JSON y PNG producidos constituyen evidencias de la ejecución correspondiente; una prueba fuera de Docker no acredita un contenedor ejecutado.

## Regenerar el modelo

```bash
python -m scripts.rebuild_model
```

Descarga el CSV de una revisión fija, verifica SHA-256, reproduce limpieza y particiones 60/20/20 y ajusta el candidato ya seleccionado. Selecciona el umbral exclusivamente con validación y comprueba concordancia con los resultados históricos antes de guardar. Cambian la fecha y posiblemente los bytes serializados; conserve juntos el nuevo modelo, metadatos y evidencia. El dataset no se sube al repositorio.

## Estado y evidencias

Consulte [el registro de validación](docs/VERIFICACION_EJEMPLOS.md) y la pestaña Actions. Un workflow existente o un Dockerfile correcto no prueban una construcción exitosa: verifique la conclusión del run y descargue sus artefactos. El manual diferencia ejecución local, ejecución Docker en runner y despliegue público.

## Referencias

Los tutoriales se adaptan al caso AI-SupportAssist; no se copian sus datos ni sus modelos. Consulte [referencias y atribución](docs/REFERENCIAS.md).
