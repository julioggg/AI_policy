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


## Fase 7 — Reglas originales y colisiones PDF

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/07_original_rules_and_collisions.py
python scripts/07_original_rules_and_collisions.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase07
git add reports/phase07
git diff --cached --quiet || git commit -m "Phase 7: original filter rules and PDF collisions"
git push origin main
~~~

Esta fase inspecciona nombres de operaciones y parámetros permitidos de los scripts originales mediante AST, sin copiar el código; compara los 786 registros excluidos, audita la ruta PDF duplicada, y separa 3644 aceptaciones explícitas, cuatro decisiones dudosas y ocho exclusiones. Requiere pandas y pyarrow.

## Fase 8 — Comparación pareada de representaciones semánticas

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/08_abstract_fulltext_comparison.py
python scripts/08_abstract_fulltext_comparison.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase08 \
  --private-cache "$HOME/ai_policy_comparison_private" \
  --threads 8 --batch-size 64
git add reports/phase08
git diff --cached --quiet || git commit -m "Phase 8: abstract vs fulltext semantic comparison"
git push origin main
~~~

La fase 8 reutiliza embeddings de texto completo y codifica títulos y resúmenes en CEDIA, en modo sin conexión con el mismo modelo MiniLM. Valida primero la alineación de una muestra del campo topic_text; si la verificación falla o no se encuentra el modelo en la caché local, deja un informe bloqueado sin asumir comparabilidad. Si pasa, calcula concordancia entre particiones k=12, 18 y 25, silhouettes de coseno y contraste exploratorio de etiquetas automáticas.

Las etiquetas policy_dimension y disciplinary_area no son ground truth independiente. Los resultados no sustituyen codificación humana ni prueban superioridad de una modalidad.

El caché de embeddings recién calculados se guarda fuera del repositorio público en $HOME/ai_policy_comparison_private. Solo informes agregados van a GitHub. Requiere numpy, pandas, pyarrow, scikit-learn, sentence-transformers y torch, preferentemente del mismo entorno usado en el proyecto original.


## Fase 8b: comparación con ambos arrays originales (sin SentenceTransformer)

El intento de la fase 8 quedó bloqueado (`blocked_missing_offline_model`) porque el entorno no pudo cargar el modelo. En vez de instalar o redescargar MiniLM, fase 8b utiliza exclusivamente estas dos matrices ya existentes en CEDIA:

- `data/processed/embeddings_core_50k_minilm.npy` (matriz del corpus core/short-text; fuente exacta a verificar en script 03 original).
- `data/processed/fulltext_topic_embeddings_minilm.npy` (matriz del corpus fulltext).

El script enlaza por OpenAlex ID y restringe el análisis a registros explícitamente aceptados y con resúmenes disponibles. Antes de calcular los clústeres pareados, exige una señal de correspondencia entre similitudes emparejadas y una permutación aleatoria; si es inconclusa, no fuerza el análisis. Mantiene la distinción entre datos reutilizados y evidencia independiente. No se exportan identificadores, títulos, textos, embeddings ni resultados por documento.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/08b_reuse_original_embeddings.py
python scripts/08b_reuse_original_embeddings.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase08b \
  --threads 8
git add reports/phase08b
git diff --cached --quiet || git commit -m "Phase 8b: paired original embeddings without model loading"
git push origin main
~~~

Interpretación: el par de matrices solo constituye una comparación realmente *título/resumen frente a texto completo* si se verifica en los scripts originales que la matriz core fue codificada a partir de esas unidades de texto. Por defecto se etiqueta con precisión como *core/short-text baseline vs fulltext*. Las etiquetas automáticas y los cambios en clústeres no son validación humana.


## Fase 9 — Forensia de embeddings: comprobar si el texto completo realmente alimenta el modelo

Ante la similitud coseno mediana de 1.000 entre representaciones original core y full-text de las mismas 3644 publicaciones, es imprescindible distinguir embeddings numéricamente idénticos de vectores diferentes con dirección similar. También hay que documentar cuánto texto realmente llega a topic_text, su semejanza con título/resumen y los nombres de las columnas utilizadas por los scripts originales. La fase 9 hace esta auditoría sin recalcular embeddings.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/09_embedding_provenance_forensics.py
python scripts/09_embedding_provenance_forensics.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase09
git add reports/phase09
git diff --cached --quiet || git commit -m "Phase 9: audit numerical embedding identity and source texts"
git push origin main
~~~

Salidas: reports/phase09/summary.md y reports/phase09/embedding_forensics.json. Contienen únicamente estadísticos agregados sobre igualdad numérica de vectores, similitudes, distancias, longitudes de los campos de texto, concordancia de prefijos y señales estáticas de código original. No exportan textos, nombres de artículos, identificadores ni vectores.

Precaución metodológica: un resultado coseno próximo a 1 no prueba que la entrada fuera idéntica; no atribuir truncamiento ni ausencia de contenido completo sin cotejar las reglas de construcción de topic_text, la codificación y el max_seq_length del modelo original.


## Fase 10 — Comprobar límites reales de tokenización y localizar MiniLM offline

El resultado 2502/3644 vectores exactamente iguales (fase09) exige verificar la fuente de los vectores y el truncamiento por tokens antes de atribuir información novedosa al análisis de texto completo. Esta fase no recalcula embeddings y solo busca indicios de configuración en código, paquete/modelo/tokenizador local y coincidencia de prefijos; evita publicar texto de documentos o ubicaciones privadas.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/10_tokenizer_environment_audit.py
python scripts/10_tokenizer_environment_audit.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase10
git add reports/phase10
git diff --cached --quiet || git commit -m "Phase 10: tokenizer truncation and offline model environment"
git push origin main
~~~

Los resultados de Python/paquetes del contenedor actual no prueban la inexistencia de un modelo en otro ambiente Singularity, conda o venv. Tampoco hay que afirmar que el modelo truncó el PDF sin comprobar la secuencia entrada -> tokenizador -> max_seq_length -> embedding. El script indica si encuentra un tokenizador ya instalado sin descargar nada.


