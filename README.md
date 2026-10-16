# Act5_GP

Actividad 5 de Gestión de proyectos de inteligencia artificial. El proyecto da continuidad a AI-SupportAssist de NovaMarket mediante un prototipo de clasificación de solicitudes de soporte.

## Estado de avance

Paso 1 completado: estructura y conexión del repositorio. Paso 2 completado: configuración de seguimiento local con MLflow y prueba de persistencia de parámetros, métricas y artefactos. La validación incluida se ejecutó en un entorno local con Python 3.12; en Colab se reproducirá al ejecutar el notebook.

La selección del dataset, los algoritmos y el entrenamiento se desarrollarán en los siguientes pasos. Las métricas de control de este paso no son resultados de un modelo.

## Estructura

| Ruta | Propósito |
|---|---|
| `datos/datos_ini/` | Datos públicos originales y documentación de su origen |
| `datos/datos_limp/` | Datos limpios y versionados |
| `fuentes/entrena.ipynb` | Notebook de Colab para entrenamiento y evaluación |
| `fuentes/datos_prep.py` | Funciones de limpieza |
| `fuentes/train.py` | Entrada por consola; actualmente verifica MLflow sin entrenar |
| `fuentes/mlflow_config.py` | Configuración local y comprobación de persistencia |
| `requirements.txt` | Dependencias fijadas para el paso 2 |
| `evidencias/mlflow_verificacion.json` | Evidencia de la validación local ejecutada |
| `README.md` | Guía de reproducción y decisiones |
| `CHANGELOG.md` | Historial de cambios y reporte final |

`Act5_GP` es el nombre elegido para el repositorio y cumple la función de la carpeta raíz `Actividad5` de la consigna. Las carpetas de datos incluyen archivos `.gitkeep` para conservarlas mientras están vacías. El notebook y el script de entrada ya implementan la configuración de MLflow. Las funciones de limpieza y entrenamiento se completarán por etapas.

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

La evidencia JSON muestra `VALIDACION_CORRECTA` y seis controles en `true`. El archivo publicado procede de una ejecución local verificada. El commit base identifica el punto de partida del código y el hash `fuente_sha256` identifica el módulo usado. Los identificadores de esa evidencia no implican que los runs existan en tu entorno: al ejecutar tú el notebook se crean tu base, tus artefactos y tu evidencia.

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

## Trabajo posterior

Seleccionar al menos dos algoritmos y un dataset público, definir métricas estandarizadas, preparar y versionar los datos, ejecutar validación cruzada y Grid Search, registrar resultados en MLflow y documentar la comparación técnica. Cada etapa se agregará mediante commits identificables.

Los datos de NovaMarket y las metas de la fase 1 se tratarán como contexto del business case, no como resultados de este repositorio. No guardar contraseñas, tokens ni información personal de clientes.

## Referencias del paso 2

MLflow Project. (s. f.). *MLflow Tracking Quickstart*. https://mlflow.org/docs/latest/ml/tracking/quickstart/

MLflow Project. (s. f.). *Python API*. https://mlflow.org/docs/latest/api_reference/python_api/mlflow.html
