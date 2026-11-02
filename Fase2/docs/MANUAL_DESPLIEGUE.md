# Manual de despliegue de AI SupportAssist

Versión 1.0 · 1 de noviembre de 2026 · Autor del proyecto: Efraín Cuatecontzi Mendoza · Universidad Tecmilenio · Estado: prototipo académico.

Este manual permite ejecutar el triaje financiero de AI-SupportAssist localmente y preparar su publicación en una plataforma administrada. Sigue la estructura conceptual de la plantilla del tema 16 y adapta la secuencia de los tutoriales de temas 15 y 16 al modelo ya evaluado en actividad 6. No declara certificación ISO ni un despliegue público realizado.

## 1 Propósito y alcance

Entregar una aplicación reproducible que reciba tickets de soporte y sugiera derivación a atención financiera humana u otra ruta de soporte. La solución incluye frontend, API REST, modelo y contenedor. Las funciones de RAG, sentimiento, prioridad, auto-resolución e integración con CRM siguen fuera de esta versión.

La fase 1 aporta el business case; actividad 5, datos y aprendizaje clásico; actividad 6, la decisión binaria y el umbral. Los ahorros, FRT, CSAT y ROI de fase 1 permanecen como proyecciones y no se infieren de las métricas del clasificador.

## 2 Responsables y arquitectura

El responsable técnico mantiene código, dependencias, modelo y pruebas. El operador de soporte revisa las rutas sugeridas. El responsable de seguridad establece acceso y conservación de información antes de un piloto con datos reales.

El navegador carga HTML, CSS y JavaScript desde FastAPI y envía `POST /api/v1/predict` mediante fetch. Pydantic valida JSON; el backend aplica normalización NFKC y marcadores, transforma el texto con TF-IDF y obtiene la puntuación de MultinomialNB. Una puntuación ≥ 0.24 activa la ruta financiera. Se devuelve JSON a la interfaz. Todos los componentes viven en un contenedor y comparten origen; no se requiere CORS para esta arquitectura.

El modelo se entrena offline. La imagen copia el Pipeline y metadatos; el arranque sólo verifica integridad y carga el estimador. No se entrena ni descarga el dataset durante una solicitud.

## 3 Requerimientos técnicos

| Recurso | Requisito o propuesta |
|---|---|
| Sistema anfitrión | Windows con Docker Desktop y soporte WSL2, macOS con Docker Desktop o Linux con Docker Engine |
| Git | Instalado para clonar y verificar revisiones |
| Docker | Motor activo; comprobar con `docker info` |
| Compose | Plugin v2; comprobar con `docker compose version` |
| Python local opcional | 3.12, para ejecutar fuera de Docker y generar pruebas |
| Python dentro del contenedor | Rama 3.12 de la imagen slim |
| Bibliotecas | Versiones fijadas en `requirements.txt`; desarrollo en `requirements-dev.txt` |
| Cómputo inicial propuesto | 1 vCPU y 1 GiB RAM para piloto; medir y ajustar con carga real |
| Disco local recomendado | Al menos 4 GiB libres para capas y caché; depende de Docker |
| Puerto | 8000 libre; `HOST_PORT` cambia sólo el puerto publicado por Compose |
| Red | Necesaria al construir para descargar imagen y dependencias; inferencia sin llamadas externas |
| GPU y base de datos | No requeridas para esta versión |
| Nube | Cuenta en el proveedor, acceso al repositorio y revisión del plan elegido |

Los recursos son una propuesta inicial, no un benchmark de capacidad. `python:3.12-slim` es una etiqueta móvil: registre el digest resuelto en cada construcción para identificar exactamente la imagen base.

## 4 Preparación del repositorio

Si es la primera vez en el equipo, ejecute:

```bash
git clone --branch fase2-ai-supportassist https://github.com/efrainkun-ai/Act5_GP.git
cd Act5_GP/Fase2
git rev-parse HEAD
docker version
docker compose version
docker info
```

Si ya tiene un clon, revise `git status`, conserve sus cambios y cambie a la rama correspondiente. No repita `git init` ni agregue de nuevo `origin`. Todos los comandos siguientes parten de `Fase2`, salvo donde se indique otra ruta.