## Fase 11 — Preflight del entorno virtual original y presupuesto real de MiniLM

La fase 10 detectó $HOME/ai_policy_he/.venv y un directorio de caché de Hugging Face para all-MiniLM-L6-v2, pero el Python general de Singularity no tenía torch/transformers. Este preflight ejecuta un proceso aislado con el Python del .venv original, fuerza HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE, comprueba imports y modelo, mide model.max_seq_length y el recuento de tokens de una muestra fija de hasta 120 registros aceptados. No reentrena ni genera embeddings, y no exporta documentos.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/11_original_venv_tokenizer_preflight.py
python scripts/11_original_venv_tokenizer_preflight.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase11
git add reports/phase11
git diff --cached --quiet || git commit -m "Phase 11: offline MiniLM model and tokenizer preflight"
git push origin main
~~~

Un marcador de caché en disco no garantiza que el modelo esté completo; el script informa explícitamente si se puede cargar. El modelo funciona en CPU solo durante la inspección de tokens. Los resultados ayudarán a escoger entre reconstrucción de embeddings por fragmentos y alternativas. No afirmar que el texto fue tokenizado por completo sin verificar model.max_seq_length y el procedimiento original.


## Fase 12 — PILOTO de embeddings del cuerpo con chunks, sin truncamiento al encabezado

La fase 11 demostró que el modelo original MiniLM tiene max_seq_length=256 tokens. En la muestra de 120, las 120 secuencias topic_text tenían más de 256 tokens (mediana 2997); el cuerpo de PDF alcanzaba mediana 6041. La codificación directa de un texto largo con SentenceTransformer no captura todo su contenido. Fase12 es una prueba exploratoria pareada, todavía NO una revisión final del corpus completo.

Se toma una muestra determinista estratificada por dimensión política de hasta 240 publicaciones aceptadas explícitamente, se carga MiniLM solo desde la caché local y se produce una representación de cuerpo excluyendo los primeros 512 tokens del PDF y el 15% final; en medio se seleccionan uniformemente hasta 12 chunks de 192 tokens con 32 de solape. Se genera por separado embedding título+resumen; la agregación del cuerpo es promedio normalizado de chunks; el híbrido es combinación 50/50 normalizada. Se compara con el embedding original del supuesto fulltext, sin reemplazarlo. Se reportan similitudes, cambios en vecinos próximos, ARI/NMI y silhouette k12/18/25. No hay etiquetas humanas independientes todavía; estas son pruebas diagnósticas, NO verificación de utilidad/precisión semántica.

Se emplea el Python original del proyecto, donde el modelo local está disponible. El script escribe vectores y estado de reanudación SOLO bajo $HOME/ai_policy_chunk_private (fuera del repositorio público). En GitHub se envían exclusivamente estadísticas agregadas.

~~~bash
set -e
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/12_body_chunks_pilot.py
"$HOME/ai_policy_he/.venv/bin/python" scripts/12_body_chunks_pilot.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase12 \
  --private-cache "$HOME/ai_policy_chunk_private" \
  --sample-size 240 --max-chunks 12 --threads 8 --batch-size 32
git add reports/phase12
git diff --cached --quiet || git commit -m "Phase 12: private body-chunk pilot and aggregate diagnostics"
git push origin main
~~~

La selección y los vectores pueden reanudarse si se interrumpe el proceso, siempre que no cambien los parámetros ni los datos. No subir $HOME/ai_policy_chunk_private a GitHub. Comprobar los informes de fase12 antes de decidir qué pipeline final ejecutar sobre todos los documentos.


## Fase 13 — Representación cuerpo por fragmentos para todo el corpus elegible

La fase 12 (n=240) mostró un cambio semántico real: similaridad coseno mediana entre bibliografía y cuerpo 0.82669 frente a 1.00000 entre bibliografía y vector original, con silhouette (k18) de 0.10544 para chunks, 0.09303 para híbrido, 0.06156 original y 0.04903 bibliográfico. Pero hubo clústeres pequeños y la muestra no constituye validación independiente. No declarar calidad superior todavía.

Esta fase toma los **3644 documentos aceptados explícitamente**, excluye las cuatro decisiones `unclear_fulltext` y las ocho exclusiones, y utiliza el `.venv` MiniLM original en modo offline para construir matrices nuevas SOLO PRIVADAS. El documento se representa mediante promedio normalizado de hasta 12 fragmentos de 192 WordPiece con 32 tokens de solape; se omiten los primeros 512 tokens y el 15% final. El texto disponible procede del campo `full_text` y está limitado en la extracción original; no afirmar cobertura de toda la publicación. El vector bibliográfico se codifica por separado a partir de título+resumen. El script compara preliminarmente ambas representaciones mediante coseno, pero deja las pruebas comparativas kmeans y robustez para una fase posterior.

~~~bash
set -e
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/13_full_corpus_body_chunks.py
"$HOME/ai_policy_he/.venv/bin/python" scripts/13_full_corpus_body_chunks.py \
  --project "$HOME/ai_policy_he" \
  --out reports/phase13 \
  --private-cache "$HOME/ai_policy_chunks_full_private" \
  --threads 8 --batch-size 32
git add reports/phase13
git diff --cached --quiet || git commit -m "Phase 13: full-corpus private chunk embeddings"
git push origin main
~~~

El proceso guarda los vectores y checkpoints en `$HOME/ai_policy_chunks_full_private`, que NUNCA debe añadirse a GitHub. Si la sesión CEDIA termina antes de finalizar, el mismo comando reanuda los documentos pendientes sin sobrescribir los vectores originales. Si necesita una ejecución parcial controlada, agregue `--max-new-docs 400` y repita posteriormente para completar. El informe público muestra el estado como `partial_resumable` mientras queden documentos pendientes y `completed_vectors_private` al terminar.


## Fase 14 — Comparación completa y robustez de los nuevos agrupamientos

La fase 13 terminó con 3644 aceptaciones explícitas, 3629 embeddings de cuerpo utilizables y 15 documentos sin cuerpo suficiente tras aplicar los límites (primeros 512 tokens descartados, 15% final descartado, mínimo un chunk de 192). No deben confundirse los 3644 casos aceptados por cribado automático con los 3629 pares utilizables en este análisis. La similitud coseno mediana entre el nuevo embedding bibliográfico y el del cuerpo es 0.82397.

