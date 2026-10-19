# Evidencias de reproducción

## MLflow

`mlflow_verificacion.json` conserva la evidencia del paso 2: experimento `Act5_GP_Configuracion`, run `3ee54eddf679434480ac07941f52f15d`, estado `FINISHED`, cinco parámetros, dos métricas de control y seis comprobaciones satisfactorias.

Los archivos `artefactos_mlflow/verificacion.txt` y `artefactos_mlflow/entorno.json` se recuperaron del almacén de ese run. Sus SHA-256 coinciden con `artefactos_sha256` del JSON. La copia exportada permite revisar el contenido sin acceder a la base de seguimiento del entorno original.

Estas son evidencias de **configuración de MLflow**. `valor_prueba` y `artefactos_esperados` no son métricas predictivas. No hay modelos entrenados en esta entrega por etapas. La base SQLite y el almacén completo permanecen fuera de GitHub y se regeneran con:

```bash
python -m pip install -r requirements.txt
python fuentes/train.py --verificar-mlflow
```

Una reproducción crea un run nuevo con su propio identificador y actualiza la evidencia local. No debe esperarse que el run histórico del JSON esté en una instalación nueva.

## Dataset

`dataset_obtencion.json` documenta la ejecución real del script de obtención: revisión fija, hashes de los archivos, dimensiones, modalidad de obtención y controles. Se reproduce con:

```bash
python fuentes/obtener_datos.py
python fuentes/obtener_datos.py --solo-verificar
```

El CSV no se aloja en GitHub. Los scripts y el lock versionado permiten obtener los originales idénticos. La carpeta de datos limpios sigue reservada para la siguiente etapa.
