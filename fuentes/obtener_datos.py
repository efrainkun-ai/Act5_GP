"""Obtiene la versión fijada de Bitext y valida sus bytes y su estructura.

Este paso solo obtiene datos originales. No limpia, divide ni entrena modelos.
Solo utiliza bibliotecas de la distribución estándar de Python.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def huella(archivo: Path) -> str:
    h = hashlib.sha256()
    with archivo.open("rb") as entrada:
        for bloque in iter(lambda: entrada.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def validar_archivo(archivo: Path, especificacion: dict) -> None:
    if not archivo.is_file():
        raise FileNotFoundError(f"Falta el archivo original: {archivo}")
    if archivo.stat().st_size != especificacion["bytes"]:
        raise ValueError(f"Tamaño inesperado: {archivo.name}. No se modificó el archivo.")
    if huella(archivo) != especificacion["sha256"]:
        raise ValueError(f"SHA-256 incorrecto: {archivo.name}. No se modificó el archivo.")


def obtener_archivo(destino: Path, especificacion: dict, solo_verificar: bool) -> str:
    if destino.exists() or solo_verificar:
        validar_archivo(destino, especificacion)
        return "archivo_existente_verificado"
    # Solo se instala el archivo definitivo después de comprobar su integridad.
    with tempfile.TemporaryDirectory(prefix="descarga_", dir=destino.parent) as temporal:
        temporal = Path(temporal) / destino.name
        with urllib.request.urlopen(especificacion["url"], timeout=120) as respuesta:
            with temporal.open("wb") as salida:
                while bloque := respuesta.read(1024 * 1024):
                    salida.write(bloque)
        validar_archivo(temporal, especificacion)
        temporal.replace(destino)
    return "descargado_y_verificado"


def obtener_datos(destino: Path, evidencia: Path, solo_verificar: bool = False) -> dict:
    lock = json.loads((RAIZ / "datos" / "dataset.lock.json").read_text(encoding="utf-8"))
    destino.mkdir(parents=True, exist_ok=True)
    modos = {}
    for nombre, especificacion in lock["archivos"].items():
        modos[nombre] = obtener_archivo(destino / nombre, especificacion, solo_verificar)
    csv_path = destino / lock["archivo_csv"]
    intenciones, categorias = set(), set()
    filas = 0
    vacios = 0
    with csv_path.open(encoding="utf-8-sig", newline="") as entrada:
        lector = csv.DictReader(entrada)
        columnas = lector.fieldnames
        if columnas != lock["columnas"]:
            raise ValueError("Las columnas no coinciden con la versión documentada.")
        for registro in lector:
            if None in registro or any(v is None for v in registro.values()):
                raise ValueError("Se encontró una fila CSV mal formada.")
            filas += 1
            intenciones.add(registro["intent"])
            categorias.add(registro["category"])
            vacios += int(any(not registro[c].strip() for c in columnas))
    controles = {
        "integridad_archivos": True,
        "columnas_correctas": columnas == lock["columnas"],
        "filas_correctas": filas == lock["filas"],
        "intenciones_correctas": len(intenciones) == lock["intenciones"],
        "categorias_correctas": len(categorias) == lock["categorias"],
    }
    if not all(controles.values()):
        raise ValueError("La estructura no coincide con la versión fijada: " + str(controles))
    resultado = {
        "resultado": "OBTENCION_VERIFICADA",
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "version_dataset": lock["version"],
        "repositorio_origen": lock["repositorio"],
        "revision_origen": lock["revision"],
        "licencia_declarada": lock["licencia_declarada"],
        "filas": filas,
        "columnas": columnas,
        "intenciones": len(intenciones),
        "categorias": len(categorias),
        "filas_con_algun_campo_vacio": vacios,
        "modos_obtencion": modos,
        "sha256_archivos": {n: huella(destino / n) for n in lock["archivos"]},
        "controles": controles,
        "alcance": "Datos originales verificados. Sin limpieza ni entrenamiento.",
    }
    evidencia.parent.mkdir(parents=True, exist_ok=True)
    evidencia.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / "datos" / "datos_ini")
    parser.add_argument("--evidencia", type=Path, default=RAIZ / "evidencias" / "dataset_obtencion.json")
    parser.add_argument("--solo-verificar", action="store_true", help="Verificar archivos existentes sin descargarlos.")
    args = parser.parse_args()
    print(json.dumps(obtener_datos(args.destino, args.evidencia, args.solo_verificar), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
