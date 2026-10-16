# Act5_GP

Actividad 5 de Gestión de proyectos de inteligencia artificial. El proyecto da continuidad a AI-SupportAssist de NovaMarket mediante un prototipo de clasificación de solicitudes de soporte.

## Estado del paso 1

Repositorio inicial preparado en la rama `main` con carpetas de datos y plantillas de código. La selección del dataset, los algoritmos, la limpieza y el entrenamiento se desarrollarán en los siguientes pasos. Esta versión no contiene datos ni resultados experimentales.

## Estructura

| Ruta | Propósito |
|---|---|
| `datos/datos_ini/` | Datos públicos originales y documentación de su origen |
| `datos/datos_limp/` | Datos limpios y versionados |
| `fuentes/entrena.ipynb` | Notebook de Colab para entrenamiento y evaluación |
| `fuentes/datos_prep.py` | Funciones de limpieza |
| `fuentes/train.py` | Entrenamiento, ajuste y registro en MLflow |
| `README.md` | Guía de reproducción y decisiones |
| `CHANGELOG.md` | Historial de cambios y reporte final |

`Act5_GP` es el nombre elegido para el repositorio y cumple la función de la carpeta raíz `Actividad5` de la consigna. Las carpetas de datos incluyen archivos `.gitkeep` para conservarlas mientras están vacías. El notebook y los scripts son plantillas que se completarán por etapas.

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

Por ahora el notebook solo documenta el inicio del proyecto. La instalación de dependencias se incorporará al definir los algoritmos y las herramientas del experimento.

## Trabajo posterior

Seleccionar al menos dos algoritmos y un dataset público, definir métricas estandarizadas, preparar y versionar los datos, ejecutar validación cruzada y Grid Search, registrar resultados en MLflow y documentar la comparación técnica. Cada etapa se agregará mediante commits identificables.

Los datos de NovaMarket y las metas de la fase 1 se tratarán como contexto del business case, no como resultados de este repositorio. No guardar contraseñas, tokens ni información personal de clientes.