Compruebe que existen `models/financial_nb.joblib`, `models/metadata.json`, `app/`, `requirements.txt`, `Dockerfile` y `compose.yaml`. No renombre el Dockerfile como `Docker` ni lo guarde con extensión `.txt`. El tutorial PDF contiene esa ambigüedad; el nombre que Docker reconoce aquí es **Dockerfile**.

## 5 Validación previa sin contenedor

Este paso es opcional para ejecutar la imagen incluida, pero útil para comparar resultados. Cree un entorno virtual con Python 3.12, actívelo e instale:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q --junitxml=evidence/junit-local.xml
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

En otra terminal:

```bash
python -m scripts.smoke --output evidence/http-local.json
```

Abra la interfaz en `http://localhost:8000/` y Swagger en `/docs`. Un resultado válido debe mostrar la clase, ruta y umbral 0.24. La puntuación representa la salida del modelo y no una probabilidad calibrada para tickets reales.

Detenga Uvicorn con Ctrl+C para liberar el puerto antes de iniciar el contenedor.

## 6 Construcción de la imagen Docker

```bash
docker compose config
docker build --progress=plain -t ai-supportassist:fase2 .
docker images ai-supportassist
docker image inspect ai-supportassist:fase2
```

El Dockerfile define el entorno Python, instala dependencias, copia código y modelo, crea un usuario sin privilegios, expone 8000, configura una prueba de salud y ejecuta Uvicorn en `0.0.0.0:8000`. No incluya datos de entrenamiento, `.env` ni cachés en el contexto; `.dockerignore` los excluye.

El criterio de aceptación es salida exitosa de la construcción y una imagen identificable con ID/digest. Guarde la salida de terminal. `EXPOSE 8000` documenta el puerto interno; no publica por sí mismo el puerto del equipo.

## 7 Ejecución local del contenedor

Ejecutar directamente la imagen construida:

```bash
docker run -d --name ai-supportassist-api -p 127.0.0.1:8000:8000 ai-supportassist:fase2
docker ps --filter name=ai-supportassist-api
docker logs ai-supportassist-api
docker inspect ai-supportassist-api
```

En PowerShell, verificar disponibilidad:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
$payload = @{text='Where is my refund?'; language='en'} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/v1/predict -Method Post -ContentType application/json -Body $payload
```

También puede usar Docker Compose, con la imagen recién construida:

```bash
docker compose up -d --wait --wait-timeout 90
docker compose ps
docker compose logs --no-color
```

Utilice una sola modalidad a la vez para evitar conflictos de puerto. Compose añade raíz de sólo lectura, `/tmp` temporal, eliminación de capacidades y restricción de privilegios. El healthcheck consulta `/ready`.

Para detener la modalidad directa:

```bash
docker stop ai-supportassist-api
docker rm ai-supportassist-api
```

Para detener Compose:

```bash
docker compose down
```

El comando correcto para ver contenedores activos es `docker ps`. En una sección del PDF de simulación aparece `docker build` bajo esa indicación; ese comando construye una imagen y no lista contenedores.

## 8 Pruebas y evidencia de integración

Con el contenedor funcionando y un entorno Python de desarrollo activado en otra terminal:

```bash
python -m scripts.smoke --output evidence/container-http.json
python -m playwright install chromium
python -m scripts.browser_check
```

Las pruebas HTTP comprueban estados, frontend, contrato, inferencia y rechazo de casos inválidos. La prueba de navegador selecciona ejemplos y verifica la respuesta visible después de la llamada real a la API; también comprueba revisión para español y presentación móvil.

Guarde el commit, salida de construcción, ID de imagen, estado del contenedor, logs, JSON de solicitudes y resultados, contrato OpenAPI y capturas. Los resultados esperados deben distinguirse de los observados. GitHub Actions ejecuta estas comprobaciones sobre Docker en su runner; eso demuestra ejecución en ese equipo remoto, no en la laptop del estudiante.

## 9 Estrategia de despliegue en la nube

Se propone **contenedor sobre PaaS administrado**. Permite conservar Dockerfile y modelo, mantener inferencia sin estado y reducir la administración de servidores. Render se documenta como ruta principal y Elastic Beanstalk con plataforma Docker como alternativa acorde al material académico. No se crean recursos ni se contratan planes al preparar este manual.

### Ruta principal en Render

1. Verifique que la rama y los archivos estén publicados en GitHub y que las pruebas del commit sean satisfactorias.
2. Ingrese a su cuenta de Render y cree un servicio web conectado a `efrainkun-ai/Act5_GP`.
3. Seleccione la rama `fase2-ai-supportassist` y runtime **Docker**.
4. Configure **Root Directory: `Fase2`**, **Dockerfile Path: `./Dockerfile`** y **Docker Build Context: `.`**, relativos a esa raíz. No configure un comando de build Python además del Dockerfile.
5. Mantenga el CMD del Dockerfile: Uvicorn escucha en `0.0.0.0:8000`. Configure `PORT=8000` si el proveedor solicita declarar el puerto. El CMD es fijo en 8000: cambiar sólo esa variable no cambia Uvicorn.
6. Establezca la ruta de salud `/ready`. Mantenga una instancia inicial y dimensione después de medir memoria y latencia. Elija el plan según los recursos necesarios; este manual no presupone gratuidad.
7. Publique manualmente el commit revisado. Conserve logs de build, revisión desplegada y URL asignada realmente por el proveedor; no utilice una URL inventada como evidencia.
8. Compruebe `https://SU-URL/`, `/health`, `/ready` y `/docs`. Ejecute `python -m scripts.smoke --base-url https://SU-URL --output evidence/cloud-http.json`.
9. Compruebe también la interfaz en navegador y verifique que el JSON muestre versión y umbral esperados. Registre resultados y fecha.
10. Mantenga el despliegue automático desactivado hasta definir promoción y reversión. Antes de datos reales, restrinja el acceso mediante mecanismos del proveedor y establezca límites de tráfico. Esta API no incorpora autenticación de usuarios y sólo debe usarse como demostración con textos de prueba.

