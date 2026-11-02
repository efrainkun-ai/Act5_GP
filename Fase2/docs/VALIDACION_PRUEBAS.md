# Validación y pruebas de AI SupportAssist

Proyecto fase 2 · Gestión de proyectos de inteligencia artificial
Efraín Cuatecontzi Mendoza
Universidad Tecmilenio · 1 de noviembre de 2026 · Versión 2.0

## 1 Propósito y dictamen

La aplicación de triaje financiero superó las verificaciones funcionales definidas para el prototipo: 30 pruebas automatizadas, 10 comprobaciones HTTP sobre el contenedor y un recorrido de interfaz en Chromium. La imagen se construyó y el contenedor alcanzó estado running y healthy en GitHub Actions. Las capturas incorporadas acreditan además la construcción y ejecución local en Windows y el despliegue público en Render. La comprobación HTTP de nube pasó diez casos y una consulta adicional de Swagger. El resultado respalda la demostración funcional; no acredita operación productiva.

Este documento presenta las entradas evaluadas, los resultados esperados y observados, la trazabilidad de las evidencias y las limitaciones pendientes. Las excepciones de arranque y los rechazos HTTP se consideran resultados correctos cuando coinciden con el comportamiento esperado.

## 2 Alcance y continuidad

La fase 1 plantea el caso NovaMarket; la actividad 5 desarrolla clasificación de 27 intenciones y la actividad 6 selecciona MultinomialNB para derivación financiera binaria. Se conserva TF-IDF, alpha=0.1 y umbral 0.24. La clase 1 comprende INVOICE, PAYMENT, REFUND y CANCEL; cancel_order permanece en ORDER y en clase 0. El sistema no implementa RAG, auto-resolución ni autorización de pagos o reembolsos.

| Entorno o componente | Configuración y evidencia |
| --- | --- |
| Reconstrucción del modelo | Python 3.12.14; scikit-learn 1.8.0; NumPy 2.3.5; SciPy 1.17.0; Joblib 1.5.3. |
| API e interfaz | FastAPI 0.115.12; Uvicorn 0.34.2; HTML/CSS/JavaScript con fetch; mismo origen. |
| Automatización en GitHub | Ubuntu 24.04.5; Python 3.12.15 en el host del runner; workflow concluido satisfactoriamente. |
| Contenedor | Imagen python:3.12-slim; Linux amd64; usuario appuser; puerto interno y publicado 8000. |
| Fecha de las evidencias | 2 de noviembre de 2026 en UTC; corresponde al 1 de noviembre en Ciudad de México. |

Se utiliza el modelo regenerado y verificado para esta entrega. No se presenta como el binario histórico de un run de MLflow. La evaluación del modelo se limita a inglés sintético y a la prueba histórica ya observada.

## 3 Pruebas funcionales realizadas

La suite utiliza FastAPI TestClient para validar el contrato y los casos de entrada. Además, scripts/smoke.py consume por HTTP el servicio ejecutado dentro de Docker; scripts/browser_check.py verifica la comunicación real navegador, API y resultado visible. Estas comprobaciones cubren capas diferentes y no se suman como casos independientes de calidad del modelo.

### 3 1 Contrato y endpoints

| Operación | Resultado esperado | Observado |
| --- | --- | --- |
| GET /health | Servicio disponible; status=ok. | HTTP 200 |
| GET /ready | Modelo cargado; status=ready. | HTTP 200 |
| GET /api/v1/model | Versión y umbral 0.24. | HTTP 200 |
| GET / | Interfaz accesible con formulario. | HTTP 200 |
| GET /static/app.js | JavaScript con llamada a la API. | HTTP 200 |
| GET /static/style.css | Estilos accesibles; validado con TestClient. | HTTP 200 |
| GET /openapi.json | Contrato incluye POST /api/v1/predict. | HTTP 200 |
| GET /docs | Documentación Swagger accesible. | HTTP 200 |

### 3 2 Solicitudes válidas

En todos los casos se envió language=en y se verificó HTTP 200, revisión humana requerida, identificador de solicitud, tiempo no negativo y coherencia entre clase y puntuación ≥ 0.24. Las seis expectativas coincidieron con los resultados.

