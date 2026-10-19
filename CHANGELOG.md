# Historial de cambios y reporte de la actividad

## 0.5.0 Reporte técnico en PDF

- Se incorpora el informe de diez páginas en `informes/Reporte_Tecnico_Actividad5_AI_SupportAssist.pdf`.
- Se documentan los diez apartados solicitados, con cifras de experimentos reales, referencias y guía de reproducción.
- Se verifica visualmente la legibilidad de las tablas, gráficas y páginas.

## 0.4.0 Experimentos y evidencia para el reporte técnico

- Se implementa la preparación v1 con auditoría, reglas explícitas y dataset limpio reproducible.
- Se versionan hashes de datos limpios, split 80/20, cinco folds y código fuente.
- Se entrenan MultinomialNB y LinearSVC con TF-IDF, seis configuraciones y cinco folds por modelo.
- Se obtienen accuracy, precision/recall/F1 macro y ROC-AUC macro OvR sobre prueba reservada.
- Se registran 15 ejecuciones en MLflow, se guardan los Pipelines y se comprueba su recarga.
- Se incorpora comparación estadística exploratoria mediante McNemar exacta y bootstrap pareado.
- Se publican métricas, resultados por clase, errores agregados y figuras.
- Se amplía el notebook para reproducir el entrenamiento en Colab.
- Los resultados son experimentales con datos sintéticos en inglés y no validan las metas empresariales de fase 1.

## 0.3.0 Obtención reproducible y documentación de la entrega

- Se mantiene el repositorio `efrainkun-ai/Act5_GP` y su estructura existente.
- Se implementa `fuentes/obtener_datos.py` con bibliotecas estándar, descarga atómica, control de tamaños y SHA-256 y validación de estructura.
- Se fija la revisión de Bitext y se versionan los metadatos en `datos/dataset.lock.json`.
- Se documentan procedencia, licencia, idioma, limitaciones y campos del dataset.
- Se incorpora evidencia real de obtención y se amplía el notebook con la descarga.
- Se exportan las copias de los dos artefactos de MLflow y se comprueban contra las huellas del run del paso 2.
- Se documenta la correspondencia entre los cuatro requisitos y los archivos del repositorio.
- Este paso no ejecuta limpieza ni entrenamiento; la evidencia de MLflow sigue correspondiendo a configuración.

## 0.2.0 Configuración y validación de MLflow

- Se configura seguimiento local con SQLite y almacén de artefactos en disco.
- Se fijan las dependencias del paso 2 y se agrega `fuentes/mlflow_config.py`.
- `fuentes/train.py --verificar-mlflow` registra una prueba sin entrenar modelos.
- Se actualiza `fuentes/entrena.ipynb` para reproducir el flujo en Colab, con persistencia opcional en Drive.
- Se verifican cinco parámetros, dos métricas de control y dos artefactos recuperados después de cerrar el run.
- Se validan seis controles: estado final, parámetros, métricas, listado y contenido de ambos archivos.
- Se conserva evidencia de una ejecución local en `evidencias/mlflow_verificacion.json`.
- La base SQLite y el almacén de artefactos quedan excluidos del repositorio.
- La selección de datos y algoritmos y el entrenamiento siguen pendientes.

## 0.1.0 Preparación del entorno y repositorio

- Se utiliza el repositorio `efrainkun-ai/Act5_GP` creado por el estudiante.
- Se conserva la rama `main` y su commit inicial.
- Se agregan las carpetas `datos/datos_ini`, `datos/datos_limp` y `fuentes`.
- Se incorporan las plantillas `entrena.ipynb`, `datos_prep.py` y `train.py`.
- Se documentan la clonación, la conexión `origin` y la apertura del notebook en Colab.
- La selección de datos, la instalación de dependencias, el entrenamiento y el seguimiento con MLflow quedan pendientes para las etapas siguientes.

## Reporte final

Los resultados y decisiones se documentan en el reporte técnico en PDF. Las evidencias numéricas reproducibles están en `evidencias/entrenamiento_v1/`.
