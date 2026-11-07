# AI Policy in Higher Education — Computational Revision

Revisión metodológica y computacional de **Mapping the Global Knowledge Structure and Full-Text Semantic Architecture of AI Policy Research in Higher Education** (Frontiers in Education).

Este repositorio contiene **código y reportes derivados no sensibles**. Los corpus PDF, los textos completos, embeddings y archivos grandes permanecen en CEDIA, en el directorio original del proyecto. La revisión computacional no debe modificar ni sobrescribir archivos originales.

## Fase 1: auditoría de procedencia (primero ejecutar)

Desde una terminal de CEDIA / Singularity:

~~~bash
cd "$HOME"
git clone https://github.com/julioggg/AI_policy.git
cd AI_policy
python scripts/01_audit_cedia.py --project "$HOME/ai_policy_he" --out reports/phase01
git status --short
git add reports/phase01
git commit -m "Audit: initial CEDIA project provenance and model inventory"
git push origin main
~~~

Si el repositorio ya existe en CEDIA, usar **git pull --ff-only** desde "$HOME/AI_policy" en vez de clonarlo de nuevo.

Si Git solicita autenticación para el push, utilizar un método autorizado para GitHub (por ejemplo, clave SSH configurada), **sin pegar tokens en scripts o mensajes**.

El auditor produce:
- reports/phase01/inventory.json: directorios, nombres/tamaños y esquemas de archivos relevantes, sin contenido de documentos;
- reports/phase01/summary.md: síntesis de rastros de las etapas de selección y de disponibilidad de métricas;
- reports/phase01/method_signals.json: rutas de scripts y señales de métodos/hiperparámetros, sin copiar código fuente potencialmente sensible.

Se ejecuta en **solo lectura respecto al proyecto**; los informes se escriben exclusivamente en el repositorio especificado por --out.

## Preguntas a resolver a partir de la auditoría

1. Reconstruir, con archivos originales y reglas efectivamente ejecutadas, los tamaños: 199366 > 102822 > 22524 > 21676 > 10283 > 10265.
2. Conciliar 5000 candidatos de texto completo, 3656 PDF descargados y 3655 textos extraídos utilizables; identificar denominadores realmente usados en KMeans.
3. Documentar OpenAlex (fecha, endpoint, filtros, deduplicación, selección), inclusión y exclusión, y clasificación automatizada.
4. Validar clasificaciones frente a muestra estratificada evaluada por dos personas, con métricas apropiadas.
5. Comparar KMeans k=12,18,25: seeds, estabilidad, silhouette, Davies–Bouldin, Calinski–Harabasz y coherencia/interpretabilidad.
6. Representatividad del corpus full-text y sensibilidad por tipo de publicación (solo peer-reviewed vs conjunto total), sin confundir repositorios con calidad editorial.
7. Comparación de la arquitectura semántica obtenida a partir del texto completo frente a títulos/resúmenes bajo una muestra común.

No se asume que los procesos anteriores se hayan ejecutado: se verificarán mediante evidencias y, solo entonces, se introducirán scripts para las pruebas faltantes.

## Política de datos