| Texto de entrada | Clase esperada y observada | Ruta |
| --- | --- | --- |
| Where is my refund? | 1 / 1 | Financiera |
| How can I get my invoice? | 1 / 1 | Financiera |
| I have a payment issue | 1 / 1 | Financiera |
| I forgot my password | 0 / 0 | Otra ruta |
| I want to create an account | 0 / 0 | Otra ruta |
| Where is my order? | 0 / 0 | Otra ruta |

Fuentes: tests/test_integration.py; junit-ci.xml; container-http.json. Los endpoints /docs y /static/style.css se verificaron en la suite; no forman parte de las diez llamadas del smoke HTTP.

## 4 Casos extremos de entrada

Se probaron catorce entradas inválidas o fuera del alcance admitido. En todas se esperaba HTTP 422 sin clasificación operativa y se observó ese resultado. El identificador P corresponde al parámetro payload del caso test_invalid_and_out_of_scope.

| Caso | Entrada o condición | Esperado / observado |
| --- | --- | --- |
| P0 | Objeto JSON vacío: {}. | 422 / 422 |
| P1 | Falta language; text=refund. | 422 / 422 |
| P2 | Falta text; language=en. | 422 / 422 |
| P3 | Texto vacío. | 422 / 422 |
| P4 | Texto formado sólo por espacios. | 422 / 422 |
| P5 | text=null. | 422 / 422 |
| P6 | text=123; tipo numérico. | 422 / 422 |
| P7 | text=[refund]; tipo lista. | 422 / 422 |
| P8 | language=fr; idioma no admitido. | 422 / 422 |
| P9 | Campo adicional threshold=0.5. | 422 / 422 |
| P10 | Texto con 4,001 caracteres. | 422 / 422 |
| P11 | Quiero un reembolso; language=es. | 422 / 422 |
| P12 | Texto compuesto por tres emojis. | 422 / 422 |
| P13 | zzzxxyyqqq; sin vocabulario reconocido. | 422 / 422 |

### 4 1 Cuerpos malformados y método incorrecto

| Condición | Esperado / observado |
| --- | --- |
| Cuerpo de 33,000 bytes. | HTTP 413 / 413 |
| JSON incompleto: una llave de apertura. | HTTP 422 / 422 |
| GET sobre /api/v1/predict, que admite POST. | HTTP 405 / 405 |
| Cuerpo por fragmentos de 20,000 + 20,000 bytes. | HTTP 413 / 413 |

Los cuatro escenarios anteriores son aserciones de una sola prueba automatizada, test_oversized_and_malformed. El rechazo por exceso de tamaño se comprobó también sin depender de Content-Length. El caso en español verifica una restricción por idioma declarado; no acredita detección automática de idioma.

## 5 Umbral integridad y consistencia

### 5 1 Límite de la decisión financiera

Se sustituyó temporalmente predict_proba por valores controlados para aislar la regla puntuación ≥ 0.24. Son pruebas unitarias con puntuaciones simuladas; no corresponden a tickets reales que hayan producido exactamente esos valores.

| Puntuación simulada | Clase esperada | Clase observada |
| --- | --- | --- |
| 0.239999 | 0 | 0 |
| 0.240000 | 1 | 1 |
| 0.240001 | 1 | 1 |

### 5 2 Respuesta ante fallos y normalización

| Verificación | Resultado esperado y observado |
| --- | --- |
| Modelo corrupto | El arranque se detiene con RuntimeError por huella distinta; se comprobó. |
| Modelo ausente | El arranque se detiene con FileNotFoundError; se comprobó. |
| Normalización | Mayúsculas y espacios equivalentes generan la misma puntuación; correos, teléfono y entidad de prueba se sustituyen por marcadores. |
| Identidad de solicitudes | Dos consultas equivalentes conservan la puntuación y reciben identificadores distintos. |
| Coherencia de artefactos | Las huellas del modelo, preprocesamiento y script coinciden con los metadatos; la matriz registrada coincide. |
| Respuesta de validación | No devuelve SECRET-TEXT en el error; se verifican Cache-Control=no-store y X-Content-Type-Options=nosniff. |

Estas verificaciones no constituyen una auditoría de privacidad completa: las expresiones regulares no anonimizan todos los datos personales y las cabeceras no prueban protección de infraestructura o control de acceso.