El script de fase14 compara **exactamente los mismos 3629 documentos** en cuatro representaciones: bibliografía (nuevo título+resumen), fulltext original truncado, body-only chunks, híbrido L2 de bibliografía+cuerpo. Verifica por SHA-256 privado la procedencia y el orden de documentos del caché de fase13 (el hash no se publica), y que las filas del Parquet original y del archivo KMeans correspondan. Genera para k=12/18/25 silhouette coseno en una muestra idéntica y fija, Davies–Bouldin, Calinski–Harabasz, ARI/NMI de 3 semillas, ARI de 3 subconjuntos de 80%, tamaño de los clústeres, concordancia con etiquetas originales y AMI exploratorio contra variables clasificadas automáticamente. Conserva los arrays de etiquetas por documento únicamente en una carpeta privada separada de GitHub. Estos indicadores NO sustituyen evaluación humana ni demuestran validez/política de los tópicos.

~~~bash
set -e
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/14_compare_full_corpus_kmeans.py
python scripts/14_compare_full_corpus_kmeans.py \
  --project "$HOME/ai_policy_he" \
  --private-cache "$HOME/ai_policy_chunks_full_private" \
  --private-labels "$HOME/ai_policy_cluster_labels_private" \
  --phase13-report reports/phase13/full_corpus_chunk_encoding.json \
  --out reports/phase14 \
  --seeds 3 --subsamples 3 --fraction 0.8 --n-init 10 --threads 8
git add reports/phase14
git diff --cached --quiet || git commit -m "Phase 14: full-corpus KMeans multi-seed robustness comparison"
git push origin main
~~~

Los reportes de fase14 contienen solo resultados agregados, y todas las etiquetas derivadas de los nuevos modelos permanecen en `$HOME/ai_policy_cluster_labels_private`. Este script NO vuelve a cargar MiniLM, procesar PDFs ni calcular embeddings; se ejecuta con el Python científico de Singularity. No sustituye automáticamente los k=18 anteriores del manuscrito.


## Fase 15 — Preparación privada de validación humana e interpretabilidad de tópicos

**Motivación de resultados de fase 14:** el cuerpo con k=12 tiene silhouette de coseno 0.116005, ARI mediano entre semillas 0.69458 y mínimo por clúster 47; cuerpo con k=18 tiene silhouette 0.100827, estabilidad mediana ARI 0.54807 y mínimo 44; híbrido 50/50 con k=18 tiene silhouette 0.076961, estabilidad ARI 0.63437 y mínimo 63. Ninguna métrica comprueba que los tópicos representen políticas de IA en educación superior. Las métricas de concordancia con etiquetas políticas automáticas son menores para cuerpo por chunks; se requieren revisores humanos.

El programa prepara tres particiones candidatas, **sin elegir una ganadora**: body_chunks k12, body_chunks k18 y hybrid_equal k18. Comprueba la huella privada de origen (fase13) y el manifiesto de etiquetas (fase14), toma siete ejemplos por tema (3 cerca del centroide, 3 aleatorios, 1 periférico) y crea 48 grupos ciegos que no revelan modalidad ni k. Produce dos juegos independientes de planillas CSV, cada uno con 48 temas y 336 filas de evaluación de documentos, además de una clave privada. Los textos solo están en CEDIA; el repositorio público recibe un informe de conteos. El documento docs/topic_validation_codebook.md define los criterios y el proceso de adjudicación.

~~~bash
set -e
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/15_prepare_blinded_topic_review.py
python scripts/15_prepare_blinded_topic_review.py \
  --project "$HOME/ai_policy_he" \
  --phase13-cache "$HOME/ai_policy_chunks_full_private" \
  --phase14-labels "$HOME/ai_policy_cluster_labels_private" \
  --phase13-report reports/phase13/full_corpus_chunk_encoding.json \
  --private-out "$HOME/ai_policy_topic_validation_private" \
  --out reports/phase15
git add reports/phase15
git diff --cached --quiet || git commit -m "Phase 15: blinded topic review sample (aggregate only)"
git push origin main
~~~

Los resultados individuales, nombres, resúmenes, fragmentos de cuerpo y clave de códigos permanecen SOLO bajo `$HOME/ai_policy_topic_validation_private`, jamás en GitHub. Las hojas pueden abrirse con Excel/LibreOffice desde una copia local protegida. **No declarar validación humana hasta que dos evaluadores completen sus planillas independientes y se calculen concordancia y adjudicación.**


## Fase 16 — Integridad de planillas y análisis de concordancia humana

La fase 15 **solo preparó** 48 grupos temáticos ciegos, con siete publicaciones cada uno, que representan tres estructuras candidatas: cuerpo k12, cuerpo k18 e híbrido k18. Cada uno de los dos evaluadores tiene 336 filas de documentos y 48 filas temáticas por calificar. Esta fase NO genera evaluaciones ni permite declarar validación humana sin las planillas originales completadas por dos expertos independientes.

Los archivos viven bajo `$HOME/ai_policy_topic_validation_private` en CEDIA. Para revisarlos los investigadores deben descargar de manera segura una copia privada mediante un cliente SFTP/SSH autorizado, completar las planillas separadamente y devolverlas al mismo directorio protegido conservando los nombres y encabezados. Consultar `docs/topic_validation_codebook.md`. **Nunca publicar, adjuntar a una incidencia pública ni subir los CSV a GitHub.** No compartir la clave `private_sampling_key.csv` con los evaluadores.

~~~bash
set -e
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/16_score_human_topic_review.py
python scripts/16_score_human_topic_review.py \
  --private-in "$HOME/ai_policy_topic_validation_private" \
  --out reports/phase16
git add reports/phase16
git diff --cached --quiet || git commit -m "Phase 16: human rating readiness and aggregate agreement"
git push origin main
~~~

