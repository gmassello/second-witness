# Voyascope (mentoce0-gif/voyascope) — revisión de un visor GMN para el público

Fecha de la revisión: 2026-11-26. Modo: producto/OSS, sin clone (todo con `gh api` y `curl` de solo lectura; no se ejecutó ni instaló nada).
Repo: https://github.com/mentoce0-gif/voyascope · sitio: https://voyascope.org

## Veredicto

No es competidor: es un **complemento de otra capa**. Voyascope muestra *meteoros* (un cielo en ojo de pez por ciudad); Second Witness muestra *estaciones, pares y qué cuesta perder una*. Voyascope descarta a propósito los códigos de estación, así que no hay solapamiento de datos ni de pregunta. Lo útil son tres lecciones de manejo de datos GMN y un par de ideas de texto llano.

## Qué es (ojo: no es solo un visor GMN)

- Evidencia: `README.md`, `CLAUDE.md`. VOYASCOPE es una app para ver "el ahora" de satélites, naves y astronautas (público: secundaria, en japonés, fan-made, no oficial). La parte GMN es **una sola página experimental**, `web/meteors/index.html` ("流星を眺める（試験版）", `<meta name="robots" content="noindex">`, línea 8), publicada el 2026-11-21 (`docs/handoff.md` línea 14).
- Muestra la noche del **2026-11-18** desde 9 ciudades: Tokio, Osaka, Fukuoka; Nueva York, Toronto, Denver; Londres, París, Zagreb (`docs/handoff.md` líneas 113-114). Cielo en ojo de pez (proyección equidistante, norte arriba, este a la izquierda), estrellas Hipparcos, Vía Láctea ESO, luna, línea de tiempo con reproducción x60/x120/x600.
- Datos de repo: creado 2026-10-04 (se rehizo el historial), push más reciente 2026-11-26, 0 estrellas, sin homepage declarada en el API (el sitio está en el README), licencia "All rights reserved" (SPDX NOASSERTION). Runs de CI: los 10 últimos `success` (`v.runs`).

## 1. Datos GMN que baja

| Qué | Evidencia |
|---|---|
| URL: `https://globalmeteornetwork.org/data/traj_summary_data/daily/` (listado HTML, se parsea con regex `traj_summary_(\d{8})_solrange_[\d.\-]+\.txt`) | `scripts/gmn/fetch_and_filter.py` líneas 28 y 76-82 |
| Archivos: **diarios**, no mensuales. Para Japón lee `20261117` y `20261118`; para Europa y Norteamérica solo `20261118` | mismo script, `REGIONS` |
| Frecuencia: **una sola vez, a mano** ("one-off download" en el User-Agent). El JSON sale versionado en `web/meteors/data/meteors_20261118_{japan,europe,namerica}.json`. No hay workflow diario de GMN: los cinco workflows son `deploy`, `pages`, `update-horizons`, `update-orbits` (órbitas de satélites) y `validate` | `v.tree`, `.github/workflows/*` |
| Caché: ninguna más allá de `--local DIR` (archivos ya bajados) | script, `main()` |
| Columnas usadas (15, por nombre y no por posición): `Beginning UTC Time`, `IAU No`, `IAU code`, `LatBeg`, `LonBeg`, `HtBeg`, `LatEnd`, `LonEnd`, `HtEnd`, `Peak AbsMag`, `Vinit`, `Vavg`, `Peak Ht`, `Duration`, `Num stat`. **Excluye** `Participating stations` y `Unique trajectory identifier` | script `WANTED` y `EXCLUDED` |
| Filtro: ventana UTC de la noche local + caja lat/lon, "punto inicial O punto final dentro de la caja" | `meta.filter` del JSON; `docs/handoff.md` línea 115 |
| Tamaños: Japón 426, Norteamérica 1.644, Europa 1.989 meteoros; solo se carga la región abierta (presupuesto 320 KB gzip, `config/size-budget.json`) | `docs/handoff.md` líneas 115 y 162 |

### Gotchas GMN que maneja y que nuestro `docs/ARCHITECTURE.md` no menciona

Comprobado contra nuestros docs con `grep -i "solrange\|solar lon\|Summary generated\|traj_summary_data\|daily/"` (cero coincidencias en ARCHITECTURE/BRIEF/PLAN para los tres primeros).

1. **El archivo diario no es un día UTC.** Se corta por 1° de longitud solar (`traj_summary_20261125_solrange_243.0-244.0.txt`, confirmado con `curl` al listado el 2026-11-26). Por eso Voyascope lee dos archivos para cubrir una noche y filtra por hora. Nuestro U13 / R24 / AE26 ("Last night", `traj_summary_yesterday.txt`) asume "ayer" = un día; el rótulo debería salir del rango real de `Beginning UTC Time` del archivo, no de una fecha supuesta.
2. **Cabecera en dos filas, con columnas `+/-` repetidas.** Su parser arma el nombre uniendo fila 1 y fila 2 y aborta si una columna pedida falta o está duplicada (`parse_header`). Es la defensa contra un cambio de formato; conviene igual en `load/build.py` (U1).
3. **Línea `# Summary generated on …`.** La guarda en `meta.files_generated_utc`. Sirve para decir "datos al corte X" y, junto con `extracted_at_utc`, para frescura. Nuestro BRIEF ya sabe que GMN reescribe el archivo del mes en curso varias veces al día; no registra este sello de generación.
4. **Los conteos cambian al re-bajar** ("GMN rehace los archivos, así que al volver a bajar cambia la cantidad", `docs/handoff.md` línea 115): su respaldo es pegar el JSON al repo, la nuestra es `store-<mes>` en Releases. Coincide con nuestra decisión de ADR-0007.
5. Valores `None`/`nan`/vacío → `null`; código IAU `...` = esporádico. Es el mismo criterio que usaríamos si mostramos nombres de lluvias.
6. Nuestro dato nuevo: `traj_summary_yesterday.txt` vive en `…/traj_summary_data/daily/` (200 OK el 2026-11-26) y **no** en `…/traj_summary_data/` ni `…/data/` (404 en ambos). Si nuestros docs no fijan la ruta completa, conviene fijarla en U13.

## 2. Arquitectura, pruebas y CI

- **Sitio estático**, sin servidor: HTML/JS a mano (sin framework), globe.gl y satellite.js vendorizados. Publicación en **Cloudflare Workers con assets estáticos** (`.github/workflows/deploy.yml`, wrangler-action; claves en Secrets). GitHub Pages quedó solo con una página "nos mudamos" (`pages.yml`, `pages-moved/`). Hay un Worker mínimo `src/lab-worker.js` para una "sala de pruebas" protegida con contraseña (`web/lab/`).
- **Pipeline diario**: existe pero **no es de GMN**: `update-orbits` y `update-horizons` (satélites y distancia de sondas) corren, commitean y disparan `deploy-cloudflare` por `workflow_run` (nota: un push hecho por Actions no dispara otros workflows). Los runs del 2026-11-26 están todos `success`.
- **Pruebas**: `node --test tests/*.test.mjs`, 30 archivos (p. ej. `tests/meteors.test.mjs`, `sky.test.mjs`, `size-budget.test.mjs`). Los tests de meteoros cubren el cálculo de radiante, no el script GMN: **no hay test de `fetch_and_filter.py`** (ni fixture de archivo GMN en `tests/fixtures`).
- **CI `validate.yml`**: `npm ci`, `validate` (JSON Schema de las fichas), `npm test`, tres chequeos `--check` de archivos generados (`sync-web-data`, `build-prompts`, `build-summaries`) y `check-size.mjs` contra `config/size-budget.json`. Sin lint ni type-check.

## 3. Solapamiento con Second Witness

| Pregunta | Resultado | Evidencia |
|---|---|---|
| ¿Muestra estaciones? | `ausente` (se miró): los códigos se omiten a propósito; solo guarda `num_stations` por meteoro | script línea 6-7 y `meta.notes`; `grep -c num_stations web/meteors/index.html` = 0, ni siquiera lo muestra |
| ¿Pares o quién confirma a quién? | `ausente` | no usa `Participating stations` ni trayectorias por par |
| ¿Cobertura o estado de estación? | `ausente` | solo meteoros por ciudad; el "estado" de su `config/status.json` es de satélites QZSS |
| ¿Mismo público/superficie? | Parcial: ambos son páginas estáticas públicas sobre datos GMN CC BY 4.0, pero uno es contemplativo (japonés, público general) y el otro es operativo (coordinadores y operadores de cámaras) | README, `docs/handoff.md` |
| ¿Compite por el criterio del jurado? | No: no es una entrada del hackatón y no usa Relate | contexto de la tarea |

Conclusión: complemento. Un operador podría ver desde Voyascope el cielo de su ciudad y desde Second Witness el estado de su cámara; ninguno cubre lo del otro. Riesgo para nosotros: ninguno. No hay motivo para contactar.

## 4. Ideas para adoptar

La licencia es "All rights reserved": **ninguna línea de código se copia**; solo ideas y lecciones.

| # | Idea | Dónde encaja | Prioridad |
|---|---|---|---|
| I-1 | El rótulo "Last night" sale del rango UTC real del archivo (`Beginning UTC Time` mín/máx) y de `Summary generated on`, no de una fecha supuesta | U13 / R24 / AE26; U4 (datos de página) | **must** (corrige un supuesto, cuesta una línea de texto y un test) |
| I-2 | Parseo de cabecera por nombre con falla ruidosa si falta o se duplica una columna | U1 (loader), tests de `tests/test_load.py` | **should** (verificar primero si `load/build.py` ya lo hace: no se leyó) |
| I-3 | Mostrar siempre "datos al corte X" (sello generado + hora de extracción) en la página y en cada respuesta de MCP | R6 (diario), R11 (36 h sin subida), R16 | **should** |
| I-4 | Texto llano con la cifra al lado: "el rango visible se explica con un dedo sobre MAG" y "6.ª magnitud = límite de cielo oscuro / 4.ª = centro de ciudad" son ejemplos de glosar el número sin reemplazarlo | R18 / criterio Clarity; registro "para dummies" del CLAUDE.md | **should** (aplicar el mismo patrón a "punto de corte", "isla", "segundo testigo") |
| I-5 | Mapa de calor mínimo de cuánto pesa cada archivo y un `size-budget.json` que falla en CI (320 KB gzip para su página GMN) | QA-01 (≤ 10 s) / U12 | **skip** (nuestro presupuesto ya está en QA-01; WASM de 2,5 MB lo hace distinto) |
| I-6 | Presupuesto de peso por grupo en CI como práctica | U12 | **skip** por lo anterior |
| I-7 | Conmutador de idioma: Voyascope es solo japonés (`<html lang="ja">`, sin `hreflang`) | `docs/BRIEF.md` toggles | **skip**: aquí no hay nada que adoptar; el CLAUDE.md del hackatón ya pide EN/ES |
| I-8 | Datos: JSON por región cargado solo bajo demanda | U4 | **skip**: nuestra página ya exporta por país |
| I-9 | Aviso de que la "noche" es parcial y de que GMN reescribe archivos ("el conteo cambia al volver a bajar"): decirlo en la página para no parecer inconsistentes entre dos cargas | R9 (límites) | **should** |

Sobre mapear al BRIEF: no hay R-ID nuevo que proponer, todas las ideas caen en R-IDs ya existentes.

## 5. CLAUDE.md y prompts: cómo está construido

Evidencia: `CLAUDE.md` (86 líneas), `RULES.md`, `prompts/`, `docs/tasks/001..020`, `docs/handoff.md`, `docs/changelog.md`.

- Construido casi entero con **Claude Code** guiado por un dueño con "pocas horas por semana" y varios modelos con roles fijos: ChatGPT ("チャッピー") = investigación de fuentes, Grok = noticias rápidas (solo como disparador, nunca directo a `curation/`), Claude chat = diseño, Claude Code = implementación (`CLAUDE.md`, tabla "AIの役割分担").
- Reglas "de oro" en el CLAUDE.md: no afirmar hechos sin URL de fuente, no cambiar LICENSE/RULES sin permiso, **parar y preguntar ante lo legal** (licencias, términos, derechos, datos personales). Cierre de cada tarea en 3 puntos: lo hecho, lo no hecho con razón, lo que debe decidir el dueño. Un `docs/handoff.md` mantenido para retomar chats (estado, pendientes, trampas) y `docs/tasks/NNN-*.md` numerados, parecido a nuestro BRIEF/PLAN con IDs.
- Detalle útil: el repo se rehízo el 2026-10-04 para limpiar del historial un correo personal e imágenes previas (`CLAUDE.md`). Es un recordatorio de revisar nuestro historial antes de hacerlo público, no una idea de producto.
- Trampas anotadas en `docs/handoff.md` líneas 155-163: `filter: blur()` en SVG no funciona en Safari de iPhone (usar `<filter>`), `globalAlpha` fuera de rango se ignora, los elementos HTML de globe.gl se reutilizan en vez de recrearse. Solo importan si añadimos canvas/SVG propio.

## Límites de esta revisión (`sin evidencia`)

- No se leyó `web/meteors/index.html` completo (1.302 líneas): se verificaron título, noindex, lang, fuente y llamadas por `grep`.
- No se midió el tiempo de respuesta ni el contenido de https://voyascope.org (no se hizo `curl`) ni se vio el video/demo; el estado en vivo es `sin evidencia`.
- No se verificó si la cuenta autora de los mensajes #16537/#16538 de la lista GMN es `mentoce0-gif` (el repo no nombra al operador; el autor se identifica como "151Me" en `CLAUDE.md`).
- No se leyó `load/build.py` de Second Witness para I-2.
- Ninguna credencial expuesta se buscó con herramientas dedicadas; ninguna apareció en los archivos leídos.
