# Auditoría cruzada: dos revisores y trabajos HPC pendientes (08-11-2026)

**Fuente:** observaciones exactas entregadas por el investigador principal (Revisor 1: 13 observaciones principales; Revisor 2: 10 bloques) y resultados verificados en reports/phase01–phase34 del repositorio. **Límite:** no se ha verificado una versión corregida del manuscrito. Diferenciar resultados COMPUTADOS, procedimientos incompletos y cambios editoriales sin nuevas simulaciones.

## Conclusión ejecutiva

**Principal experimento computacional nuevo no ejecutado:** Fase35, diseño ponderado del contraste de la muestra de 1200 con etiquetas originales y referencia humana conciliada, con incertidumbre R9. El script scripts/35_screen_vs_expert_weighted.py está en GitHub y pasó pruebas sintéticas, pero no se ha ejecutado con los datos reales de CEDIA. Su modelo positivo "include" evalúa alcance universitario en el MARCO FINAL de 10283 registros, nunca sensibilidad de la búsqueda bibliográfica global de 199366. No equiparar include_policy con R3 ni con R2+.

**Principal peligro científico:** las fases 09/11 hallaron 2502 de 3644 vectores legacy fulltext EXACTAMENTE iguales a los vectores core; el modelo MiniLM tenía presupuesto de 256 tokens para inputs que frecuentemente tenían miles. Fases 13/14 corrigieron con fragmentos de cuerpo sobre 3629 casos utilizables. La versión revisada debe usar esa arquitectura realmente derivada del cuerpo, o reducir la afirmación de que el antiguo análisis comprendía la semántica del texto completo.

## Correspondencia con Revisor 1

| Observación | Estado técnico comprobado | Acción concreta |
|---|---|---|
| R1.1: búsqueda y PRISMA | PARCIAL: fases 02/06/07 reconstruyen conteos 199366→102822→22524→21676→10283→10265; captura fechada 2026-05-25 | Extraer argumentos API/filtros exactos, los 27 términos/capturas de los scripts originales y PRISMA; documentar Q1 real, 786 IDs ausentes en dedup, 848 y 11393 descartes previos |
| R1.2: frontera conceptual | PENDIENTE en texto: HE-AI general ≠ política directa | Definir S y R=1/2/3, decidir si título/objetivo debe ampliarse; no llamar "AI policy" a los 10265 como si todos trataran política |
| R1.3: validación de screening | PARCIAL: fase32 n1200 acuerdo relevancia .95 / κ.894; fase33 324 conciliados y 74 R9 | Ejecutar fase35 ponderada, diferenciar concordancia humana vs exactitud automática, mostrar incertidumbre y anomalías de procedencia |
| R1.4: 18 clústeres | COMPUTADO en fases03/14/19; decisión interpretativa PENDIENTE | No repetir ajustes. Presentar DB, CH, ARI seeds/subsamples y evaluación humana; k12 tiene ventaja numérica en chunks, k18 posible por resolución interpretativa, nunca "18 categorías naturales" |
| R1.5: sesgo texto completo | PARCIAL fases02/04/06 | Comparaciones año/discipline/policy/type/source/OA hechas; falta país/región y, sobre todo, RECONSTRUIR criterio exacto de selección 5000 de los 10265 y separar su sesgo del éxito 3656/5000 |
| R1.6: escasez vs madurez | CAMBIO DE TEXTO | Diferenciar frecuencia de calidad/madurez/importancia de política; no usar "underdeveloped" sin medición |
| R1.7: meta-analysis feasibility | CAMBIO DE TEXTO o estudio de validez adicional | Renombrar a potential quantitative-synthesis suitability, explicar reglas y limitaciones; no atribuir calidad/madurez |
| R1.8: tipos y repositorios | COMPUTADO parcialmente fase04 | 7216 registros journal+article/review de 10265; 2992/3656 fulltext análogo. Proxy journal ≠ revisión por pares certificada; revisar versiones preprint/artículo y DOI |
| R1.9: geografías teoría vs implementación | PENDIENTE como constructo | Retirar inferencia teórica o crear codificación geográfica nueva; mostrar solo volúmenes y redes medidos |
| R1.10: tipo de artículo | EDITORIAL prioritario | Solicitar Review/Methods/bibliometric mapping o cumplir estándar Systematic Review y limitaciones full-text; no inventar registro de protocolo |
| R1.11: novedad | EDITORIAL | Aportación es enfoque HE/política y análisis multinivel auditable, no volumen como novedad aislada |
| R1.12: reproducibilidad | PARCIAL: GitHub tiene scripts de revisión y reportes agregados | Añadir scripts originales de extracción, filtros, parámetros y materiales no copyright; PRISMA y depósito con identificador persistente |
| R1.13: denominadores y citas | PARCIAL técnico y editorial | 5000 intentos; 3655 downloaded+1 exists=3656 PDFs; uno sin texto=3655 textos positivos; 3644 explícitamente aceptados y 3629 cuerpos usable para chunks. Aclarar en cada figura/caption y auditar referencias |

## Correspondencia con Revisor 2