**Antes de las calificaciones** la salida esperada es `awaiting_independent_human_ratings`, con conteos de celdas completadas; no inventa kappa ni puntuaciones. **Cuando estén completas ambas planillas** produce resumen por modelo, medidas de concordancia de Cohen (binaria para pertenencia; ponderada cuadrática para ordinal), denominadores, desacuerdos y casos inciertos. Incluso entonces, sigue pendiente la adjudicación experta de etiquetas y conflictos. Este análisis es distinto de la validación del cribado de la fase 5. No utilizar la tabla como ranking automático definitivo de modelos.


## Fase 18 — Paquete privado de adjudicación ciega posterior a validación humana

**Fase 16 confirmada (2026-11-08 UTC):** dos evaluadores completaron 48/48 grupos y 336/336 documentos por persona. Concordancia de pertenencia documental exacta=91.667%, κ=.73370; pertinencia política documental exacta=47.619%, κ ponderado=.44784. Para las tres opciones evaluadas, coherencia media de ambos revisores: cuerpo k12=2.8333, cuerpo k18=3.5278, híbrido k18=3.4722. Diferenciación media: 2.125, 2.5 y 2.6389 respectivamente. Pertinencia política de grupo: 1.6667, 1.7778 y 1.6944. Estas son evaluaciones descriptivas sobre muestras de solo siete documentos por tema, con diseño no probabilístico de prototipos y periferia. No seleccionar el modelo por estas medias solamente.

La fase 18 crea un **ÚNICO Excel ciego privado para adjudicación humana** a partir de las cuatro planillas normalizadas de la fase 16 y del banco original de la fase 15, verificando que los textos no fueron alterados. El libro incluye INSTRUCCIONES, GRUPOS (48 grupos, con etiquetas y valoraciones separadas A/B y celdas para consenso), EJEMPLOS (336 textos para interpretar cada tema), DESACUERDOS (solo documentos en los que A y B difieren en pertenencia o pertinencia) y ESCALAS. La adjudicación NO es un nuevo juicio independiente; observa las calificaciones A/B pero no los modelos ni su k. El script nunca rellena consenso automáticamente.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/18_prepare_blinded_adjudication_excel.py
python scripts/18_prepare_blinded_adjudication_excel.py \
  --normalized-ratings "$HOME/ai_policy_calificaciones_normalizadas_privado" \
  --phase15-private "$HOME/ai_policy_topic_validation_private" \
  --private-out "$HOME/ai_policy_adjudicacion_privado" \
  --out reports/phase18
git add reports/phase18
git diff --cached --quiet || git commit -m "Phase 18: prepare model-blinded adjudication packet (aggregate only)"
git push origin main
~~~

El archivo privado `~/ai_policy_adjudicacion_privado/Adjudicacion_Ciega_Fase18.xlsx` debe descargarse mediante el mecanismo de transferencia privado del HPC, enviarse solo a la persona responsable de adjudicación, completarse exclusivamente en las columnas amarillas y guardarse en formato XLSX. **Nunca** cargar el Excel o los CSV de evaluadores en GitHub. `reports/phase18` solo incluye cantidades agregadas y el estado `adjudication_packet_prepared_human_consensus_pending`; no contiene decisiones humanas definitivas ni evidencia textual.


## Fase 19 — Validación segura del Excel de adjudicación completado

La fase 18 preparó, **pero no adjudicó**, 48 grupos, 336 ejemplos documentales y 189 casos documentales en disputa (28 de pertenencia, 176 de pertinencia, con solapamiento de 15). Fase 19 valida una **copia final** del Excel rellenada por un adjudicador humano. Comprueba que todas las filas, códigos, títulos, resúmenes, extractos y calificaciones independientes A/B sigan idénticos al archivo plantilla protegido; rechaza fórmulas, valores fuera de escala, filas editadas, grupos faltantes, archivos intercalados y hojas renombradas.

**Procedimiento de entrega:** descargar de la carpeta privada `~/ai_policy_adjudicacion_privado/Adjudicacion_Ciega_Fase18.xlsx`, compartir con la persona adjudicadora por medio privado. Debe completar para los 48 grupos las cinco celdas de consenso (nombre, coherencia, diferenciación, pertinencia y justificación) y para los 189 casos en DESACUERDOS tres celdas (pertenencia, pertinencia y justificación). Los 336 ejemplos de EJEMPLOS son de consulta, no deben cambiarse. La persona ve A/B pero no modelo/k. Devuelve el XLSX protegido y el coordinador lo sube a `~/ai_policy_adjudicacion_recibida_privado/Adjudicacion_Ciega_Fase18_COMPLETADA.xlsx` mediante la opción privada de carga de CEDIA (no dentro del checkout GitHub). Conservar la plantilla original intacta.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/19_analyze_completed_adjudication.py
python scripts/19_analyze_completed_adjudication.py \
  --original-xlsx "$HOME/ai_policy_adjudicacion_privado/Adjudicacion_Ciega_Fase18.xlsx" \
  --returned-xlsx "$HOME/ai_policy_adjudicacion_recibida_privado/Adjudicacion_Ciega_Fase18_COMPLETADA.xlsx" \
  --phase18-report reports/phase18/adjudication_preparation_aggregate.json \
  --normalized-ratings "$HOME/ai_policy_calificaciones_normalizadas_privado" \
  --out reports/phase19
git add reports/phase19
git diff --cached --quiet || git commit -m "Phase 19: private adjudication audit and aggregate-only comparison"
git push origin main
~~~

Si el Excel está incompleto, devuelve `awaiting_human_adjudication` y **NO** desvela ni publica resultados por modelo; solo agregados de completitud y validación. Una vez completo, vincula internamente las claves privadas con tres modelos (cuerpo k12, cuerpo k18, híbrido k18) para entregar medias temáticas consensuadas y proporciones documentales. Para documentos donde A y B ya coincidían conserva su calificación común y la distingue de los 189 adjudicados. Nunca modifica los kappas de fase16 ni presenta la adjudicación como un tercer evaluador ciego independiente. No selecciona modelo ganador automáticamente. No publicar el libro, grupo individual, claves ni textos.


