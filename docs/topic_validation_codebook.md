# Protocolo de validación humana de tópicos — fase 15

## Objetivo
Evaluar **interpretabilidad**, **coherencia de los documentos agrupados**, **diferenciación entre temas** y **pertinencia para políticas de IA en educación superior**. Este experimento **no sustituye** el protocolo de pertinencia y cribado de la fase 5; ambos responden a preguntas diferentes. No afirmar validez humana hasta recibir dos evaluaciones independientes.

### Modelos candidatos, ocultos a los evaluadores
- Embeddings por fragmentos del cuerpo, k = 12.
- Embeddings por fragmentos del cuerpo, k = 18.
- Embeddings híbridos bibliografía + cuerpo (50/50), k = 18.

Para cada grupo se presentan siete publicaciones: tres prototípicas (próximas al centroide), tres aleatorias y una periférica. **Los evaluadores desconocen qué documentos son prototípicos y qué modelo produjo el grupo.** Los códigos neutros `G-001`, etc., se mantienen iguales en ambas planillas; su correspondencia con el algoritmo se conserva solo en una clave privada.

## Instrucciones para los dos evaluadores

Los archivos se generan **exclusivamente dentro de CEDIA, fuera del repositorio GitHub** en `~/ai_policy_topic_validation_private`. Cada evaluador trabaja **sin conocer las calificaciones del otro**.

**1. `rater_[a|b]_topics.csv`** (una fila por grupo). Después de examinar los siete ejemplos del grupo en la planilla de documentos, rellenar:

- `topic_name_proposed`: título temático propuesto sin usar la etiqueta automática previa.
- `topic_coherence_1_to_5`: 1 = no se reconoce un tema compartido; 2 = tema superficial/ambiguo; 3 = consistencia moderada; 4 = consistente; 5 = consistente, claro y específico.
- `distinctiveness_1_to_5`: 1 = solapamiento evidente con muchos otros grupos; 3 = cierta diferenciación; 5 = tema muy diferente del resto de grupos. Requiere haber examinado los demás grupos.
- `direct_policy_relevance_0_to_3_or_9`: 0 = ajeno a IA en educación superior; 1 = IA educativa sin dimensión política clara; 2 = implicación indirecta para políticas; 3 = investigación directa sobre regulación, gobernanza, instituciones, marcos normativos o políticas; 9 = información insuficiente.
- `confidence_1_to_5`: confianza en el juicio.
- `reviewer_comments`: justificación breve de la etiqueta y casos no coherentes.

**2. `rater_[a|b]_documents.csv`** (siete filas por grupo). Leer título, resumen y fragmentos orientativos del cuerpo. Los extractos no son secciones científicas formalmente identificadas y pueden contener ruido de extracción.

- `belongs_to_one_coherent_theme_0_no_1_yes_9_uncertain`: 0 = el documento no corresponde al tema que el evaluador acaba de nombrar; 1 = sí pertenece; 9 = incierto.
- `policy_relevance_0_to_3_or_9_uncertain`: usar la escala de pertinencia anterior, aplicada **al documento**, no al grupo.
- `document_comments`: evidencia para incluir o excluir y cualquier problema de extracción.

## Orden y adjudicación

1. No consultar la clave privada de modelos ni intercambiar respuestas antes de terminar ambas planillas.
2. Conservar exactamente los códigos de `group_code` e `item_code`. No cambiar los encabezados de columna.
3. Después del cierre independiente, calcular concordancia interevaluador: Cohen kappa para pertenencia binaria (excluyendo 9) y kappa ponderado para escalas ordinales, informar denominadores, los casos inciertos y sus distribuciones. Comparar nombres propuestos con adjudicación cualitativa por un tercer investigador (no calcular kappa sobre texto libre).
4. Adjudicar desacuerdos relevantes e identificar tópicos duplicados, muy amplios o sin pertinencia política. Evaluar diferencias entre los tres modelos sobre las mismas reglas.
5. El muestreo incluye prototipos y casos periféricos: **no** estimar una tasa poblacional de coherencia sin ponderar o modelar explícitamente el diseño estratificado. Las puntuaciones descriptivas son de la muestra elegida.
6. Registrar fechas, evaluadores, criterios, desacuerdos y cambios de interpretación para documentarlos en metodología; el informe público solo expondrá métricas agregadas.

## Seguridad

Ningún título, resumen, extracto del cuerpo, documento identificable, clave de muestreo ni planilla de evaluador debe subirse al repositorio GitHub público. Para las respuestas editoriales publicar solamente definiciones de indicadores, conteos agregados y estimaciones autorizadas.
