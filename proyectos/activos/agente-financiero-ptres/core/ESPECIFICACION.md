# Especificación de Diseño — Contrato `PipelineSpec` (núcleo `core/`)

**Proyecto:** Agente Financiero P-TRES GROUP — núcleo compartido entre pipelines.
**Fecha:** 2026-06-24
**Estado:** Diseño aprobado — pendiente de plan de implementación.
**Relación con otros specs:** Extraído de [`pipelines/summary/ESPECIFICACION.md`](../pipelines/summary/ESPECIFICACION.md) (primer pipeline construido). Define el contrato que también usarán `pipelines/pl/` y `pipelines/cashflow/`.

---

## 1. Problema

Los 3 pipelines (Summary, P&L, Cash Flow) comparten la misma forma de trabajo: leer fuentes de Drive → interpretar con IA → calcular con código determinista → escribir un Excel destino, siempre con aprobación humana antes de escribir. Sin un contrato común, cada pipeline reimplementaría su propio servidor, manejo de sesión y bloqueo por mes.

`PipelineSpec` es la pieza que cada pipeline implementa una sola vez para conectarse al núcleo (`core/`), sin que `core/` necesite conocer la lógica de negocio de ninguno.

---

## 2. El contrato

```
PipelineSpec:
  name        # "summary" | "pl" | "cashflow"
  sources     # lista de patrones de archivo esperados en Drive
  interpret(archivos_crudos) -> estructura_interpretada   # usa IA
  calculate(estructura_interpretada, estado_anterior) -> plan   # determinista
  write(plan, archivo_destino) -> archivo_actualizado     # determinista
```

- **`sources`** — qué archivos busca este pipeline en Drive (nombres/patrones). `core/drive_client` los localiza y descarga; el pipeline no toca la API de Drive directamente.
- **`interpret`** — recibe el contenido crudo de los archivos de `sources` y devuelve solo **estructura** (mapeo de filas/columnas, clasificación), nunca montos calculados. Es la única pieza que llama a Claude.
- **`calculate`** — recibe la estructura interpretada y el estado anterior (ej. hoja del mes pasado), y devuelve el **plan de escritura**: qué se va a escribir, con todos los montos ya calculados por código determinista. Es lo que se le muestra al usuario para aprobar.
- **`write`** — recibe el plan aprobado y el archivo destino, y produce el archivo actualizado. No decide nada, solo ejecuta.

Cada pipeline implementa estas 4 piezas en su propia carpeta (`pipelines/<nombre>/`); `core/` nunca conoce los detalles internos de ninguna.

---

## 3. Orquestación genérica (`core/api`)

La API es la única forma en que la interfaz web habla con cualquier pipeline. Mismo flujo de dos fases para los 3:

**`POST /procesar/{pipeline}`**
1. Buscar el `PipelineSpec` registrado con ese `name`.
2. `core/lock` — verificar que no haya otro `/procesar` activo para ese mes y ese pipeline; si lo hay, rechazar y avisar a ambos usuarios.
3. `core/drive_client` — descargar los archivos de `sources`.
4. Llamar `interpret(archivos_crudos)`.
5. Llamar `calculate(estructura_interpretada, estado_anterior)` → `plan`.
6. Guardar el `plan` en sesión (token) junto con el bloqueo del mes.
7. Responder al frontend: resumen del plan + `token`.

**`POST /confirmar/{pipeline}`**
1. Recuperar el `plan` con el `token`.
2. Llamar `write(plan, archivo_destino)`.
3. `core/drive_client` — subir el archivo actualizado.
4. `core/audit_log` — registrar lo escrito (valor anterior / nuevo).
5. Liberar el `lock` del mes.
6. Responder con el reporte final.

**`POST /rechazar/{pipeline}`** — invalida el token y libera el `lock` sin llamar `write` ni tocar Drive (igual que ya existe para Summary).

---

## 4. Qué vive en `core/` vs en cada pipeline

| Pieza | Vive en | Por qué |
|---|---|---|
| `drive_client` | `core/` | Localizar/descargar/subir archivos es igual para los 3 — solo cambian los nombres de archivo (`sources`). |
| `lock` | `core/` | Bloqueo por mes+pipeline es la misma lógica para los 3. |
| `audit_log` | `core/` | Registrar fila anterior/nueva es el mismo formato para los 3. |
| `api` (router genérico) | `core/` | Mismas 3 rutas para los 3 pipelines; el `{pipeline}` en la URL decide qué `PipelineSpec` usar. |
| `sources`, `interpret`, `calculate`, `write` | `pipelines/<nombre>/` | Lógica de negocio específica de cada entregable — distinta cantidad de fuentes, distinta forma de interpretar, distinto cálculo. |

`pipelines/summary/` ya tiene esta lógica specced en detalle (`interpreters/`, `reconciler`, `summary_writer` de la sección 5 de su spec) — al implementar el contrato, esos 3 módulos se renombran/agrupan para exponer exactamente `interpret`, `calculate` y `write`.

---

## 5. Pendientes antes de implementar

Comparten los mismos pendientes ya documentados en `pipelines/summary/ESPECIFICACION.md` sección 14 (autenticación de la interfaz, estructura en Drive, almacenamiento del plan de escritura) — se resuelven una sola vez aquí en `core/`, no por pipeline.

1. Formato exacto del `plan` que devuelve `calculate` — ¿estructura genérica única para los 3 pipelines, o cada pipeline define su propio shape de `plan` y el frontend lo renderiza según `name`? (Summary ya tiene su forma en la sección 8 de su spec — `canceladas/activas/nuevas/totales/alertas`; falta confirmar si P&L y Cash Flow caben en ese mismo shape o necesitan uno distinto.)
2. Mecanismo de registro de pipelines en `core/api` (ej. diccionario `{"summary": SummarySpec(), ...}` cargado al iniciar el servicio).
3. Almacenamiento del `plan` + `lock` entre `/procesar` y `/confirmar` (memoria, archivo temporal o Redis) — pendiente de sección 14 del spec de Summary, aplica igual aquí.
