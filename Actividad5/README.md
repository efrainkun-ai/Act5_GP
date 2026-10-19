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

## Resultado verificado y publicado

Lote `20261019T051743_4b3d97f7`, ejecutado localmente de principio a fin; no se presenta como una ejecución nueva de Colab. Código previo al entrenamiento: [`8eee1626fc0c40ae2efcbc16130e24ed0e589648`](https://github.com/efrainkun-ai/Act5_GP/commit/8eee1626fc0c40ae2efcbc16130e24ed0e589648). Los 15 runs están FINISHED y ligados a ese commit.

| Modelo | Mejor configuración | F1 macro CV | F1 macro prueba |
|---|---|---:|---:|
| MultinomialNB | alpha=0.1, n-gramas=(1,2) | 0.988880 | 0.989802 |
| LinearSVC | C=1.0, n-gramas=(1,2) | 0.991871 | 0.992678 |

McNemar exacta: p=0.072454; diferencia de accuracy no concluyente al 5 %. La selección usa F1 macro de CV. La prueba no modifica la cuadrícula. Los tiempos y las latencias dependen del entorno.

[Ver evidencias del lote](evidencias/20261019T051743_4b3d97f7/). [Reporte Word](informes/Actividad_5_ECM_GP_Completa.docx). [Referencias APA 7](REFERENCIAS.md). El notebook conserva las salidas de esta verificación; `fuentes/entrena_colab_v2_original.ipynb` conserva la ejecución previa entregada por el estudiante.

Los manifiestos incluyen hashes de los CSV sin compresión. `split_v1.csv.gz`, `folds_v1.csv.gz` y `audit_all_rows.csv.gz` se descomprimen con gzip; las huellas se contrastan con los bytes descomprimidos. El CSV completo y los Pipelines se regeneran con las mismas reglas.

Para fijar el código auditado antes de entrenar localmente: `ACT5_CODE_REF=8eee1626fc0c40ae2efcbc16130e24ed0e589648 python fuentes/train.py`. En Colab, asignar ese valor a `os.environ["ACT5_CODE_REF"]` antes de la celda de verificación Git si se desea reproducir exactamente esa revisión.