`render.yaml` en la raíz del repositorio ofrece la configuración equivalente mediante Blueprint. Revise plan y rama antes de aplicarlo. Su existencia no acredita que el servicio haya sido publicado.

### Alternativa en AWS Elastic Beanstalk

1. Seleccione una región y cree una aplicación en Elastic Beanstalk.
2. Cree un entorno web con plataforma **Docker** compatible con la documentación vigente del proveedor. No mezcle esta ruta con la plataforma Python nativa del ejemplo.
3. Prepare un ZIP cuyo nivel superior contenga `Dockerfile`, `requirements.txt`, `.dockerignore`, `app/` y `models/`. No incluya una carpeta contenedora `Fase2/`, el Compose local ni datos de entrenamiento.
4. Suba el paquete como versión identificada por commit. El Dockerfile expone 8000 y el proxy del entorno debe dirigir solicitudes a ese puerto.
5. Configure roles, red y seguridad requeridos por su cuenta, healthcheck `/ready` y registros. Dimensione la instancia inicialmente para el prototipo.
6. Despliegue, capture el endpoint real y repita las pruebas HTTP y de navegador. Configure HTTPS antes de operar con datos reales.
7. Finalizada la demostración, cierre el entorno si no se utilizará y revise los recursos asociados para evitar consumo innecesario.

Esta alternativa es un procedimiento preparado; debe validarse en la cuenta elegida. El `Procfile` de una plataforma Python nativa no inicia un servicio Docker: en nuestra estrategia gobierna `CMD`.

## 10 Datos y modelo

Entrada: JSON con texto de 1 a 4,000 caracteres e idioma declarado `en` o `es`. Sólo `en` permite inferencia; `es` deriva a revisión mediante error controlado. No existe detector automático de idioma. La limpieza por expresiones regulares no garantiza anonimización integral.

Salida: clase, ruta, puntuación financiera, umbral, versión, revisión humana, referencia y latencia del procesamiento. No se persisten tickets ni predicciones en una base de datos; los errores de validación no devuelven el texto original. Los logs de acceso Uvicorn están desactivados. Los registros del proxy cloud requieren configuración y política de retención independiente.

La clase positiva comprende INVOICE, PAYMENT, REFUND y CANCEL. `cancel_order` pertenece a ORDER y no se convierte automáticamente en positivo. Cero FN en el benchmark no equivale a riesgo cero. Una puntuación elevada no autoriza transacciones.

