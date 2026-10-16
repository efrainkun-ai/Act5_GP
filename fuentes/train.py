"""Entrada del proyecto. Paso 2: configuración y verificación de MLflow."""

import argparse
import json
from pathlib import Path

from mlflow_config import registrar_y_validar_prueba


def main():
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar-mlflow", action="store_true",
                        help="Registrar y recuperar una prueba sin entrenar modelos.")
    parser.add_argument("--tracking-dir", type=Path, default=raiz / ".mlflow_local")
    parser.add_argument("--evidencia", type=Path,
                        default=raiz / "evidencias" / "mlflow_verificacion.json")
    args = parser.parse_args()
    if not args.verificar_mlflow:
        parser.error("El entrenamiento está pendiente. Usa --verificar-mlflow para este paso.")
    resultado = registrar_y_validar_prueba(args.tracking_dir, args.evidencia)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print("Evidencia guardada en:", args.evidencia.resolve())


if __name__ == "__main__":
    main()
