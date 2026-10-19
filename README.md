# Act5_GP

Actividad 5 de Gestión de proyectos de inteligencia artificial. El proyecto da continuidad a AI-SupportAssist de NovaMarket mediante un prototipo de clasificación de solicitudes de soporte.

## Estado de avance

Se completaron la preparación del repositorio, la obtención verificada del dataset, la configuración de MLflow y los experimentos requeridos para el reporte técnico. El entrenamiento se ejecutó localmente con Python 3.12 y dependencias fijadas; el notebook permite reproducirlo en Colab.

El experimento `Act5_GP_Entrenamiento_v1` compara MultinomialNB y LinearSVC con TF-IDF, cinco folds estratificados, Grid Search y prueba reservada. Los resultados, las verificaciones y las versiones se conservan en `evidencias/entrenamiento_v1/`. Son resultados de un prototipo con datos sintéticos en inglés, no de producción en NovaMarket.

## Estructura

| Ruta | Propósito |
|---|---|
| `datos/datos_ini/` | Datos públicos originales y documentación de su origen |
| `datos/datos_limp/` | Datos limpios y versionados |
| `fuentes/entrena.ipynb` | Notebook de Colab para entrenamiento y evaluación |
| `fuentes/datos_prep.py` | Limpieza determinista, deduplicación y auditoría completa |
| `fuentes/obtener_datos.py` | Descarga atómica y verificación del dataset de origen |
| `datos/dataset.lock.json` | Revisión, URLs, hashes y estructura esperada |
| `datos/README.md` | Origen, licencia y diccionario de campos |
| `fuentes/train.py` | Entrada por consola para verificar MLflow o ejecutar el entrenamiento |
| `fuentes/experimentos.py` | Pipelines, Grid Search, métricas, estadística y registro de modelos |
| `fuentes/mlflow_config.py` | Configuración local y comprobación de persistencia |
| `requirements.txt` | Dependencias fijadas para el paso 2 |
| `evidencias/mlflow_verificacion.json` | Evidencia de la validación local ejecutada |
| `evidencias/artefactos_mlflow/` | Archivos recuperados de la ejecución de MLflow |
| `evidencias/dataset_obtencion.json` | Resultado real de la descarga y verificación del dataset |
| `README.md` | Guía de reproducción y decisiones |
| `CHANGELOG.md` | Historial de cambios y reporte final |

`Act5_GP` es el nombre elegido para el repositorio y cumple la función de la carpeta raíz `Actividad5` de la consigna. Las carpetas de datos incluyen archivos `.gitkeep` para conservarlas mientras están vacías. El notebook y el script de entrada ya implementan la configuración de MLflow. La preparación y el entrenamiento ya se implementan mediante módulos separados.

## Obtener una copia y comprobar la conexión

```bash
git clone https://github.com/efrainkun-ai/Act5_GP.git
cd Act5_GP
git remote -v
git status
```

El remoto `origin` debe apuntar a `https://github.com/efrainkun-ai/Act5_GP.git`.

## Abrir el notebook en Colab

1. Abre https://colab.research.google.com/.
2. Selecciona **Archivo > Abrir cuaderno > GitHub**.
3. Introduce `https://github.com/efrainkun-ai/Act5_GP`.
4. Abre `fuentes/entrena.ipynb` en la rama `main`.

El notebook incluye descarga del repositorio, instalación de dependencias, ubicación del seguimiento, registro y verificación. En Colab guarda por defecto la base y los artefactos en `MyDrive/Act5_GP/mlflow_local`. Para usar almacenamiento temporal cambia `GUARDAR_EN_DRIVE=False`.

## Obtener el dataset público

Desde la raíz del repositorio, con Python 3.12 e internet:

```bash
python fuentes/obtener_datos.py
python fuentes/obtener_datos.py --solo-verificar
```

La obtención utiliza solo bibliotecas estándar de Python. El script descarga el CSV y la ficha originales desde la revisión fija `430d1a89bd93bd1fa23c16f29dd53e73f0087443` de Bitext, comprueba los tamaños y hashes de ambos archivos y valida los cinco campos, 26,872 filas, 27 intenciones y 11 categorías. No sobrescribe un archivo existente que no coincide. El segundo comando verifica las copias existentes sin descargarlas.

El archivo original y la ficha se conservan en `datos/datos_ini/` y se excluyen de Git porque esta entrega utiliza scripts de obtención. La evidencia queda en `evidencias/dataset_obtencion.json`. La revisión y las huellas están versionadas en `datos/dataset.lock.json`; un cambio futuro de fuente deberá documentarse como una versión nueva.

La entrada prevista es `instruction` y el objetivo es `intent`. No se utilizará `response` como predictor. El dataset es híbrido sintético y está en inglés: sirve como referencia académica de triaje, no como validación de tickets reales de NovaMarket en español. Consulta el origen, la licencia y cada campo en [datos/README.md](datos/README.md).

El notebook incluye una sección del paso 3 para ejecutar esta misma descarga; en Colab con Drive habilitado conserva los originales en `MyDrive/Act5_GP/datos/datos_ini/`.

## Configurar y verificar MLflow desde la consola

Con Python 3.12, desde la raíz del repositorio:

```bash
python -m pip install -r requirements.txt
python fuentes/train.py --verificar-mlflow
```

Se utiliza **seguimiento local**, con base SQLite en `.mlflow_local/mlflow.db` y archivos en `.mlflow_local/artefactos`. No requiere un servidor ni una cuenta remota. `requirements.txt` fija MLflow 3.5.0, SQLAlchemy 2.0.43 y packaging 25.0.