### 5 3 Recuento de la suite

| Grupo | Casos |
| --- | --- |
| Contrato y frontend: 1; solicitudes válidas: 6. | 7 |
| Entradas inválidas parametrizadas. | 14 |
| Cuerpo y método: 1; normalización: 1; umbral: 3. | 5 |
| Modelo corrupto: 1; ausente: 1; artefactos: 1; cabeceras: 1. | 4 |
| Total; errores, fallos y omitidos: 0. | 30 |

La misma suite pasó en desarrollo y en el host del runner. Son 30 casos repetidos en dos entornos, no 60 casos diferentes. Las pruebas de TestClient se ejecutan en el host; el smoke HTTP y Chromium sí consumen el contenedor.

## 6 Resultados del modelo

La regeneración utilizó el CSV de Bitext con revisión y SHA-256 fijados, la misma limpieza y particiones estratificadas por intención: 14,408 registros para ajuste, 4,803 para validación y 4,803 para prueba. El umbral se seleccionó en validación; la prueba se usó para comprobar concordancia con actividad 6, sin elegir de nuevo el algoritmo.

### 6 1 Matriz de confusión

| Clase real | Predicción 0 | Predicción 1 |
| --- | --- | --- |
| No financiero | 3,333 VN | 8 FP |
| Financiero | 0 FN | 1,462 VP |

### 6 2 Métricas sobre 4803 registros históricos

| Métrica | Cálculo o interpretación | Resultado |
| --- | --- | --- |
| Exactitud | (3,333 + 1,462) / 4,803. | 99.8334 % |
| Precisión financiera | 1,462 / (1,462 + 8). | 99.4558 % |
| Recall financiero | 1,462 / (1,462 + 0). | 100 % |
| F1 financiero | Media armónica de precisión y recall. | 0.997271 |
| ROC AUC | Ordenamiento de puntuaciones continuas. | 0.99999877 |
| Costo supuesto en prueba | 5 × FN + FP; unidades hipotéticas. | 8 |
| Costo supuesto en validación | Costo usado para seleccionar 0.24. | 13 |

Se derivaron correctamente 1,462 solicitudes financieras y se enviaron ocho solicitudes no financieras a esa ruta. No hubo omisiones financieras en esta muestra. Las probabilidades del estimador recargado fueron idénticas a las del modelo en memoria sobre el test, con tolerancia cero en la comprobación de regeneración.

Los 4,803 registros se evaluaron directamente sobre el estimador: no se enviaron todos a la API ni al contenedor. Las diez comprobaciones HTTP validan integración, mientras el benchmark verifica el comportamiento predictivo histórico. Son evidencias complementarias.

### 6 3 Interpretación y límites

El resultado reproduce la política de actividad 6 y respalda la continuidad técnica. El test ya fue observado y el dataset es sintético en inglés, con posible dependencia entre paráfrasis. Cero FN no implica ausencia de riesgo en operación. Estos resultados no demuestran desempeño externo en español, superioridad estadística, mejora de FRT o CSAT, auto-resolución ni el ROI proyectado en fase 1.

## 7 Validación del contenedor y de la interfaz

El workflow 41374877919 concluyó con éxito. Construyó la imagen, inició Docker Compose, ejecutó diez comprobaciones HTTP y recorrió la interfaz en Chromium. La inspección conservada muestra el contenedor fase2-supportassist-1 en estado running y healthy, con 127.0.0.1:8000 publicado hacia 8000/tcp.

| Elemento | Resultado observado |
| --- | --- |
| Imagen | ai-supportassist:fase2; Linux amd64; usuario appuser. |
| ID de imagen | sha256:8d1d9239846d7a66c9142a5a2348fc75d7467701142aacf1ed75a811d7b25f38 |
| Contenedor | ID edd0ae244c12; salud healthy; estado running. |
| Construcción y ejecución | Ambos pasos concluyeron satisfactoriamente; el contenedor se detuvo y eliminó al finalizar. |
| Interfaz | Rutas financiera y de soporte, rechazo de español y vista móvil sin desbordamiento horizontal; cero errores JavaScript. |

### 7 1 Diez verificaciones HTTP sobre Docker

