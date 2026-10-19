# Actividad 5 AI SupportAssist versión 3

Proyecto académico de clasificación de 27 intenciones de soporte con datos híbridos sintéticos en inglés de Bitext. No valida producción en español, auto-resolución ni ROI de NovaMarket.

## Reproducción en Colab
Abrir `fuentes/entrena.ipynb`, usar CPU y ejecutar en orden. La instalación muestra progreso; reiniciar manualmente solo si se actualizan bibliotecas ya importadas. Google Drive es opcional. La última celda descarga el ZIP del lote.

## Reproducción local
Desde `Actividad5/`: `python -m pip install -r requirements.txt` y `python fuentes/train.py`. `ACT5_ROOT` cambia la carpeta de salida. El script obtiene y comprueba el CSV original.

## Trazabilidad
Antes de entrenar se obtiene un commit de `efrainkun-ai/Act5_GP` y se comparan byte a byte `Actividad5/fuentes/train.py` y `datos_prep.py` con los scripts usados. Si difieren, el programa se detiene. `ACT5_CODE_REF` permite fijar un commit histórico y `ACT5_CODE_REPO` permite reutilizar un clon local. Los 15 runs de MLflow registran el mismo commit.

## Datos y selección
Revisión de origen: `430d1a89bd93bd1fa23c16f29dd53e73f0087443`. Se aplican limpieza determinista, auditoría y deduplicación antes de separar 80/20. TF-IDF se ajusta dentro de cada fold. Se comparan MultinomialNB y LinearSVC con seis candidatos y cinco folds; decide F1 macro de CV. Se muestran y exportan los mejores hiperparámetros y todas las métricas de clasificación, incluido ROC-AUC macro uno contra el resto.

## Evidencias
Cada lote se guarda en `evidencias/<batch_id>/`. Incluye `mejores_hiperparametros.csv`, `mejores_hiperparametros.json`, `codigo_versionado.json`, `mlflow_verificacion.json`, `mlflow_runs.csv`, tablas de CV, estadísticas, métricas por clase y gráficas. Los resultados se publican por lote conservando su commit de código. El CSV limpio, la base y modelos se regeneran; el paquete de entrega no traslada SQLite a otra ubicación.

## Fuente y licencia
Bitext Innovations (s. f.). Dataset público: https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset. Licencia declarada CDLA Sharing 1.0. Las referencias completas están en `REFERENCIAS.md`.