## Phase 20 — Excel blind screening validation (Phase05 sample)

The original `reports/phase05` sample remains **unrated**, 368 records in six strata: 120 `include_core`, 80 `include_policy`, 40 `include_context`, all 18 `screen_exclude`, 80 `q1_not_article_ready` and 30 `core_not_q1`. These are NOT 368 random items from a single inclusion population; especially Q1 and core filter exclusions must not be conflated with final AI-screening negatives. For independent human classification, new `scripts/20_screening_reviewer_excel.py` creates two private Excel workbooks, with INSTRUCCIONES, CRIBADO (368 rows), ESCALAS; reviewers never see model labels or strata. The screening codebook remains `docs/human_validation_protocol.md`.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/20_screening_reviewer_excel.py
python scripts/20_screening_reviewer_excel.py \
  --mode export \
  --private-in "$HOME/ai_policy_validation_private" \
  --out-dir "$HOME/ai_policy_screening_excel_para_evaluadores_privado"
~~~

Transfer `Cribado_A.xlsx` to reviewer A and `Cribado_B.xlsx` to reviewer B **privately**. Each rates 368 records: 0/1/2/3/9 relevance, one discipline category, one primary policy dimension and a short explanation. Edit only yellow cells; preserve original titles, abstracts, sample codes, headers and row counts. No coding or HPC access is required. Sample key `sampling_key.csv` stays in CEDIA and is **never** shared with the researchers. Do not publicize article titles/abstracts or review judgments.

After the two annotated Excel workbooks are returned, upload them to `~/ai_policy_screening_excel_recibidos_privado` and execute:

~~~bash
cd "$HOME/AI_policy"
python scripts/20_screening_reviewer_excel.py \
  --mode import \
  --private-in "$HOME/ai_policy_validation_private" \
  --received-xlsx "$HOME/ai_policy_screening_excel_recibidos_privado/Cribado_A.xlsx" \
  --rater a \
  --out-dir "$HOME/ai_policy_screening_calificaciones_normalizadas_privado"
python scripts/20_screening_reviewer_excel.py \
  --mode import \
  --private-in "$HOME/ai_policy_validation_private" \
  --received-xlsx "$HOME/ai_policy_screening_excel_recibidos_privado/Cribado_B.xlsx" \
  --rater b \
  --out-dir "$HOME/ai_policy_screening_calificaciones_normalizadas_privado"
~~~

Phase20 import verifies exact sample IDs, evidence metadata, allowed categories and original reviewer identities; it preserves the original Phase05 private CSVs and key, while writing normalized responses into a different private folder. **It does NOT calculate kappa or classifier precision yet**: those will be implemented only after actual expert labels exist. The parent-universe metrics will require explicit stratum inclusion probabilities and eligibility logic; never claim naive 368/368 overall precision or recall.


## Phase21 — independent reviewer agreement for Phase05 screening

Once both returned private Phase20 Excel books are imported into `~/ai_policy_screening_calificaciones_normalizadas_privado` using `scripts/20_screening_reviewer_excel.py`, run:

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/21_score_human_screening.py \
  --private-in "$HOME/ai_policy_screening_calificaciones_normalizadas_privado" \
  --phase05-report reports/phase05/sample_aggregate.json \
  --out reports/phase21
git add reports/phase21
git diff --cached --quiet || git commit -m "Phase21: two-reviewer stratified screening agreement"
git push origin main
~~~

The script verifies the private correspondence IDs, immutable reviewed metadata, allowed categories, all six original sampling strata and completion. It publishes only aggregates. It reports unweighted and quadratic weighted Cohen kappa for relevance 0–3 excluding code 9, nominal kappas for discipline and principal policy dimension including `uncertain` as a class, and distributions with per-stratum denominators. It flags counts for human adjudication. It intentionally **does not** report machine screening precision/recall before human consensus, and never equates earlier bibliographic filter exclusions to classifier-negative cases. Original private CSVs, texts, IDs and keys must never be committed to GitHub. No AI-generated human assessments.


## Phase 22 — adjudicar discordancias en el cribado humano de 368 registros

Fase 21 procesó dos evaluaciones independientes completas (368/368 por revisor) y encontró **89 discordancias de relevancia**, **218 de disciplina** y **183 de dimensión principal de política**, cuya unión son **316 registros únicos**. Entre los 18 casos excluidos por la clasificación automatizada ambos anotadores calificaron los 18 como relevancia 0. El promedio de etiquetas de un estrato no prueba por sí solo que el clasificador sea erróneo. La concordancia sobre relevancia 0–3 excluye 17 pares con 9 incierto: κ sin ponderar=0.67334 y ponderado cuadrático=0.75365. Disciplina κ nominal=0.24698, política κ nominal=0.39749. El diseño estratificado obliga a no calcular precisión/recall global sin ponderación/inferencia válida.

### Preparar el Excel privado de adjudicación

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/22_prepare_screening_adjudication_excel.py \
  --private-in "$HOME/ai_policy_screening_calificaciones_normalizadas_privado" \
  --private-out "$HOME/ai_policy_screening_adjudicacion_privado" \
  --phase21-report reports/phase21/human_screening_agreement_aggregate.json \
  --out reports/phase22
git add reports/phase22
git diff --cached --quiet || git commit -m "Phase22: prepare human screening adjudication packet"
git push origin main
~~~

El Excel **privado** `~/ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx` contiene las pestañas INSTRUCCIONES, DISCREPANCIAS (solo los 316 registros discordantes con puntuaciones A/B y texto), TODOS (368 registros, solo consulta) y ESCALAS. La persona responsable completa **4 columnas amarillas** por cada caso en DISCREPANCIAS: relevancia final, disciplina final, dimensión política final, justificación. Permitir decisión distinta de A/B y valor 9 si realmente no hay evidencia. No editar identificadores, los datos científicos fuente, puntuaciones A/B, pestañas o encabezados. No subir el Excel a GitHub. Reconciliar estos dictámenes es adjudicación posterior, **no** una nueva evaluación independiente. Quedan 52 registros sin discrepancias a los que podrá asignarse el valor compartido de A/B en una fase posterior, explícitamente diferenciado de dictamen adjudicado.

