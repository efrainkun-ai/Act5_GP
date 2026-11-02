# Verificación contra los ejemplos de temas 15 y 16

Fecha de revisión: 1 de noviembre de 2026. Se inspeccionaron README, Dockerfile y API de ambas demostraciones en el commit **0d3985f681080a8cde5ea3a17ed1977c0d6be920** del repositorio MinaNik229/tema12-mlflow-colab. Los enlaces completos están en REFERENCIAS.md.

## Dictamen técnico

La implementación sigue el flujo docente: modelo entrenado y guardado, simulación/inferencia, API, consumo HTTP, imagen, contenedor y preparación de nube. Adapta el contenido a AI-SupportAssist. El nombre del archivo serializado, el módulo y el endpoint pueden cambiar si las rutas y comandos coinciden.

| Comprobación | Ejemplos docentes | AI SupportAssist | Estado de revisión |
|---|---|---|---|
| Modelo serializado | model.pkl o modelo_desercion.pkl | models/financial_nb.joblib y metadata.json | Modelo regenerado y recargado; matriz histórica reproducida |
| API | FastAPI en app.py/main.py | app/main.py con carga durante lifespan | Pruebas de contrato satisfactorias |
| Entradas | Campos tipados de transacción o consulta de deserción | JSON con texto e idioma declarado | Validación y errores probados |
| Salud | GET /health | GET /health y /ready | HTTP 200 comprobado en Docker y Render |
| Inferencia | POST /predict | POST /api/v1/predict | Consumo HTTP y navegador comprobados |
| Dependencias | requirements.txt | Versiones fijadas de inferencia y desarrollo | Instalación y ejecución local comprobadas |
| Imagen base | python:3.12-slim en ambos ejemplos GitHub | python:3.12-slim | Coincide la familia de runtime |
| Puerto interno | Tema 15: 8000; tema 16: 80 | 8000 en Uvicorn, EXPOSE y healthcheck | Configuración coherente |
| Publicación de puerto | 8000:8000 o 8000:80 | 127.0.0.1:8000:8000 en Compose | Restricción local intencional |
| Consumo externo | test_api.py o SimulaConsumo.py | scripts/smoke.py | Diez verificaciones HTTP satisfactorias |
| Frontend | Swagger; no interfaz propia en los main.py revisados | HTML/CSS/JS con fetch real | Chromium comprobó dos rutas, rechazo de español y vista móvil |
| Nube | Estrategia PaaS y Procfile del ejemplo | Docker sobre PaaS y render.yaml | Render Live y comprobación HTTP pública conservada |
| Documentación | README y plantilla técnica | README, manual, referencias y matriz de comprobación | Adaptados al proyecto |

## Resultados ejecutados en el entorno de desarrollo

- Regeneración de MultinomialNB: umbral 0.24, matriz `[[3333,8],[0,1462]]`, F1 0.9972714870395635 y recall 1.0 en el test histórico de 4,803 registros.
- Recarga Joblib: probabilidades exactamente iguales a las del estimador en memoria.
- Pytest: 30 pruebas satisfactorias; un aviso de deprecación de AnyIO/Starlette sin fallo.
- HTTP real: 10 verificaciones satisfactorias con Uvicorn, incluyendo la API desde otro programa.
- Chromium: ruta financiera, otra ruta, revisión de español, vista móvil y cero errores JavaScript.

Las evidencias se guardan en `evidence/model_reconstruction.json`, `junit-local.xml`, `http-local.json`, `browser.json` y capturas PNG. Las fechas técnicas de los JSON se expresan en UTC; pueden caer en el día siguiente a la fecha de México.

## Construcción Docker y ejecución local

El run 41374877919 acredita Docker en GitHub Actions. Las capturas E01 a E06 acreditan adicionalmente la ejecución en Windows del estudiante: imagen 7d109de9eb50, contenedor healthy y rutas financiera y no financiera en localhost. Las figuras E07 y E08 acreditan publicación en Render del commit eba2c4f y resultado del frontend público. Consulte evidence/capturas/README.md y evidence/render/cloud-http.json. Los ID de imagen de CI y de la laptop pertenecen a construcciones distintas.

## Diferencias justificadas y correcciones a las referencias PDF

Se mantiene el mismo patrón de los ejemplos GitHub, con mejoras de validación, usuario de ejecución sin privilegios, healthcheck, límites de entrada y supervisión humana. El umbral 0.24 procede de actividad 6 y debe aplicarse a predict_proba; usar sólo predict no reproduce la política validada.

El archivo se llama Dockerfile; no Docker ni Dockerfile.txt. `docker ps` lista contenedores y `docker build` construye imágenes. La estrategia Docker/PaaS se documenta separada del runtime Python/Procfile para evitar combinar comandos incompatibles. No se requiere copiar Python 3.9 o las versiones antiguas del PDF cuando el modelo fue regenerado y probado con Python 3.12 y scikit-learn 1.8.0.

No se afirma uso real de Microsoft Copilot: se documenta ChatGPT/Codex y se entregan prompts transferibles con sus criterios de revisión. La documentación conceptual toma la plantilla como referencia y no declara certificación ISO.
