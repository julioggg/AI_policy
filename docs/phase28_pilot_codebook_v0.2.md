# Fase 28 — Rúbrica operacional V0.2-PILOT

**Proyecto:** AI Policy in Higher Education. **Estado:** versión de trabajo congelable para un PILOTO independiente de 30 publicaciones; NO constituye la rúbrica final de validación ni se aplicó retroactivamente a las fases 21–27.

## Tres dimensiones distintas que no deben confundirse

**S — Alcance de IA en educación superior.** S=0 significa fuera del campo de IA aplicada a alumnado, profesorado, gestión, docencia, evaluación o investigación en educación superior. S=1 significa dentro del campo. S=9 significa que título/resumen no permiten decidir. No basta que los autores pertenezcan a una universidad para que el estudio sea de educación superior.

**R — Pertinencia política.** Clasificación ordinal 0–3, con 9 reservado para evidencia insuficiente. La pertinencia política depende de los objetivos y resultados, no de palabras clave o de la posible utilidad genérica del estudio.

**T — Tema principal.** Describe el objeto temático, independientemente de R. Un artículo que trata ética o evaluación puede ser R=1 si no examina preguntas políticas.

**D — Disciplina principal.** Describe el campo principal de contribución y no necesariamente la afiliación de los autores.

## Escala R

- **0 — Fuera de alcance.** No se estudia conjuntamente IA y educación superior. Ejemplo ilustrativo ficticio: redes neuronales para diagnóstico de fallas eléctricas sin escenario educativo. Requiere S=0.
- **1 — IA en educación superior sin política demostrada.** Estudio de utilización, impacto, percepción o diseño de IA en universidades, sin objetivo normativo ni mecanismo político o institucional concreto sustentado. Ejemplo ficticio: experimento de tutor ChatGPT que mejora notas de universitarios. Incluso la frase genérica «universities should adopt AI responsibly» no justifica R=2.
- **2 — Implicación política indirecta sustentada.** El objetivo principal puede ser pedagógico o técnico, pero el resumen documenta un hallazgo sobre una decisión, norma o práctica institucional ESPECÍFICA, identificando mecanismo relevante. Ejemplo ficticio: impacto desigual de una política universitaria concreta de acceso a asistentes de IA.
- **3 — Política/gobernanza directa.** El objeto primario del estudio consiste en desarrollar, comparar, evaluar, aplicar o investigar reglamentos, normas, políticas, mecanismos de gobernanza, rendición de cuentas o supervisión de IA en educación superior. Ejemplo ficticio: comparación de las reglas formales sobre autoría con IA generativa de 40 universidades.
- **9 — Insuficiencia de evidencia.** Resumen ausente, truncado o insuficiente para decidir S o R. Se describe qué falta y se marca necesidad de texto completo. No es una categoría ordinal más alta ni un negativo automático.

**Reglas de consistencia:** S=0 exige R=0. S=9 exige R=9. S=1 permite R=1/2/3 o R=9 cuando la evidencia no permite establecer pertinencia política. Para R=2/3 se exige identificar una norma, una decisión institucional o un mecanismo de gobernanza concreto y la evidencia textual que la sustenta. R=9 exige señalar consulta de texto completo.

## Ejemplos artificiales para capacitación (NO son estudios de la muestra)

| Descripción abreviada ficticia | S | R | T | Distinción |
|---|---:|---:|---|---|
| Predicción neuronal de rendimiento de batería | 0 | 0 | not_applicable | No es educación superior |
| Tutor IA mejora notas universitarias | 1 | 1 | teaching_learning | Eficacia pedagógica, no regulación |
| Recomendación genérica de formar a docentes al final de un ensayo | 1 | 1 | teaching_learning | Recomendación incidental no es política |
| Evaluación de consecuencias de una política institucional de acceso a IA | 1 | 2 | equity_access | Mecanismo institucional explícito; objetivo de impacto |
| Comparación de políticas universitarias de IA generativa | 1 | 3 | governance_policy | Normativa objeto primario |
| Diseño técnico de detector de plagio por IA | 1 | 1 | assessment | Herramienta, no marco regulatorio |
| Análisis de reglamentos de apelación al usar detectores de IA | 1 | 3 | assessment | Reglas estudiadas directamente |
| Actitudes hacia plagio con ChatGPT | 1 | 1 | ethics_integrity | Tema ético no implica norma |
| Efectos sobre conducta de una sanción institucional por plagio con IA | 1 | 2 | ethics_integrity | Consecuencia de una decisión formal |
| «Ética de IA en educación» sin nivel educativo ni resumen | 9 | 9 | uncertain | Evidencia insuficiente |

Estos casos NO deben presentarse como registros auténticos ni incorporarse a ninguna estimación de validación.