| Grupo de solicitudes | Esperado y observado | Cantidad |
| --- | --- | --- |
| GET /health, /ready, /, /static/app.js, /openapi.json y /api/v1/model. | HTTP 200 en las seis. | 6 |
| POST: Where is my refund? e I forgot my password; language=en. | HTTP 200; clases 1 y 0. | 2 |
| POST: texto vacío y solicitud declarada en español. | HTTP 422 en ambas. | 2 |

### 7 2 Puntuaciones y tiempos observados

| Solicitud | Puntuación | HTTP total | Inferencia |
| --- | --- | --- | --- |
| Where is my refund? | 0.997420 | 3.101 ms | 1.475 ms |
| I forgot my password | 0.001286 | 1.709 ms | 0.599 ms |

Los tiempos pertenecen a dos consultas individuales registradas en container-http.json. No son promedios, percentiles ni pruebas bajo carga y no sustentan un SLA. El tiempo HTTP incorpora comunicación y procesamiento; latency_ms corresponde al intervalo medido dentro del endpoint.

Los valores de esta sección corresponden al runner de GitHub Actions. Las capturas del estudiante acreditan adicionalmente Docker en Windows y el servicio público en Render. Sus resultados y la comprobación remota se presentan en la sección 10; cada entorno conserva su propia evidencia.

## 8 Conclusiones y seguimiento

La versión evaluada integra el modelo, el backend y la interfaz de manera funcional. Los casos válidos devolvieron rutas coherentes con el umbral, las entradas inválidas se rechazaron como estaba previsto y los fallos de integridad evitaron iniciar con un artefacto incorrecto. La imagen se construyó y el contenedor respondió correctamente en el entorno verificado.

La reproducción de la matriz y las métricas de actividad 6 confirma continuidad en el benchmark. El prototipo cumple los criterios de aceptación de las pruebas definidas; ello no equivale a cobertura exhaustiva ni aprobación para producción. Antes de ampliar su uso se requiere evaluación externa, medición de capacidad y controles operativos acordes al contexto.

| Pendiente | Acción y evidencia necesaria |
| --- | --- |
| Ejecución local y nube | Completadas para demostración: capturas de Docker en Windows y Render Live. Conservar las evidencias y repetir tras cambios de código. |
| Límites y robustez adicionales | Probar exactamente 4,000 caracteres, Unicode diverso, varias intenciones, tiempos de espera y fallos de red. |
| Rendimiento y seguridad | Medir concurrencia, memoria, p95 y recuperación; revisar autenticación y controles para un piloto real. |
| Validez externa | Pendiente: etiquetar tickets externos en español y separar por cliente o periodo. El despliegue público ya está ejecutado. |

## 9 Evidencias y trazabilidad

Código evaluado: f810851c66310fb1b5208d323c5bd3549bafaa66. El run de pull request comprobó la referencia de integración temporal 7fa0dd755431d10711966af90f724ef4bb0dc433. El SHA del modelo es 3bcdf28fb22781d16bb2840ac9bd2f1861c7aae2853e7f4fc40695e1c8553790.

Paquete fase2-evidencias-2, artefacto 13110821954: junit-ci.xml documenta 30 casos y cero fallos; container-http.json las diez solicitudes; docker-state.json y docker-image.json el estado y la imagen; browser.json la interfaz; model_reconstruction.json el benchmark. Los archivos del run se preservan en evidence/ci_run_41374877919 del repositorio. La retención original de Actions finaliza el 2 de diciembre de 2026.

## Referencias y fuentes del proyecto

Cuatecontzi Mendoza, E. (2026a). AI SupportAssist Fase 2 (Revisión f810851) [Código fuente]. GitHub. https://github.com/efrainkun-ai/Act5_GP/tree/f810851c66310fb1b5208d323c5bd3549bafaa66/Fase2

Cuatecontzi Mendoza, E. (2026b). Fase 2 API Docker e integración (Ejecución 41374877919) [Registro de pruebas]. GitHub Actions. https://github.com/efrainkun-ai/Act5_GP/actions/runs/41374877919

Bitext Innovations. (s. f.). Bitext customer support LLM chatbot training dataset (Revisión 430d1a8) [Conjunto de datos]. Hugging Face. https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset

## 10 Ejecución local y despliegue público