El script solo publica conteos agregados en `reports/phase22`; no crea valores de consenso ni revela estratos, decisiones automáticas, códigos, textos o comentarios de artículos.


## Phase 23 — audit a completed private Phase22 human screening adjudication

The coordinator receives a **separate copy** of the 316-case Phase22 adjudication Excel: `Adjudicacion_Cribado_Fase22_COMPLETADA.xlsx`. Do not overwrite the original blank `~/ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx`; retain source two-rater CSVs unchanged. Upload privately to `~/ai_policy_screening_adjudicacion_recibida_privado/`, outside the GitHub checkout.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/23_analyze_adjudicated_screening.py \
  --original-xlsx "$HOME/ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx" \
  --returned-xlsx "$HOME/ai_policy_screening_adjudicacion_recibida_privado/Adjudicacion_Cribado_Fase22_COMPLETADA.xlsx" \
  --private-in "$HOME/ai_policy_screening_calificaciones_normalizadas_privado" \
  --phase05-report reports/phase05/sample_aggregate.json \
  --phase21-report reports/phase21/human_screening_agreement_aggregate.json \
  --phase22-report reports/phase22/screening_adjudication_packet_aggregate.json \
  --out reports/phase23
git add reports/phase23
git diff --cached --quiet || git commit -m "Phase23: audit adjudicated human screening (aggregate only)"
git push origin main
~~~

Phase23 conservatively validates the unchanged immutable title/abstract metadata, original A/B scores and justifications, matching sample IDs and stratum sampling key, and all four consensus fields for 316 discordant records. When the workbook is complete, it reports aggregate code distributions within each original stratum and **approximate, explicitly conditional design-weighted prevalence** for the four final AI-screening strata only, with finite-population sampling correction and uncertainty separated as code 9. The two earlier bibliographic exclusion strata stay distinct. It does **not** automatically claim binary precision, recall, corpus-level full-text accuracy, or independently verified gold standard.

**Methodological quality caution:** local pre-import audit of the delivered private file found all 1,264 required consensus cells filled, no invalid rubric codes, and unchanged source fields compared with uploaded original human workbooks. For the explicitly disputed dimensions, the adjudication matched reviewer B in 71/89 relevance cases, 212/218 discipline cases, 165/183 policy dimensions. This asymmetry does not prove bias or invalid human judgment; nevertheless, verify adjudicator process, written rationales and a risk-focused independent spot-check, especially of disciplines. Phase23 publishes these asymmetry counts but does not expose per-case details. The raw adjudication workbook must NOT be pushed to GitHub.


## Phase24 — genuine independent *blinded* quality control of Phase23 consensus

Phase23 has been completed and verified at `reports/phase23`, with all 316 discordant cases adjudicated and 52 A/B-unanimous cases retained. Conditional four-stratum, final-screening weighted proportions (N=10,283): code0=11.6375%, code1=50.7917%, code2 or3=35.7763% (including direct code3=3.7538%), code9=1.7945%. These are conditional title/abstract consensus proportions, **not** classifier accuracy or publication prevalences for the original much larger discovery universe. Specific concern: of 80 reviewed `screen_include_policy` cases, 59 were assigned code1, only 10 scored 2+, none 3. Adjudication QA alerts: preference for reviewer B in 212/218 discipline disagreements and 165/183 policy-dimension disagreements; only 153 distinct justification strings in 316 resolved rows, and 226 begin with a common relevance-agreement template. These patterns are not themselves proof of invalidity, but warrant an independent blinded quality spot-check before asserting validated screening.

`scripts/24_prepare_blinded_screening_qa.py` takes the **original and returned Phase22 Excel**, private Phase20 A/B sheets + key and the official Phase05/22/23 reports, re-verifies the 368 decisions, then creates a separate reproducible 80-item **risk-enriched** QA sample containing uncertain 9 cases, some B-selected disagreements in relevance/discipline/policy, some auto-`include_policy` consensus1 cases and direct policy3 cases, with a small random safety fill. The reviewer sees only the publication title, abstract, year, type and blank four-field coding rubric; no prior human label, machine label, stratum, case selection criterion, article ID or Phase05 original code. The correspondence is stored in a second PRIVATE CSV on CEDIA. This is **not** a probability sample and is not to be used to estimate accuracy or weighted prevalence.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/24_prepare_blinded_screening_qa.py \
  --original-xlsx "$HOME/ai_policy_screening_adjudicacion_privado/Adjudicacion_Cribado_Fase22.xlsx" \
  --completed-xlsx "$HOME/ai_policy_screening_adjudicacion_recibida_privado/Adjudicacion_Cribado_Fase22_COMPLETADA.xlsx" \
  --private-in "$HOME/ai_policy_screening_calificaciones_normalizadas_privado" \
  --private-out "$HOME/ai_policy_screening_qa_independent_privado" \
  --out reports/phase24
git add reports/phase24
git diff --cached --quiet || git commit -m "Phase24: blinded independent screening QA packet (counts only)"
git push origin main
~~~

Deliver ONLY `~/ai_policy_screening_qa_independent_privado/Control_Independiente_Cribado_Fase24.xlsx` to an independent expert who has **not** seen the Phase20 A/B or Phase22 consensus results. The expert must make all four judgments independently with specific explanations. Do NOT deliver `correspondencia_qa_privada.csv`, the previous A/B sheets, any code mapping or public report to that expert. The workbook and key must never be pushed to GitHub. No new judgment has been generated yet. If the independent QA disagrees systematically, return to the adjudication protocol and revise cautiously, preserving all earlier forms. Only after a documented QA decision should final screening conclusions be integrated into a manuscript.


## Phase 25 — independiente QA: pertinencia y disciplina + normalización transparente de categorías políticas