| Petición | Estado | Acción |
|---|---|---|
| Tipo de artículo / PRISMA / PICOS / RoB | PENDIENTE editorial | La reetiquetación del tipo y alcance es probable vía rápida; no afirmar calidad/riesgo de sesgo no analizados. PICOS no es obligatorio en toda revisión de mapeo, pero sí si se mantiene una pregunta de intervención |
| Búsqueda exacta, filtros, Q1, prompts, AI disclosure | PARCIAL fases06/07 | Extraer literalmente código y fecha de fuente; declarar MiniLM SentenceTransformer y reglas; aclarar uso genuino de IA generativa vs embeddings; no afirmar "No GenAI" sin comprobar |
| Sesgo 5000→3656 | PARCIAL fases02/04/06 | Dos fases de selección separadas y tabla adicional geográfica si existen datos |
| KMeans 18 y parámetros UMAP/HDBSCAN | COMPUTADO KMeans fases03/14/19; faltan empaquetado modelo/labels/términos | Presentar MiniLM-L6-v2 384d, max_seq_length256 original, KMeans semillas/n_init, estabilidad; si UMAP/HDBSCAN no se usaron, no inventar parámetros |
| Clasificación general HE, política, evidence maturity | PARCIAL: fase04 cuenta 2 "General HE" automático; fase32 humanos usan taxonomy diferente | Auditar etiqueta original y no sustituir con human general_he; dimensiones pueden ser single-primary o multi-label según código, debe verificarse |
| Figuras y tabla3 | PENDIENTE maquetación / si cambia partición, HPC regenerate | Reparar figuras panel A/B, Fig6 topic nombres reales, Table3 estructura, leyendas, colores, denominadores |
| Datos/reproducibilidad | PENDIENTE editorial + depósito | Reemplazar [NAME OF REPOSITORY] [LINK], preservar licencias, publicar scripts originales si autorizado |
| Declaración de IA | PENDIENTE ética editorial | Debe indicar uso real en análisis y escritura; separar análisis con MiniLM de GenAI, sin encubrir |
| Bibliografía/citas | PENDIENTE manuscrito | Completar lista y cita de Wang, Kofinas/Bittle etc. |
| Overclaims global | PENDIENTE manuscrito | Acotar al OpenAlex consultado, idioma del corpus y subconjunto open-access, sin inferencia causal |

## Resultados robustos reutilizables sin recomputar

- Fase03 ya ejecutó KMeans k12,18,25 con 5 seeds y 5 remuestreos; DB/CH/silhouette y ARI están publicados.
- Fase14 comparó en los MISMOS 3629 registros cuatro embeddings. En body_chunks: k12 silhouette cosine 0.116005, DB=2.66346, CH=127.78036, ARI mediana seeds .69458; k18 silhouette .100827, DB=2.851701, CH=98.23918, ARI mediana .54807; k25 silhouette .084329, DB=2.903424, CH=79.47277. No escoger k18 alegando superioridad numérica.
- Fase19: validación sustantiva sobre muestras sesgadas hacia centroides; coherencia temática media 2.91667 para body k12, 3.5 body k18 y 3.5 híbrido k18; la resolución más fina es argumento interpretativo condicionado, no superioridad universal.
- Fase02: distancia variación total para fulltext vs población: año .023, disciplina .0279, dimensión política .0302; país/region no figura entre comparaciones documentadas.
- Fase04: sensibilidad journal-indexed article/review con n7216 sobre n10265 y n2992 sobre fulltext n3656, incluyendo divergencia TV y Jensen–Shannon; NO implica verificación real de peer review.
- Fases30/32/33: dos evaluaciones de n1200 atribuidas a expertos, concordancia κ relevancia .893772; 324 registros de arbitraje y 74 R9 irresueltos; fase34 SOLO generó hojas de 148 textos completos, aún no revisados.
- Fase25, anterior control 80 casos enriquecidos en riesgo, tuvo baja concordancia con el consenso anterior (relevancia exacta .4125, disciplina .275). Fase27 fue conciliación NO ciega, no sustituye QA. Mantener y explicar los resultados desfavorables de desarrollo metodológico.

## Prioridad HPC para entregar hoy

**Hacer**: ejecutar nueva fase35; auditar exacto algoritmo de "5000 high-priority" y representatividad por región si el código original conserva el país; generar empaquetado FINAL de k12/k18/k25 y tabla de métricas ya ejecutadas, decidir coherentemente cuál partición corresponde a las figuras de la versión revisada. Hacer análisis de duplicación/versiones si es plausible y datos disponibles.

**No hacer hoy salvo exigencia editorial expresa**: repetir las 148 consultas de texto completo sin recursos, reentrenar MiniLM, generar miles de embeddings ya hechos, inventar parámetros UMAP/HDBSCAN, transformar una conciliación informada por A/B en tercera calificación ciega, y recalcular grafos de colaboración si no cambia la población.

**Riesgo científico mayor que más HPC:** el título sugiere investigación de política y arquitectura de texto completo, pero el universo incluye IA universitaria genérica y los vectores originales estaban muy afectados por truncamiento. Resolver este riesgo con evidencia/foco correcto antes de añadir más experimentos decorativos.

El repositorio es PÚBLICO: únicamente agregar informes agregados, scripts y tablas no sensibles; títulos, DOI caso a caso, documentos y encuestas originales permanecen PRIVADOS.