El archivo Captura de evitencias.docx contiene 13 imágenes revisadas. Ocho figuras seleccionadas se incluyen en los documentos Word entregados por separado; el repositorio conserva el inventario, SHA-256 y descripciones. Las figuras E03 a E08 se incorporan a este documento; E01 y E02 y la secuencia reproducible aparecen en el manual. Las capturas registran Windows, PowerShell, Docker Desktop, localhost y Render el 1 de noviembre de 2026. Los JSON técnicos remotos expresan fecha UTC.

| Entorno | Evidencia observada |
| --- | --- |
| Windows local | Commit eba2c4fe6ecbda062e71d6d3f71f8b6a29f97685; imagen ai-supportassist:fase2, ID 7d109de9eb50. Docker informa 550 MB de disco y 127 MB de contenido. |
| Contenedor local | fase2-supportassist-1 healthy; 127.0.0.1:8000 → 8000/tcp; /ready informa act6-nb-financial-v1. |
| Interfaz local | Reembolso: ruta financiera y 99.74 %. Contraseña: otra ruta y 0.13 %. Umbral 0.24. |
| Render público | Deploy succeeded y Live; revisión eba2c4f. La interfaz pública clasifica factura con puntuación 99.98 % e inferencia 1.82 ms en la captura. |

URL comprobada: https://ai-supportassist-fase2.onrender.com. La captura de exportación acredita comandos ejecutados en PowerShell, pero no se recibieron los archivos JSON originales de ese equipo; no se sustituyen por resultados del runner ni se atribuyen las pruebas remotas a la laptop.

### 10 1 Comprobación remota de la API pública

Registro: evidence/render/cloud-http.json; fecha UTC 2026-11-02T04:14:40.574108+00:00. Se ejecutaron las mismas diez solicitudes del smoke contra HTTPS. Los códigos y aserciones de las diez coincidieron con lo esperado; /docs se comprobó adicionalmente y devolvió HTTP 200 con HTML Swagger.

| Caso público | Esperado y observado |
| --- | --- |
| Seis GET de estado interfaz JavaScript contrato y modelo | 200 en las seis solicitudes. |
| Where is my refund? | 200; clase 1; puntuación 99.74 %. |
| I forgot my password | 200; clase 0; puntuación 0.13 %. |
| Texto vacío e idioma declarado español | 422 en ambos casos; rechazo previsto. |

Los registros incluyen request_id, versión, umbral y tiempos individuales. No son una evaluación bajo carga. La publicación del prototipo y las capturas prueban comunicación funcional de frontend, API y modelo; la validez predictiva continúa limitada al benchmark histórico en inglés sintético.

## 11 Evidencia de Docker en Windows

Figura E03 incluida en el documento Word entregado por separado.

La salida final confirma Image ai-supportassist:fase2 Built; ID local 7d109de9eb50, 550 MB de uso en disco y 127 MB de contenido.

Figura E04 incluida en el documento Word entregado por separado.

Docker Compose informa healthy; publica 127.0.0.1:8000 y /ready devuelve ready con act6-nb-financial-v1.

Los ID de imagen de CI y Windows corresponden a construcciones distintas. La imagen de Render se construyó desde GitHub y no se identifica con el ID local.

## 12 Evidencia de integración local

Figura E05 incluida en el documento Word entregado por separado.

Where is my refund? produce atención financiera humana y puntuación 99.74 % con umbral 0.24.

Figura E06 incluida en el documento Word entregado por separado.

I forgot my password produce otra ruta de soporte y puntuación financiera 0.13 %.

La decisión aplica la puntuación como número entre 0 y 1. El umbral 0.24 equivale a 24 %; ambas rutas mantienen revisión humana requerida.

## 13 Evidencia del despliegue público

Figura E07 incluida en el documento Word entregado por separado.

Render muestra Deploy succeeded y Live, fuente eba2c4f y Uvicorn escuchando en 0.0.0.0:8000.

Figura E08 incluida en el documento Word entregado por separado.

La URL ai-supportassist-fase2.onrender.com procesa How can I get my invoice? y muestra atención financiera humana con 99.98 %.

Fuente de las figuras: capturas proporcionadas por el estudiante. Se ajustó el encuadre para eliminar áreas ajenas al resultado. La aplicación desplegada conserva eba2c4f; esta actualización documental no cambia la implementación.
