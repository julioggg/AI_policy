# Código de clasificación V1.0 — validación integral de 1.200 registros

**Estado:** versión preespecificada y fija para validación de 1.200 publicaciones por DOS NUEVOS expertos independientes. **Sin piloto**, por decisión del investigador principal, noviembre de 2026. Esta nueva versión no se utilizó en las fases 21–27 y no debe afirmarse lo contrario.

## Objeto científico

Evaluar sistemáticamente el alcance universitario y la relevancia política de publicaciones con IA seleccionadas por un cribado automático. Separar rigurosamente: (S) alcance; (R) pertinencia política; (T) tema principal; (D) disciplina principal. Los títulos/resúmenes, sin texto completo adjunto, son la evidencia inicial; si no basta, marcar insuficiencia y solicitar revisión de texto completo. No inferir que autores universitarios convierten un artículo técnico general en estudio de educación superior.

## Escala S — alcance

- 0: fuera de IA aplicada a educación superior.
- 1: IA aplicada a enseñanza, evaluación, investigación, alumnado, profesorado o gestión UNIVERSITARIA.
- 9: título/resumen no permiten decidir.

## Escala R — relevancia política

- 0: no trata IA en educación superior. Exige S0.
- 1: IA en educación superior SIN mecanismo normativo, gubernativo o institucional verificable en el objetivo/hallazgo.
- 2: estudio sobre IA en educación superior con efecto de una norma, política, decisión institucional o mecanismo de gobernanza ESPECÍFICO, documentado en objetivos/resultados, pero cuyo foco principal no es analizar la política en sí. Se debe nombrar el mecanismo.
- 3: la política, norma, reglamento, regulación, estrategia institucional, responsabilidad, supervisión o gobernanza de IA en educación superior constituye el OBJETO PRINCIPAL investigado. Debe nombrarse el objeto normativo.
- 9: evidencia insuficiente. No equivale a exclusión ni a categoría ordinal superior. Requiere fulltext_required=yes y especificar por qué.

**Restricciones:** S0 implica R0; S9 implica R9; S1 permite R1/R2/R3/R9. R2 y R3 necesitan policy_mechanism y evidence_excerpt. Una recomendación genérica para formar docentes, una mención a ChatGPT, un tema de ética o un tema de evaluación no justifican por sí solos R2/R3.

## Ejemplos HIPOTÉTICOS de entrenamiento (no pertenecen a la muestra)

| Descripción ilustrativa | S | R | Tema | Distinción |
|---|---|---|---|---|
| Clasificación neuronal de fallas en paneles solares | 0 | 0 | not_applicable | No estudia universidad |
| Tutor GPT y rendimiento en estudiantes universitarios | 1 | 1 | teaching_learning | Efecto pedagógico sin norma |
| Experimento universitario que recomienda genéricamente capacitar a docentes | 1 | 1 | teaching_learning | Recomendación incidental |
| Impacto de un reglamento institucional de acceso inclusivo a IA | 1 | 2 | equity_access | Efecto de norma específica |
| Comparación de reglamentos universitarios sobre derechos de autor con IA | 1 | 3 | governance_policy | Normativa objeto central |
| Modelo para detectar plagio con IA en tareas | 1 | 1 | assessment | Herramienta ≠ norma |
| Auditoría de procesos de apelación por detectores IA regulados | 1 | 3 | assessment | Regla de evaluación objeto central |
| Opiniones sobre plagio asistido por IA en universitarios | 1 | 1 | ethics_integrity | Tema ético no es política |
| Cambio conductual tras sanción institucional por plagio de IA | 1 | 2 | ethics_integrity | Efecto de regla |
| «Ética de IA en educación» sin resumen ni nivel | 9 | 9 | uncertain | Insuficiente información |

## Diccionarios de T y D

**T:** teaching_learning, assessment, ethics_integrity, governance_policy, research_scholarship, ai_literacy_training, equity_access, privacy_security, general_policy, not_applicable, uncertain.

**D:** ssh, engineering, health_sciences, general_he, uncertain.

T es objeto temático primario, D el área de estudio. Elegir por objetivo/contribución del documento, NO solo por revista o filiación; si hay interdisciplinariedad sin predominio, D=general_he. Un tema ethics_integrity, assessment o governance_policy no determina automáticamente R=2 o R=3.

## Campos de respuesta obligatorios

En la pestaña VALIDACION, los campos visibles e inmutables son: código ciego, título, resumen, año y tipo. Los ocho campos editables F–M son: scope_code, relevance_code, primary_topic, primary_discipline, policy_mechanism, evidence_excerpt, fulltext_required (yes/no), reason.

Completar evidencia específica extraída del título/resumen y una justificación concreta en TODAS las filas. Para R2/R3 indicar mecanismo normativo identificable; para R9 describir información faltante y marcar yes en fulltext_required. No fabricar evidencia de cuerpos no suministrados. No revisar el artículo íntegro por cuenta propia durante el cribado inicial salvo procedimiento autorizado y documentado. Las opiniones generadas por herramientas de IA no son calificaciones humanas independientes.

## Protocolo de independencia

Evaluadores A y B reciben exactamente las mismas 1.200 publicaciones en distinto orden, sin estrato, predicción automática, DOI/identificador OpenAlex ni etiquetas de fases previas. No se consultan entre sí; se devuelven Excel separados. Se conservan versiones originales, fechas y huellas SHA256 antes de cualquier comparación. Las decisiones humanas originales NUNCA se sobrescriben después del arbitraje.

Al disponer de las dos evaluaciones, calcular acuerdo exacto por S/R/T/D, tablas cruzadas y kappa, manejando R9 como incertidumbre. Posteriormente escalar a texto completo los R9 y casos potencialmente elegibles que lo necesiten, con resolución documentada por el panel. No contar una adjudicación informada por puntuaciones previas como tercer revisor ciego.

## Universo y muestra

Marco original 10.283 registros del cribado final (sin retirar 30 de un piloto, ya que no habrá piloto). Asignación probabilística: include_core 9.264 de los cuales n=800; include_policy 899 con n=290; include_context 102 con n=92; exclude 18 con n=18, censo. Total 1.200. El hecho de que un caso hubiera sido leído en las fases 21–27 NO lo elimina del marco: si es sorteado, dos expertos NUEVOS y ciegos lo evalúan sin consultar esos resultados. Los dos grupos q1_not_article_ready 11.393 y core_not_q1 848 son exclusiones BIBLIOGRÁFICAS anteriores, que deben estudiarse separadamente si se afirma validez del procedimiento íntegro.

No reconfigurar estratos, umbrales, correspondencia entre predicciones del sistema y categorías humanas ni esta rúbrica cuando se conozcan las respuestas. Los estimandos propuestos son S=1, R≥2 y R=3. El nombre de la categoría automática no prueba la equivalencia a un estimando humano: hay que documentar el mapeo antes de calcular la matriz de confusión.

## Transparencia y limitaciones

**Se omitió deliberadamente un piloto formal de 20–30 registros.** Esto evita una etapa de entrenamiento y permite comenzar inmediatamente, pero no proporciona evidencia previa de uniformidad interpretativa. Debe consignarse en el artículo y no ocultar la variabilidad del acuerdo. Los estimadores ponderados necesitan diseño probabilístico, resoluciones de incertidumbre y CI adecuados. La categoría directa R3 puede resultar escasa; si no hay suficientes casos, informar intervalos amplios o resultados no estimables, sin reclasificar casos para mejorar métricas.

Referencias: PRISMA 2020 item 8 https://pmc.ncbi.nlm.nih.gov/articles/8005925/ ; Cochrane Handbook Chapter 4 https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04 .