El archivo humano `Control_Independiente_Cribado_Fase24_Lleno.xlsx` recibió 80 evaluaciones con relevancia, disciplina y justificación completas. **El investigador utilizó cinco etiquetas no normalizadas para todas las 80 decisiones de política**: `Ninguna (Uso General)` (32), `Ética y Gobernanza` (21), `Ética y Plagio` (14), `Marco Político/Regulatorio` (11), `N/A` (2), ajenas al codebook oficial Phase24. NO traducir etiquetas arbitrariamente como si fueran decisiones humanas originales. Entre las 21 etiquetas `Ética y Gobernanza`, escoger por evidencia la dimensión PRINCIPAL (`ethics_integrity`, `governance_policy` u otra si procede).

La copia privada `Normalizacion_codigos_QA_Fase24_PENDIENTE.xlsx`, generada desde el archivo recibido, conserva 80 etiquetas originales y propone 59 equivalencias textuales: `Ninguna (Uso General) -> not_applicable` (32), `Ética y Plagio -> ethics_integrity` (14), `Marco Político/Regulatorio -> governance_policy` (11), `N/A -> not_applicable` (2), e incluye 21 campos finales en blanco para decisión humana. Los 59 campos propuestos son **normalización técnica post hoc, no nueva evaluación humana independiente**. Revisar y corregir si la publicación contradice la equivalencia. La versión completada debe tener 80/80 códigos oficiales, con los mismos datos originales.

`scripts/25_compare_independent_screening_qa.py` verifica la correspondencia privada de los 80 documentos Phase24 y la integridad de las calificaciones originales. Puede computar ya, sin normalización, la **concordancia descriptiva de relevancia y disciplina** en la muestra dirigida de calidad, dejando la concordancia de dimensión política como pendiente. Solo cuando se entregue una planilla de normalización completa calcula la concordancia sobre dimensión política **identificada expresamente como normalizada post hoc**. Ningún valor individual, título, resumen o código se exporta a GitHub.

Tras subir la versión original recibida de QA a una carpeta privada separada del repositorio de trabajo:

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/25_compare_independent_screening_qa.py \
  --qa-original-xlsx "$HOME/ai_policy_screening_qa_independent_privado/Control_Independiente_Cribado_Fase24.xlsx" \
  --qa-returned-xlsx "$HOME/ai_policy_screening_qa_recibida_privado/Control_Independiente_Cribado_Fase24_Lleno.xlsx" \
  --qa-private-key "$HOME/ai_policy_screening_qa_independent_privado/correspondencia_qa_privada.csv" \
  --phase24-report reports/phase24/quality_audit_packet_aggregate.json \
  --out reports/phase25
~~~

Una vez que esté completada y subida la normalización, repetir incorporando `--normalization-xlsx "$HOME/ai_policy_screening_qa_recibida_privado/Normalizacion_codigos_QA_Fase24_COMPLETA.xlsx"`. En ambos casos publicar solo `reports/phase25` y conservar los libros y claves privadas. El acuerdo QA no mide exactitud poblacional: la muestra de 80 fue intencionalmente enriquecida por incertidumbre, desacuerdos previos y conflictos de política. Si emergen desacuerdos importantes de relevancia o disciplina, analizar causas conceptuales y documentar una decisión independiente antes de declarar válida la adjudicación Phase23.


### Phase25 — corrected Phase24 reviewer file (after original response; strict provenance)

A later human-provided `Control_Independiente_Cribado_Fase24_Corregido.xlsx` was examined against the originally returned `Control_Independiente_Cribado_Fase24_Lleno.xlsx`: all **80** source codes, titles, abstracts, years, types, relevance ratings and discipline ratings remained unchanged; **all 80 policy labels and all 80 justifications changed**. The corrected policy labels use 34 `not_applicable`, 31 `ethics_integrity`, 12 `governance_policy`, and 3 `assessment`. In detail, the original 21 `Ética y Gobernanza` became `ethics_integrity`; the 14 original `Ética y Plagio` became 10 `ethics_integrity`, 3 `assessment`, 1 `governance_policy`. The 32 `Ninguna (Uso General)`, 11 `Marco Político/Regulatorio`, and 2 `N/A` became the natural official codebook counterparts. This is a **later revision**, NOT an additional independent reviewer.

A separate protected normalization book, `Normalizacion_codigos_QA_Fase24_COMPLETA.xlsx`, was generated preserving the **original** 80 QA evidence texts and QA responses; it fills official final codes from the corrected workbook, with explicit review provenance. The 59 initial technical-equivalence proposals included four overrulings in `Ética y Plagio`. In total 25 final codes differ from/extend the original technical proposals (21 ambiguous plus four overrulings). Never silently replace the independent original with the corrected QA workbook.

After uploading these three books privately into `~/ai_policy_screening_qa_recibida_privado` and **keeping** the original untouched, run:

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/25_compare_independent_screening_qa.py \
  --qa-original-xlsx "$HOME/ai_policy_screening_qa_independent_privado/Control_Independiente_Cribado_Fase24.xlsx" \
  --qa-returned-xlsx "$HOME/ai_policy_screening_qa_recibida_privado/Control_Independiente_Cribado_Fase24_Lleno.xlsx" \
  --qa-corrected-xlsx "$HOME/ai_policy_screening_qa_recibida_privado/Control_Independiente_Cribado_Fase24_Corregido.xlsx" \
  --normalization-xlsx "$HOME/ai_policy_screening_qa_recibida_privado/Normalizacion_codigos_QA_Fase24_COMPLETA.xlsx" \
  --qa-private-key "$HOME/ai_policy_screening_qa_independent_privado/correspondencia_qa_privada.csv" \
  --phase24-report reports/phase24/quality_audit_packet_aggregate.json \
  --out reports/phase25
git add reports/phase25
git diff --cached --quiet || git commit -m "Phase25: aggregate independent QA and corrected-codebook provenance"
git push origin main
~~~

The added `--qa-corrected-xlsx` argument verifies that no original relevance, discipline, source evidence or sample correspondence was altered by the later corrected workbook; it requires a complete separate normalization file with identical official policy codes and reports only aggregated counts of revisions. QA risk-selection is **not representative**; comparisons should not be interpreted as classifier accuracy. The assessor's procedure/independence cannot be established computationally. Synthetic end-to-end tests for this provenance check pass in CI.


## Phase26 — diagnostic methods reconciliation for significant Phase25 disagreement