## Reglas del tema principal T

Valores oficiales: teaching_learning (enseñanza y aprendizaje), assessment (evaluación y calificación), ethics_integrity (ética e integridad académica), governance_policy (gestión y políticas), research_scholarship (investigación y trabajo académico), ai_literacy_training (alfabetización/capacitación), equity_access (equidad/acceso), privacy_security (privacidad/seguridad), general_policy (política general), not_applicable (fuera de alcance), uncertain (no determinado).

Seleccionar según el objeto primario. T=ethics_integrity, T=assessment o T=governance_policy **NO fuerza** R=2/3. La clasificación temática y la pertinencia política deben decidirse por separado.

## Reglas de disciplina D

ssh (ciencias sociales y humanidades), engineering (ingeniería/tecnología), health_sciences (ciencias de la salud, incluida su docencia), general_he (educación superior general/transversal), uncertain (insuficiencia de evidencia). No inferir D por la revista o la afiliación de los autores. Si hay disciplinas múltiples y ninguna domina, general_he.

## Formulario de decisión

El evaluador registra por publicación: código ciego, título, resumen, año y tipo (inmutables); scope_code S; relevance_code R; primary_topic T; primary_discipline D; policy_mechanism (texto de la norma o decisión concreta, obligatorio para R2/R3); evidence_excerpt (frase breve o paráfrasis precisa del resumen/título); fulltext_required yes/no; reason (justificación específica no repetitiva).

Validar: S=0/R=0, S=9/R=9; R=2/R=3 exige mecanismo; R=9 exige fulltext_required=yes; todos los casos requieren evidencia y justificación. Ante incertidumbre, no inventar el cuerpo del artículo.

## Procedimiento de independencia y congelación

1. Antes de generar archivos, registrar hash de esta V0.2-PILOT, código fuente, semilla y marco documental en manifest privado. Una vez enviados los libros, no modificar instrucciones hasta que ambos califiquen.
2. El piloto selecciona **30 registros no incluidos en la antigua muestra de 368**: 10 del estrato automático include_core, 10 de include_policy y 10 de include_context. **No incluye los 18 casos exclude**, ya revisados íntegramente en la fase antigua y reservados para auditoría de validación posterior con nuevos evaluadores. El piloto es deliberadamente enriquecido para calibrar; NO representativo.
3. Se generan dos archivos Excel privados, A y B, mismos 30 casos en orden diferente, TODOS los campos de decisión vacíos, sin ID original OpenAlex, clasificación automática, estrato ni calificación histórica. No compartir un archivo con el otro evaluador.
4. Ambos anotadores trabajan independientemente, sin LLM que emita las respuestas, sin consultar la etiqueta automática ni debatir los casos. Las respuestas originales se conservan inalteradas; el supervisor las coteja con fuentes y sellos de integridad.
5. Calcular acuerdo por campo, matriz ordinal 0–3, fuentes de desacuerdos 1↔2, 2↔3 y 9. Conservar valores inciertos; **ningún código se impone automáticamente**. Solo después de cerrar A y B se discute y actualiza la rúbrica.
6. La referencia JBI recomienda un piloto de 25 títulos/resúmenes y acuerdo ≥75 % antes de iniciar cribado de revisión de alcance. Aquí 30 y 75 % son criterios operativos iniciales de calibración, no prueba concluyente de validez ni sustitutos de análisis de ambigüedad.
7. Tras piloto, generar historial de modificaciones y congelar **V1.0-VALIDATION**, luego preespecificar muestra probabilística final, estimandos, tamaño/precisión, normas de tratamiento del texto completo y el mapeo de etiquetas automáticas a preguntas humanas.
8. Los casos del piloto no pueden incorporarse a la evaluación final. Dos nuevos evaluadores, preferentemente sin exposición a documentos previos, realizarán el cribado final ciego de la nueva muestra estratificada; el estrato exclude tiene solo 18 casos en el universo y habrá que auditarlo como censo con nuevos lectores ciegos.

## Declaraciones y transparencia

El presente piloto no corrige retrospectivamente los desacuerdos de las fases 21–27. Es un entrenamiento metodológico para el nuevo experimento de validación. No publicar nombres, títulos, resúmenes, IDs, decisiones de personas ni claves de muestreo en el repositorio público.

**Referencias:**
- JBI Manual for Evidence Synthesis (2026), sección 10.2.7.1: https://jbi-global-wiki.refined.site/space/MANUAL/2049540102/10.2.7.1%2BPiloting%2Bthe%2Bselection%2Bof%2Bstudies
- Cochrane Handbook 6.5.1, capítulo 4, selección independiente y piloto: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04
- PRISMA 2020, ítem 8: https://pmc.ncbi.nlm.nih.gov/articles/8005925/
