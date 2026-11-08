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
