# Auditoría final de la regla de selección de 5.000 PDF (fase 37)

**Base de la comprobación:** fragmento de `~/ai_policy_he/scripts/10_download_open_access_pdfs.py`, líneas 58–85, mostrado directamente por el investigador el 8 de noviembre de 2026; informes agregados publicados de fases 36 y 37. El presente documento **no demuestra que esa revisión exacta del script sea la misma que se ejecutó históricamente** ni reconstruye identidades de todos los 5.000 casos.

## Regla verificable del código

1. Retener únicamente `ai_decision` en `Include_core`, `Include_policy`, `Include_context` (línea 58).
2. Crear `download_url` priorizando `pdf_url` cuando comienza con `http`. En su defecto, aceptar `landing_page_url` cuando comienza con `http` y termina en `.pdf` **o contiene la cadena `pdf`** (líneas 60–69). Mantener solo filas con `download_url` comenzando por `http` (línea 70). La mera presencia de un URL candidato **no confirma que sea accesible ni que devuelva contenido PDF válido**.
3. Calcular `priority_score` (líneas 72–80):

```text
5×1(Include_core) + 4×1(Include_policy) + 2×1(Include_context)
+ 3×is_review + 4×is_meta_candidate
+ 3×is_intervention_candidate + 2×is_latin
+ 4×coalesce_numeric(ai_include_score,0)
+ clamp(coalesce_numeric(cited_by_count,0),0,200)/200
```

Las tres categorías son excluyentes en la línea 58. `is_latin` es **nombre de bandera interna**, no prueba por sí solo una afiliación de autores a países de América Latina; requiere definición previa si se interpreta como variable geográfica.

4. Ordenar **descendentemente** por `priority_score`, desempatando por `cited_by_count` también descendente (línea 82). Seleccionar los primeros `MAX_PDFS=5000` (líneas 84–85).

La regla es **determinista condicionada a los datos, los valores de las banderas, el orden inicial en empates exactos y la versión del script**; no corresponde a muestreo probabilístico aleatorio. El número de citas entra tanto como término de puntuación limitado a 200 (de 0 a 1 punto) como criterio secundario de ordenación sin ese límite.

## Denominadores medidos

- 10.265 publicaciones incluidas tras cribado automático.
- Cantidad de incluidas con URL candidato válido **no conocida con las líneas entregadas**; no afirmar que las 10.265 participaron efectivamente del ranking de 5.000.
- 5.000 filas en manifiesto de intentos de descarga.
- 3.655 descargas más un fichero `exists` = 3.656 registros recuperados/preexistentes.
- 4.834 publicaciones del manifiesto de 5.000 vinculadas inequívocamente por DOI a la población de 10.265. No equivalen a la identidad exacta de toda la muestra de 5.000; 164 intentos carecen de DOI y dos corresponden a DOI ambiguo.

## Representatividad geográfica

La fase36 descartaba erróneamente los campos `countries` delimitados por punto y coma. Fase37 **la sustituye únicamente para comparaciones geográficas**, preservando la fase36. En 10.265 incluidos se recuperaron 1.685 cadenas ISO2 separadas por punto y coma; permanecen 2.763 casos sin país registrado. En 3.656 textos recuperados se recuperaron 587 cadenas y permanecen 855 sin país.

Las cifras geográficas describen **incidencia de afiliaciones nacionales por documento** (multipaís, denominadores por registros, no cuotas mutuamente exclusivas). Entre cambios de PDF vs corpus incluido destacan: US −1,225 pp; ID +1,115 pp; GB −0,846 pp; ZA +0,835 pp. La existencia de cambios pequeños entre algunas cuotas **no demuestra ausencia de sesgo**, porque existe selección deliberada por puntuación y falla de recuperación no aleatoria.

## Implicaciones para respuesta a revisores

- **R1/R2 sesgo de selección y transparencia:** el subconjunto de 3.656 textos completos es *purposively prioritised and availability-constrained*, no representativo por diseño probabilístico de todos los 10.265.
- **R1/R2 geografía:** se ofrece análisis descriptivo corregido, con disponibilidad de país de 73,1 % y 76,6 % respectivamente. No inferir causalidad, diferencias significativas ni calidad científica por país.
- **Texto completo:** recuperación del PDF no equivale a evaluación humana de elegibilidad integral; 148 solicitudes adicionales de texto completo de la validación separada de 1.200 siguen pendientes.
- **Clasificador:** la elevada concordancia de evaluadores humanos no implica rendimiento predictivo pleno del cribado de política. Fase35 estima relevancia R2/R3 en rangos sensibles a casos inciertos.

## Redacción propuesta para Methods (English)

> Full-text retrieval was conducted using a purposive, priority-based selection strategy rather than random sampling. After automated title-and-abstract screening, records assigned to the Include_core, Include_policy, or Include_context categories were retained only when a candidate PDF URL or an eligible landing-page URL was available. A composite priority score combined screening class (5, 4, or 2 points, respectively), review status (+3), meta-analysis candidate status (+4), intervention candidate status (+3), a script-defined Latin-America relevance indicator (+2), the automated inclusion score (multiplied by 4), and a normalized citation component capped at 200 citations (0–1 points). Records were ordered by decreasing priority score, with citation count as a secondary descending key, and up to 5,000 candidates were selected for retrieval. The download manifest contains 5,000 attempts, of which 3,655 resulted in downloads and one corresponded to a pre-existing file, yielding 3,656 records with available PDF files. The full-text subset was therefore deliberately prioritized and availability-constrained and should not be interpreted as a probability sample of all 10,265 machine-included records.

## Redacción propuesta para Limitations (English)

> The full-text subset was not selected randomly. Candidate-URL availability, priority-score components, citation counts, and retrieval failures could introduce selection bias. Accordingly, geographic and thematic comparisons between the machine-included corpus and the retrievable full-text subset are descriptive rather than evidence of population representativeness. Country incidence was calculated from available institutional-affiliation metadata after parsing semicolon-delimited ISO country codes, but missing country information remained for 2,763 included records and 855 full-text records. Furthermore, bibliographic screening validation and PDF retrieval do not establish article-level full-text eligibility.

## Respuesta breve propuesta para revisores (English)

> We clarified the original PDF selection algorithm and explicitly acknowledged its nonrandom nature. Eligible download candidates were ranked using a documented composite priority score (screening category, review/meta-analysis/intervention indicators, script-defined Latin-America indicator, automated inclusion score, and citations); the top 5,000 were targeted for retrieval. Of these, 3,656 PDFs were downloaded or already available. We also added a descriptive comparison of the 10,265 machine-included records with the retrievable full-text subset, including corrected country-of-affiliation parsing and transparent missingness counts. We no longer imply that the retrievable full-text subset is a probability sample or that PDF availability establishes final study eligibility.

## Elementos no comprobados por el fragmento

La definición de las banderas `is_review`, `is_meta_candidate`, `is_intervention_candidate`, `is_latin` antes de la línea 55; la versión exacta ejecutada históricamente; el número de registros con URL candidato antes del ranking y el desempate de scores/citas idénticos; comparación de membresía exacta de 5.000 porque el manifiesto no contiene `openalex_id`. No rellenar esos datos por inferencia.
