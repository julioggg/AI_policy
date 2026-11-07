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