**Important scientific stop rule:** Phase25 finished with integrity passed, but the risk-selected independent QA **does not corroborate** the Phase23 consensus in a defensible way. On the 80 risk-enriched cases, relevance exact agreement=33/80=41.25%, unweighted κ=0.31447 (n=67 excluding 13 consensus cases scored uncertain9), weighted quadratic κ=0.31315; discipline exact=22/80=27.5%, κ=0.13755; *posthoc* normalized policy exact=9/80=11.25%, κ=0.00647. This quality-audit result CANNOT be generalized to all 368 or 10,283 records: selection deliberately enriched risk. Original QA coded 32 cases direct3 vs only six direct3 in the earlier consensus, with 13 unresolved9 cases all assigned 0–3 by QA. These conflicts may stem from construct/codebook mismatch or low evidential specificity, not necessarily a uniquely correct rater. The posthoc normalized policy dimension is not independently assessed using the original codebook. **Do not present Phase23 design-weighted conditional estimates as definitive validated performance, or impute classifier precision/recall.**

To move forward without repeated full-corpus re-rating, `scripts/26_prepare_methodological_reconciliation.py` creates a *single private 80-case methods-panel dossier* containing the original A/B and adjudicated scores, the independent QA relevance/discipline, the explicitly posthoc normalized QA policy dimension, both earlier QA justifications, and four blank final panel fields. It rechecks the protected Phase22/23 consensus, Phase24 original QA, corrected QA and Phase25 public aggregate counts, and retains a strict distinction between evidence sources. Neither OpenAlex IDs, original Phase05 sample IDs, machine labels nor original stratum identity are shown in the panel workbook. Only aggregate counts are published to `reports/phase26`; all human decisions remain pending.

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/26_prepare_methodological_reconciliation.py \
  --private-out "$HOME/ai_policy_panel_conciliacion_fase26_privado" \
  --out reports/phase26
git add reports/phase26
git diff --cached --quiet || git commit -m "Phase26: prepare private methods reconciliation packet"
git push origin main
~~~

Deliver only the XLSX `~/ai_policy_panel_conciliacion_fase26_privado/Conciliacion_Metodologica_Fase26.xlsx` to a competent methods panel; do not share it publicly or with GitHub. It contains 80 rows and all original textual evidence and ratings with four yellow columns for new **documented panel decisions**. BEFORE resolving 80 items, agree on a precise rule distinguishing codes 1 (educational AI without demonstrable policy), 2 (defensible indirect policy implications) and 3 (policy itself is investigated); resolve direct-policy overcalling, handling of 9, interdisciplinarity and primary-policy hierarchy. Full-text escalation should be recorded for ambiguous cases; the panel need not replace all 368 original ratings unless a systematic codebook fault is identified. The file's consensus fields start empty; no human judgments are fabricated.


## Phase27 — completed methods panel (80 risk-selected cases): audit, not an independent gold standard

A returned private workbook named `Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx` was inspected before import. The 80 blinded QA codes are unique and all 80 rows have valid codes in the four panel fields (320/320), with 79 unique written rationales and a repeated `[R...]` rubric-style prefix in all 80 responses. These are **descriptive features**, not a procedural verification of independent human judgment. Relative to Phase23 consensus shown in the panel workbook, the latest panel retained relevance on 78/80 records (two 2→1 changes), discipline on 80/80 and main policy dimension on 79/80 (one `equity_access`→`teaching_learning` change). Against the original *independent* Phase24 QA, the panel's final classifications match on relevance 34/80, discipline 22/80, and later-normalized policy on 9/80. High agreement with previously visible consensus is not itself independent validation, even when rationales are filled. Risk-selected Phase24 QA was deliberately enriched for disagreement and cannot estimate overall population error rates.

`scripts/27_audit_panel_reconciliation.py` requires both the ORIGINAL, blank protected Phase26 panel dossier and the distinctly returned completed panel dossier; it compares all unchanged source fields cell by cell and validates both against Phase25/Phase26 published aggregate fingerprints. It checks the 80×4 human panel entries and emits only aggregate retention/change counts, completedness and methodological stop-rule caveats in `reports/phase27`. It NEVER overwrites Phase23 estimates, Phase24 QA, confidential article text or reviewer scores. It does not invent new gold-standard labels or claim precision/recall.

Upload the returned XLSX to the CEDIA working directory `~/AI_policy` from a local computer, then move it to a fresh private folder OUTSIDE GitHub and run:

~~~bash
cd "$HOME/AI_policy"
git pull --ff-only
PRIVATE="$HOME/ai_policy_panel_conciliacion_fase26_recibida_privado"
mkdir -p "$PRIVATE" && chmod 700 "$PRIVATE"
if [ -s "$HOME/AI_policy/Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx" ] && [ ! -e "$PRIVATE/Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx" ]; then
  mv "$HOME/AI_policy/Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx" "$PRIVATE/"
  chmod 600 "$PRIVATE/Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx"
fi
python scripts/27_audit_panel_reconciliation.py \
  --original-xlsx "$HOME/ai_policy_panel_conciliacion_fase26_privado/Conciliacion_Metodologica_Fase26.xlsx" \
  --returned-xlsx "$PRIVATE/Conciliacion_Metodologica_Fase26_COMPLETADA.xlsx" \
  --phase26-report reports/phase26/panel_reconciliation_preparation_aggregate.json \
  --phase25-report reports/phase25/independent_screening_qa_aggregate.json \
  --out reports/phase27
git add reports/phase27
git diff --cached --quiet || git commit -m "Phase27: audit completed methodological reconciliation (aggregate only)"
git push origin main
~~~

Expected Phase27 status if all inputs correspond: `completed_panel_reconciliation_reviewed_not_independently_validated`. The scientific decision remains whether to design a new blind, probability-sampled codebook validation or strictly report Phase23 preliminary screening strata and separately report the Phase24/26 disagreement/correction chain as limitations. Do not conceal poor independent agreement or treat 80 risk-enriched cases as representative. Before final manuscript inference, independently verify policy construct operationalization and, where necessary, full-text records scored 9.