La ejecución crea o reutiliza `Act5_GP_Configuracion` y registra:

- Parámetros: proyecto, repositorio, etapa, semilla y tipo de prueba.
- Métricas de control: `valor_prueba=1.0` y `artefactos_esperados=2.0`.
- Artefactos: `verificacion/verificacion.txt` y `verificacion/entorno.json`.
- Etiquetas: tipo de ejecución, ausencia de entrenamiento, commit base y hash del módulo.

Luego cierra el run y vuelve a consultar el backend. Verifica el estado `FINISHED`, todos los parámetros y métricas, el listado de artefactos y la igualdad byte a byte de los archivos descargados. Si algún control falla el comando termina con error. Cada repetición crea un run nuevo, conservando el historial del experimento.

La evidencia JSON muestra `VALIDACION_CORRECTA` y seis controles en `true`. Las copias de los dos archivos recuperados están disponibles en `evidencias/artefactos_mlflow/`; sus hashes coinciden con el JSON. Consulta [evidencias/README.md](evidencias/README.md) para interpretar su alcance. El archivo publicado procede de una ejecución local verificada. El commit base identifica el punto de partida del código y el hash `fuente_sha256` identifica el módulo usado. Los identificadores de esa evidencia no implican que los runs existan en tu entorno: al ejecutar tú el notebook se crean tu base, tus artefactos y tu evidencia.

En Colab la evidencia queda junto al seguimiento en Drive. Para elegir rutas propias desde consola:

```bash
python fuentes/train.py --verificar-mlflow --tracking-dir ./seguimiento --evidencia ./seguimiento/verificacion.json
```

## Consultar la interfaz local

Después de la prueba por consola:

```bash
mlflow ui --backend-store-uri sqlite:///.mlflow_local/mlflow.db --host 127.0.0.1 --port 5000
```

Abre `http://127.0.0.1:5000`, elige `Act5_GP_Configuracion` y revisa parámetros, métricas y artefactos. En Colab la validación utiliza el cliente y no necesita un túnel público. La base y los artefactos se guardan juntos en su ubicación de trabajo y no se suben a GitHub. El repositorio contiene la configuración y la evidencia reproducible.

## Reproducir preparación y entrenamiento

```bash
python -m pip install -r requirements.txt
python fuentes/obtener_datos.py
python fuentes/train.py --entrenar
```

El segundo modo de `train.py`, `--verificar-mlflow`, conserva la prueba de infraestructura del paso 2. `--entrenar` prepara el dataset, crea particiones, entrena los dos modelos, ajusta hiperparámetros, evalúa, calcula ROC-AUC macro OvR y registra modelos y artefactos reales en MLflow. El modo de entrenamiento necesita CPU, no GPU ni servicios de pago.

| Evidencia | Contenido |
|---|---|
| `datos/preparacion_v1.json` | Hashes del dataset limpio, particiones, folds y fuentes |
| `evidencias/entrenamiento_v1/calidad_datos.json` | Diagnóstico y exclusiones |
| `evidencias/entrenamiento_v1/comparacion_modelos.csv` | Accuracy, precision, recall, F1, ROC-AUC, CV y recursos |
| `evidencias/entrenamiento_v1/*_grid.csv` | Configuraciones y resultados de cada fold |
| `evidencias/entrenamiento_v1/*_por_clase.csv` | Métricas desglosadas por intención |
| `evidencias/entrenamiento_v1/estadistica.json` | McNemar exacta y bootstrap pareado |
| `evidencias/entrenamiento_v1/mlflow_runs.csv` | Las 15 ejecuciones de la corrida |
| `evidencias/entrenamiento_v1/mlflow_evidencia.json` | Parámetros, métricas, artefactos y recarga de ambos modelos |
| `evidencias/entrenamiento_v1/figuras/` | Gráficos obtenidos del experimento |

Los CSV limpios y las particiones se regeneran en `datos/datos_limp/` y se excluyen de Git; sus hashes quedan versionados. La base SQLite, los modelos exportados y el almacén completo de MLflow permanecen en `.mlflow_local/` o en la ruta indicada con `--tracking-dir`. Al reproducir se generan nuevos identificadores de run. La evidencia publicada pertenece a la ejecución local documentada.

## Decisiones y límites

Se excluyen textos vacíos, etiquetas contradictorias y duplicados exactos después de normalizar. Se reserva 20 % de prueba y TF-IDF se aprende dentro de cada fold. F1 macro de CV decide la selección. ROC-AUC se calcula por clase frente al resto: probabilidades en Naive Bayes y márgenes de decisión en SVM, sin tratar márgenes como probabilidades.

SVM lineal fue seleccionado por CV. La diferencia de accuracy en prueba no resultó concluyente al nivel del 5 %. No se modifica la configuración usando ese conjunto de prueba. Aún se requiere evaluación externa en español, separación por familias de paráfrasis cuando existan sus identificadores, revisión humana, monitoreo y validación operativa de FRT, AHT, CSAT y ROI.

Los parámetros del business case de NovaMarket siguen siendo metas o supuestos. No se ha desplegado este prototipo en producción.

## Referencias del paso 2

MLflow Project. (s. f.). *MLflow Tracking Quickstart*. https://mlflow.org/docs/latest/ml/tracking/quickstart/

MLflow Project. (s. f.). *Python API*. https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html

## Referencia del dataset

Bitext Innovations. (2024). *Bitext customer support LLM chatbot training dataset* [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset
