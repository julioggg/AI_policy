# Entrega y recuperación de Excel para evaluadores independientes

Esta guía es para el **coordinador**; los evaluadores solo reciben un Excel cada uno y un instructivo. La fase 15 ya preparó las muestras, pero **no calificó** artículos ni temas.

## 1. Convertir las hojas privadas de la fase 15 a Excel

Ejecutar en la sesión Singularity de CEDIA:

```bash
cd "$HOME/AI_policy"
git pull --ff-only
python -m py_compile scripts/17_excel_reviewer_packages.py
python scripts/17_excel_reviewer_packages.py \
  --mode export \
  --private-in "$HOME/ai_policy_topic_validation_private" \
  --out-dir "$HOME/ai_policy_excel_para_evaluadores_privado"
realpath "$HOME/ai_policy_excel_para_evaluadores_privado"
ls -lh "$HOME/ai_policy_excel_para_evaluadores_privado"/*.xlsx
```

Esta operación genera:

- `Evaluador_A.xlsx`: enviar **solamente** al primer evaluador.
- `Evaluador_B.xlsx`: enviar **solamente** al segundo evaluador.
- `LEER_ANTES_DE_ENVIAR.txt`: información para el coordinador, no es necesario compartirla.

Cada Excel contiene cuatro pestañas: INSTRUCCIONES, DOCUMENTOS (336 filas), GRUPOS (48 filas), ESCALAS. Los **campos amarillos** se rellenan con listas desplegables; los identificadores y los textos quedan protegidos en la importación posterior por verificaciones de integridad. Ninguno de los libros contiene la clave de modelo/k ni el muestreo por prototipo.

## 2. Descargar desde CEDIA

Conectar un cliente SFTP autorizado (por ejemplo, WinSCP en Windows) al **servidor de acceso SSH usado normalmente para entrar a CEDIA**. No asumir que el nombre de un nodo de cómputo interno permite SFTP desde Internet. Navegar a la ruta mostrada por `realpath` y descargar **los dos .xlsx** a la computadora local. Si SFTP no permite acceder a un nodo de cómputo, mover o copiar los archivos dentro del espacio privado accesible desde el nodo de acceso, conforme a las políticas de CEDIA.

Compartir cada libro por un canal privado con el evaluador correcto. No subir los libros a GitHub, servicios públicos de transferencia o repositorios abiertos. El investigador debe conservar el archivo .xlsx y los códigos de grupos/documentos sin alteraciones.

**No entregar** a los evaluadores `private_sampling_key.csv`, `private_validation_manifest.json`, los vectores del modelo ni ningún fichero del proyecto original.

## 3. Instrucciones para los evaluadores (sin programación)

1. Abra el Excel asignado. La primera pestaña contiene las instrucciones y la última las escalas.
2. En DOCUMENTOS, filtre por `Código grupo`; hay siete publicaciones por grupo. Lea título, resumen y fragmentos orientativos.
3. En GRUPOS, proponga un nombre temático, califique coherencia (1–5), diferenciación (1–5), pertinencia política (0–3 o 9) y confianza (1–5).
4. En DOCUMENTOS, indique para cada publicación si pertenece al tema propuesto (0, 1 o 9), y su pertinencia política (0–3 o 9).
5. Justifique casos dudosos y haga el análisis sin ver las calificaciones del otro evaluador.
6. Complete exclusivamente las celdas amarillas y guarde el MISMO .xlsx; no altere columnas, códigos ni registros. Devuélvalo por un canal privado.

**9 significa incertidumbre por evidencia insuficiente**, no puntuación alta. No existe una puntuación esperada. Las respuestas negativas también son científicamente importantes.

## 4. Cargar Excel terminados y estandarizarlos de forma segura

Crear una carpeta protegida solo para los dos Excel recibidos y cargarlos allí mediante el cliente SFTP:

```bash
mkdir -p "$HOME/ai_policy_excel_recibidos_privado"
chmod 700 "$HOME/ai_policy_excel_recibidos_privado"
```

Colocar los archivos con estos nombres exactos dentro de ella: `Evaluador_A.xlsx` y `Evaluador_B.xlsx`.

Una vez recibidos, ejecutar, **en ese orden**:

```bash
cd "$HOME/AI_policy"
git pull --ff-only
python scripts/17_excel_reviewer_packages.py \
  --mode import \
  --private-in "$HOME/ai_policy_topic_validation_private" \
  --received-xlsx "$HOME/ai_policy_excel_recibidos_privado/Evaluador_A.xlsx" \
  --reviewer a \
  --out-dir "$HOME/ai_policy_calificaciones_normalizadas_privado"

python scripts/17_excel_reviewer_packages.py \
  --mode import \
  --private-in "$HOME/ai_policy_topic_validation_private" \
  --received-xlsx "$HOME/ai_policy_excel_recibidos_privado/Evaluador_B.xlsx" \
  --reviewer b \
  --out-dir "$HOME/ai_policy_calificaciones_normalizadas_privado"
```

El importador compara los grupos, identificadores, número de filas y textos fuente con las muestras protegidas. Rechaza duplicaciones, eliminación de filas, cambios en evidencia, escalas inválidas y libros intercambiados. El resultado son las **cuatro planillas CSV estandarizadas** junto con los archivos privados de correspondencia, en `~/ai_policy_calificaciones_normalizadas_privado`. Las muestras originales de fase 15 permanecen intactas.

Si uno de los Excel contiene un error, pedir una versión corregida. Para evitar sobrescribir una importación anterior ya validada, utilizar una **nueva carpeta de destino** cuando cambien calificaciones previamente importadas.

## 5. Calcular concordancia interevaluador

```bash
cd "$HOME/AI_policy"
python scripts/16_score_human_topic_review.py \
  --private-in "$HOME/ai_policy_calificaciones_normalizadas_privado" \
  --out reports/phase16
git add reports/phase16
git diff --cached --quiet || git commit -m "Phase 16: validated human review aggregate"
git push origin main
```

Con planillas incompletas la fase 16 informa `awaiting_independent_human_ratings` y **no fabrica resultados**. Cuando ambas están completas calcula indicadores descriptivos y de concordancia; la adjudicación posterior sigue siendo una tarea humana separada.

**Política de privacidad:** solo el informe agregado `reports/phase16` puede subirse a GitHub. No subir los Excel, los CSV, identificadores, comentarios, títulos, resúmenes o fragmentos extraídos.
