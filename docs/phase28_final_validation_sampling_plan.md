# Diseño provisional de la validación final — después del piloto V0.2

**Estado:** PLAN ESTADÍSTICO PRELIMINAR, NO MUESTRA EJECUTADA Y NO MÉTRICAS VALIDADAS.

## 1. Población, unidad y restricciones de solapamiento

La población existente de cribado automático tiene N=10.283 registros bibliográficos: include_core 9.264, include_policy 899, include_context 102 y exclude 18. Las 11.393 exclusiones q1_not_article_ready y las 848 core_not_q1 se deben estudiar por separado como filtro bibliográfico anterior, NO como clase negativa del clasificador final.

La fase28 selecciona 30 artículos para el PILOTO de capacitación (10+10+10) y debe mantenerlos FUERA del holdout final. Por ello, **el estimando primario de la validación prospectiva sin piloto se referirá a N=10.253** registros, con las siguientes poblaciones: core 9.254; policy 889; context 92; exclude 18. NO reportar que las cifras de esa validación describen sin condiciones los 10.283 originales. Se puede reportar que se retiró del marco la muestra de capacitación conocida, 30/10.283=0,292 %, e incluir una sensibilidad de esta exclusión. Para una estimación del marco original sin exclusiones se necesitarían evaluaciones nuevas apropiadas de esos 30 casos bajo la versión final, sin reutilizar etiquetas del piloto.

**Crítico:** Los 368 casos de las fases 05/21 no deben excluirse automáticamente del marco probabilístico final si se pretende inferir sobre el universo completo no-piloto. Podrán ser sorteados con sus probabilidades normales y se evaluarán desde cero, usando lectores diferentes que NO conozcan las decisiones originales. Excluir deliberadamente todas las publicaciones anteriormente evaluadas crearía probabilidad de inclusión cero en regiones del marco, invalidando la inferencia sin corrección explícita.

Los 18 registros machine-exclude constituyen un censo completo, ya cubierto anteriormente; para la nueva evaluación se necesitarán lectores nuevos efectivamente ciegos. En este estrato la incertidumbre de muestreo es cero (sin que desaparezcan errores humanos o del codebook).

## 2. Estimandos preespecificables — distintos

- Estimando de alcance S positivo: evaluación humana S=1 entre los registros.
- Estimando de pertinencia institucional o normativa indirecta/directa: R en {2,3}.
- Estimando estricto de investigación *directamente* sobre políticas y gobernanza: R=3, subconjunto de R≥2.
- Tasas de categoría de tema T y disciplina D con denominador y tratamiento explícito de uncertain.
- Solo después de inspeccionar las **reglas reales de decisión automática** y el objetivo de cada estrato, declarar mapeo prespecificado a decisiones binarias o multiclase. No equivale automaticamente include_policy a R≥2, ni include_core a R=3. Se puede estimar directamente la distribución de la puntuación R dentro de cada estrato automático.

Los casos S9/R9 no se convertirán en positivos ni negativos. Se escalarán a texto completo cuando sea factible, se documentarán sin resolver si faltan datos y se calcularán análisis de sensibilidad.

## 3. Tamaño y asignación — ejemplo conservador inicial

Tras revisar el piloto, un ejemplo de asignación sobre los **10.253 NO PILOTO** es:

| Estrato automático | N no piloto | n planeada (ejemplo) | Tipo |
|---|---:|---:|---|
| include_core | 9.254 | 350 | Muestra aleatoria simple sin reemplazo |
| include_policy | 889 | 90 | Muestra aleatoria simple sin reemplazo |
| include_context | 92 | 60 | Muestra aleatoria simple sin reemplazo |
| exclude | 18 | 18 | Censo |
| **Total** | **10.253** | **518** | Dos evaluadores nuevos por registro |

Con variable binaria de máxima varianza p=0,5 en cada estrato, ponderación por W_h=N_h/10.253 y corrección por población finita, el margen de confianza normal aproximado al 95% para **una proporción de contenido agregada** sería ±4,72 puntos porcentuales (no para una clase rara ni para sensibilidad/recall). Este es un cálculo preliminar de planificación bajo un modelo de respuesta binaria y muestreo aleatorio; es preciso recalcularlo ante costos, desacuerdos reales, casos inciertos y desenlaces específicos.

La selección no se realizará hasta: calibración del piloto de 30, congelación del codebook V1.0, especificación de estimandos y mapeo de decisiones automáticas, y registro previo de la semilla. En la validación final los datos de entrenamiento del codebook no entran a las estimaciones; los casos antiguos pueden reaparecer solo con **nuevos** evaluadores ciegos y nueva calificación.

## 4. Estimación por diseño estratificado

Con h=estrato y W_h=N_h/N*, la prevalencia binaria puede estimarse como

P_estimado = Σ_h W_h × p_estimado_h.

Su varianza de muestreo, bajo MAS sin reemplazo, se estima mediante

V_estimado = Σ_h [W_h² × (1 - n_h/N_h) × s²_h / n_h].

Para una variable 0/1, s²_h = n_h × p_h × (1-p_h)/(n_h-1) cuando n_h>1. Para estratos censales, el término de varianza de muestreo es cero. Usar intervalos adecuados cuando la clase sea rara, n pequeño o límite 0/1; no limitarse al intervalo normal si la distribución es asimétrica.

Para medir desempeño de un predictor automático, calcular totales estimados de las celdas de la matriz de confusión con factores de expansión N_h/n_h, y recién entonces derive sensibilidad, precisión, especificidad, VPP, etc., con incertidumbre de diseño (bootstrap estratificado o técnicas de razón apropiadas). No usar automáticamente promedios no ponderados de 518 publicaciones ni reportar validación de texto completo basada en títulos/resúmenes.

## 5. Protección metodológica

- Los 30 casos piloto no entran en el holdout.
- Formularios individuales ciegos sin ID OpenAlex, estrato, predicciones automáticas ni A/B anteriores.
- Dos personas realmente independientes, idealmente diferentes de los cuatro primeros roles humanos, confirman decisiones y justificaciones antes de conciliarlas.
- Registrar entrenamiento, rúbrica usada, fecha/hora, libro original y hash, conflictos, arbitraje, incertidumbre e intervenciones de texto completo.
- Conservar todos los resultados adversos e incluir el bajo acuerdo de la fase 25 en el manuscrito. La fase 27 no sustituyó el control independiente.
- NO hacer nuevas afirmaciones cuantitativas de eficacia hasta finalizar los datos prospectivos.

**Estado del presente documento:** planificación únicamente; ni muestra n=518 seleccionada ni revisión n=518 realizada.
