"""Seguimiento local de MLflow y verificación de lectura después de escritura."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import mlflow
import sqlalchemy
from mlflow.tracking import MlflowClient

EXPERIMENTO = "Act5_GP_Configuracion"
ARTEFACTO_TEXTO = (
    "AI-SupportAssist: prueba de persistencia de artefactos en MLflow.\n"
    "Paso 2: configuración. No contiene un modelo ni resultados de entrenamiento.\n"
)


def configurar_mlflow(directorio: str | Path) -> dict:
    """Crea SQLite y el almacén local; reutiliza el experimento si ya existe."""
    base = Path(directorio).expanduser().resolve()
    artefactos = base / "artefactos"
    artefactos.mkdir(parents=True, exist_ok=True)
    tracking_uri = "sqlite:///" + (base / "mlflow.db").as_posix()
    mlflow.set_tracking_uri(tracking_uri)
    cliente = MlflowClient(tracking_uri=tracking_uri)
    experimento = cliente.get_experiment_by_name(EXPERIMENTO)
    if experimento is None:
        experimento_id = cliente.create_experiment(
            EXPERIMENTO, artifact_location=artefactos.as_uri()
        )
        experimento = cliente.get_experiment(experimento_id)
    if experimento.lifecycle_stage != "active":
        raise RuntimeError("El experimento está eliminado; restáuralo antes de continuar.")
    if experimento.artifact_location.rstrip("/") != artefactos.as_uri().rstrip("/"):
        raise RuntimeError("El experimento apunta a otro almacén de artefactos.")
    return {
        "tracking_uri": tracking_uri,
        "experiment_id": experimento.experiment_id,
        "experiment_name": experimento.name,
        "artifact_location": experimento.artifact_location,
        "base": str(base),
    }


def _sha256(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


def registrar_y_validar_prueba(directorio: str | Path, evidencia: str | Path) -> dict:
    """Registra parámetros, métricas y dos archivos; verifica su persistencia."""
    config = configurar_mlflow(directorio)
    if mlflow.active_run() is not None:
        raise RuntimeError("Finaliza la ejecución activa antes de iniciar la prueba.")
    parametros = {
        "proyecto": "AI-SupportAssist",
        "repositorio": "Act5_GP",
        "etapa": "2_configuracion_mlflow",
        "semilla": 42,
        "tipo_prueba": "infraestructura_sin_entrenamiento",
    }
    entorno = {
        "python": platform.python_version(),
        "mlflow": mlflow.__version__,
        "sqlalchemy": sqlalchemy.__version__,
        "backend": "SQLite local",
        "alcance": "Verificación técnica; no se evalúa ningún modelo.",
    }
    archivos = {
        "verificacion.txt": ARTEFACTO_TEXTO.encode("utf-8"),
        "entorno.json": json.dumps(entorno, ensure_ascii=False, indent=2).encode("utf-8"),
    }
    # Valores de control para comprobar el API; no son métricas predictivas.
    metricas = {"valor_prueba": 1.0, "artefactos_esperados": float(len(archivos))}
    raiz_repo = Path(__file__).resolve().parents[1]
    git = subprocess.run(
        ["git", "-C", str(raiz_repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    commit_base = git.stdout.strip() if git.returncode == 0 else "no_disponible"
    fuente_sha256 = _sha256(Path(__file__).read_bytes())
    with tempfile.TemporaryDirectory(prefix="act5_mlflow_") as temporal:
        temporal = Path(temporal)
        with mlflow.start_run(
            experiment_id=config["experiment_id"],
            run_name="verificacion_parametros_metricas_artefactos",
        ) as run:
            run_id = run.info.run_id
            mlflow.set_tags({
                "tipo": "prueba_configuracion",
                "entrenamiento": "no",
                "git_commit_base": commit_base,
                "fuente_sha256": fuente_sha256,
            })
            mlflow.log_params(parametros)
            mlflow.log_metrics(metricas)
            for nombre, contenido in archivos.items():
                archivo = temporal / nombre
                archivo.write_bytes(contenido)
                mlflow.log_artifact(str(archivo), artifact_path="verificacion")

        # Se vuelve a consultar el backend después de cerrar la ejecución.
        cliente = MlflowClient(tracking_uri=config["tracking_uri"])
        recuperado = cliente.get_run(run_id)
        controles = {
            "estado_finished": recuperado.info.status == "FINISHED",
            "parametros_recuperados": all(
                recuperado.data.params.get(k) == str(v) for k, v in parametros.items()
            ),
            "metricas_recuperadas": all(
                recuperado.data.metrics.get(k) == v for k, v in metricas.items()
            ),
        }
        listado = cliente.list_artifacts(run_id, "verificacion")
        rutas = {item.path for item in listado if not item.is_dir}
        controles["artefactos_listados"] = rutas == {
            "verificacion/" + nombre for nombre in archivos
        }
        hashes = {}
        for nombre, original in archivos.items():
            destino = temporal / "recuperados" / Path(nombre).stem
            destino.mkdir(parents=True)
            descargado = Path(cliente.download_artifacts(
                run_id, "verificacion/" + nombre, str(destino)
            ))
            recibido = descargado.read_bytes()
            controles["contenido_" + nombre] = recibido == original
            hashes[nombre] = _sha256(recibido)
        if not all(controles.values()):
            raise RuntimeError("La verificación de MLflow falló: " + str(controles))

    resultado = {
        "resultado": "VALIDACION_CORRECTA",
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "experiment_name": config["experiment_name"],
        "experiment_id": config["experiment_id"],
        "run_id": run_id,
        "estado": recuperado.info.status,
        "parametros": recuperado.data.params,
        "metricas": recuperado.data.metrics,
        "artefactos_sha256": hashes,
        "controles": controles,
        "entorno": entorno,
        "fuente_sha256": fuente_sha256,
        "git_commit_base": commit_base,
        "nota": "Prueba local de infraestructura. Sin entrenamiento ni métricas predictivas.",
    }
    destino_evidencia = Path(evidencia).resolve()
    destino_evidencia.parent.mkdir(parents=True, exist_ok=True)
    destino_evidencia.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return resultado