## 11 Monitoreo mantenimiento y reversión

Compruebe disponibilidad con `/ready`. Registre por separado tiempos HTTP completos y tiempo interno de inferencia; no confunda las latencias de Colab con rendimiento de producción. Los identificadores de solicitud ayudan al seguimiento, sin guardar texto personal.

Para un piloto, proponga seguimiento de errores 5xx, latencia p95, memoria, cobertura, entradas rechazadas, prevalencia y calidad con etiquetas humanas. Los umbrales operativos deben calibrarse con datos reales; no se implementa una plataforma de monitoreo completa en esta entrega.

Si falla el arranque, revise logs, existencia del modelo, SHA-256 y versión de scikit-learn. Si hay un incidente de calidad, derive a soporte humano y suspenda el uso de rutas automáticas. No baje el umbral durante un incidente sin nueva validación.

Para actualizar, genere un paquete con nuevo modelo, metadatos, umbral y evidencia; ejecute pruebas sobre una rama y promueva un commit identificado. Para revertir, vuelva al commit y paquete anterior en PaaS o ejecute la imagen anterior identificada por digest. Verifique `/ready` y las solicitudes de prueba antes de restablecer el servicio.

## 12 Riesgos y uso responsable

El dataset es sintético y en inglés; el test histórico ya fue observado y puede contener familias de paráfrasis relacionadas. No se acredita validez externa en español ni impacto económico. El modelo conserva supervisión humana y no sustituye políticas de soporte.

Antes de un piloto real: consentimiento o fundamento aplicable para uso de datos, minimización, anonimización revisada, acceso controlado y evaluación por idioma y tipo de solicitud. La configuración pública de demostración no se declara lista para producción con datos sensibles.

## 13 Documentación asistida por IA y Copilot

La asistencia utilizada en esta elaboración es ChatGPT/Codex para código, revisión y redacción, con comprobaciones mediante scripts y pruebas. No se afirma haber ejecutado Microsoft Copilot. Los siguientes prompts están preparados para reproducir una revisión con esa herramienta si se desea.

**Prompt de arquitectura:** «Actúa como revisor técnico. Con base exclusivamente en app/main.py, app/inference.py, Dockerfile y models/metadata.json, describe la arquitectura de AI-SupportAssist. Distingue lo implementado de lo propuesto. No atribuyas RAG, autenticación o monitoreo inexistentes. Usa ISO/IEC 23053:2022 como referencia conceptual, sin afirmar certificación.»

**Prompt de manual:** «Genera una guía numerada para ejecutar este proyecto en Windows y Docker Compose, y preparar un servicio Docker en PaaS. Respeta el puerto 8000, la ruta Fase2, el umbral 0.24 y los nombres reales. No inventes URLs, resultados de construcción ni despliegues.»

**Prompt de auditoría:** «Compara el manual con el código y los archivos de evidencia. Enumera inconsistencias de dependencias, puertos, modelo y estados. Señala comandos que no correspondan a la plataforma elegida y distingue resultados esperados de ejecutados.»

Registre herramienta, fecha, versión si está disponible, prompt, archivos aportados, fragmento de respuesta, correcciones y verificación humana. No cargue secretos ni tickets personales. La salida de una herramienta generativa no sustituye una prueba técnica.

## 14 Trazabilidad referencias y glosario

`models/metadata.json` vincula modelo, fuente, particiones, código y entorno con SHA-256. `evidence/model_reconstruction.json` conserva la nueva reproducción de actividad 6. Git identifica las revisiones de la aplicación; los runs de Actions relacionan commit, build y pruebas. Consulte también `VERIFICACION_EJEMPLOS.md` y `REFERENCIAS.md`.

**Imagen:** paquete construido a partir de Dockerfile. **Contenedor:** instancia ejecutable de una imagen. **API:** contrato de comunicación. **Endpoint:** ruta y operación de la API. **PaaS:** plataforma administrada para ejecutar servicios. **Inferencia:** uso del estimador ya entrenado. **Readiness:** capacidad actual del servicio para atender solicitudes. **Rollback:** retorno a una versión anterior identificada.