**No hacer** \`git add -A\` desde la carpeta original ni cargar directamente PDF, datos de texto completo, embeddings, archivos .env, credenciales o paquetes ZIP/TAR. El repositorio es público. Confirmar licencias y consentimiento antes de publicar metadatos a nivel documento. Los informes automáticos omiten textos, títulos, resúmenes, correos, DOI, identificadores de documentos y valores potencialmente privados.

La carpeta de trabajo que se versiona es "$HOME/AI_policy". El corpus permanece en "$HOME/ai_policy_he".

## Estado

Fase 1: código de inspección disponible; pendiente ejecución en CEDIA y evaluación de resultados.

## Fase 2: reconciliación de corpus y evaluación de representatividad

Una vez publicada la fase 1, ejecutar desde CEDIA:

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/02_provenance_and_bias.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase02
git add reports/phase02
git diff --cached --quiet || git commit -m "Phase 2: corpus provenance and representativeness"
git push origin main
~~~

Dependencias: Python 3.9+, pandas, numpy y pyarrow. Se utilizan las bases Parquet y los embeddings existentes (lectura), sin reinstanciar los modelos de lenguaje ni descargar PDF.

Salidas: reports/phase02/summary.md y reports/phase02/provenance_bias.json. Se comparten únicamente frecuencias agregadas, distancias descriptivas y metadatos de arrays, nunca registros individuales. Las diferencias de distribución NO constituyen estimaciones causales ni pruebas de calidad del contenido.


## Corrección fase 2 + Fase 3: estabilidad semántica, sin volver a descargar textos

El cribado original utiliza los valores \`include_core\`, \`include_policy\`, \`include_context\` y \`exclude\`. La primera versión de fase 2 no reconocía los tres primeros para la comparación de muestras, por lo que fue corregida.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only

python scripts/02_provenance_and_bias.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase02

python scripts/03_kmeans_robustness.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase03 \
  --seeds 5 --subsamples 5 --fraction 0.8 --n-init 10 --threads 8

git add reports/phase02 reports/phase03
git diff --cached --quiet || git commit -m "Phase 2 corrected and Phase 3 KMeans robustness"
git push origin main
~~~

La fase 3 realiza nuevos **ajustes de KMeans sobre los embeddings previamente guardados**, para k=12/18/25 con cinco semillas y cinco remuestreos cada uno. Reporta ARI/NMI, dispersión entre semillas, silhouette coseno muestral, Davies–Bouldin, Calinski–Harabasz y sensibilidad al excluir registros marcados como no aceptados o sin longitud de texto. Los valores por defecto están pensados como primera sensibilidad; se pueden aumentar semillas/remuestreos después de revisar los resultados. No se escribe ninguna modificación al corpus original.

Advertencias: la alineación exacta entre la matriz .npy y las filas de la base se presume conforme al pipeline original y se comprueba indirectamente; los índices no identifican publicaciones. La coherencia sustantiva de las etiquetas temáticas requiere validación humana. Las métricas no prueban por sí solas que k=18 sea una estructura natural.


## Fases 4 y 5: sensibilidad por fuente y preparación de validación humana

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only

python scripts/04_source_topic_sensitivity.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase04

python scripts/05_prepare_human_validation.py \
  --project "$HOME/ai_policy_he" \
  --private-out "$HOME/ai_policy_validation_private" \
  --public-out reports/phase05

git add reports/phase04 reports/phase05
git diff --cached --quiet || git commit -m "Phases 4-5: source sensitivity and blinded validation sampling"
git push origin main
~~~

**Fase 4** evalúa distribuciones de disciplinas, dimensiones políticas y clústeres k=12,18,25 entre corpus total, subconjunto de revistas (solo proxy de revisión por pares), textos completos y subconjunto elegible sin exclusiones ni textos vacíos. Entrega tablas agregadas, distancias TV y divergencia Jensen–Shannon, sin exportar registros.

**Fase 5** prepara hojas de codificación independientes para dos revisores: el material con títulos, resúmenes y OpenAlex ID permanece exclusivamente en la carpeta privada fuera del repositorio, situada en $HOME/ai_policy_validation_private. Solo los conteos de muestreo se versionan en GitHub. No afirmar que se ha realizado validación humana hasta que ambos revisores hayan codificado de verdad. El protocolo está en docs/human_validation_protocol.md.


## Fase 6: procedencia OpenAlex y reconciliación de denominadores

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/06_trace_and_reconcile.py
python scripts/06_trace_and_reconcile.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase06

git add reports/phase06
git diff --cached --quiet || git commit -m "Phase 6: reconcile OpenAlex stages and PDF extraction"
git push origin main
~~~

Esta fase contrasta los identificadores únicos y DOI entre captura original y corpus deduplicado; investiga los 786 IDs no retenidos, recoge las fechas de recuperación, lista únicamente cadenas de consulta simples verificadas como no sensibles y compara los manifiestos de 5000 intentos, descargas exitosas y extracciones. También confirma los ocho registros no elegibles y registra una aproximación (por DOI) de la selección de los 5000 documentos.

Los resultados son descriptivos; un DOI coincidente no prueba un algoritmo de deduplicación y la presencia de 5000 registros en un manifiesto no justifica por sí misma el criterio de prioridad. Es indispensable cotejar los scripts originales antes de afirmar que está reconstruido el protocolo sistemático. El proyecto original permanece inalterado.
