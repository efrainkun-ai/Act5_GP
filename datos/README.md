# Origen y obtención de los datos

Se utiliza la alternativa de la consigna **scripts de obtención**. El CSV completo no se aloja en este repositorio: se obtiene desde una revisión fija de su fuente pública. `dataset.lock.json` versiona la revisión, URL, tamaño, SHA-256, campos y dimensiones esperadas. El script rechaza archivos que no coinciden y no sobrescribe una copia existente alterada.

## Fuente

Bitext Innovations. (2024). *Bitext customer support LLM chatbot training dataset* [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset

Licencia declarada por el autor: **CDLA Sharing 1.0**. Texto: https://cdla.dev/sharing-1-0/. El script descarga también la ficha de la revisión original como `README_fuente.md`. Conservar la atribución y revisar la licencia de la fuente antes de distribuir datos derivados.

## Alcance y continuidad

El dataset contiene solicitudes de atención al cliente en inglés, generadas con una metodología híbrida sintética y supervisión lingüística. Permite explorar el reconocimiento de intenciones como componente del triaje de AI-SupportAssist. No son tickets reales de NovaMarket ni validan sus metas operativas o financieras. Una futura evaluación en español requiere datos adicionales.

El archivo verificado tiene **26,872 registros, cinco campos, 27 intenciones y 11 categorías**. Se reportan las categorías observadas en el CSV, ya que la descripción narrativa de la ficha no coincide completamente con su contenido. No se inventa una correspondencia con departamentos de NovaMarket.

| Campo | Descripción | Uso previsto |
|---|---|---|
| flags | Marcas de variación lingüística | Documentación y análisis |
| instruction | Solicitud del usuario | Texto de entrada |
| category | Categoría semántica | Contexto de la etiqueta |
| intent | Intención de la solicitud | Objetivo de clasificación |
| response | Respuesta de ejemplo | Excluida como entrada para evitar fuga de información |

## Reproducción

Desde la raíz de `Act5_GP`, con Python 3.12 e internet:

```bash
python fuentes/obtener_datos.py
python fuentes/obtener_datos.py --solo-verificar
```

No se requieren paquetes externos ni token de Hugging Face para esta descarga pública. Se guarda el CSV original y la ficha en `datos/datos_ini/`, y la evidencia en `evidencias/dataset_obtencion.json`. La salida satisfactoria indica `OBTENCION_VERIFICADA`.

`datos/datos_limp/` se reserva para la siguiente etapa. Esta entrega obtiene y verifica datos originales; no realiza limpieza, partición ni entrenamiento.
