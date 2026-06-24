# Especificación de Diseño — Agente de Provisiones (Summary)

**Proyecto:** Agente Automatizador del *Summary de Provisiones* — P-TRES GROUP, S.A.P.I. de C.V.
**Fecha:** 2026-06-23
**Estado:** Diseño aprobado — pendiente de plan de implementación
**Relación con otros agentes:** Independiente del [Agente P&L](../agente-pl-ptres/README.md). No comparte archivos ni lógica con él.

---

## 1. Resumen ejecutivo (para el cliente)

Hoy, armar la hoja mensual del **Summary de Provisiones** es un trabajo manual: abrir cinco archivos, comparar provisiones contra facturas una por una, decidir cuáles se cancelan y cuáles siguen, copiar montos, convertir monedas y vaciar todo en la hoja del mes. El `.xlsm` **no tiene macros** — no hay ninguna automatización previa; todo el proceso se hace a mano hoy. Por eso se necesita un agente con IA: no solo para adaptarse a columnas que cambian de mes a mes, sino para automatizar de cero un proceso que hasta ahora es enteramente manual.

Este agente hace ese trabajo en minutos. El usuario solo elige el mes, **revisa un resumen** y **aprueba**. El agente:

1. Toma los 5 archivos directamente de Google Drive.
2. **Interpreta** cada archivo aunque las columnas cambien de lugar mes a mes.
3. Hace el cruce de provisiones contra facturas (cancelar / mantener / agregar).
4. Calcula todos los montos con precisión (el sistema calcula, nunca la IA).
5. Muestra un resumen para aprobación — **nada se escribe sin confirmar**.
6. Escribe la hoja del mes en el Summary **sin dañar fórmulas ni el tablero KPI**.
7. Sube el archivo actualizado a Drive y entrega un reporte.

> Convierte un trabajo de horas en una revisión de minutos. La decisión final siempre es del usuario.

---

## 2. Contexto de negocio

El **Summary** es un archivo acumulativo `.xlsm` con una hoja por mes (`2026_Ene`, `2026_Feb`, …). Cada hoja es una **foto estática del estado de provisiones al cierre de ese mes**. No se modifican hojas de meses anteriores — cada mes es un nuevo corte.

Segmentos activos:

| CC | Segmento | Archivo fuente de provisiones |
|---|---|---|
| 3000 | CONSULTING (CONS OPS) | `PROVISIONES_Overview_Projects_YYYY_MMM.xlsx` |
| 2000 | ENGINEERING (ING) | `Provisiones_ES_MMMYY.xlsx` |
| 7000 | DIGITAL SOLUTIONS (DS) | `FORMATO_PROVISIONES_P3_DS_YYYY_MMMYY.xlsx` |
| 1000/BO | BACK OFFICE | No aplica — BO es el área administrativa, solo genera gastos, nunca ingresos. No habrá archivo fuente de provisiones para este segmento (confirmado por el cliente). |

### Archivos que maneja el agente

**Destino:** `2026_Summary_provision.xlsm` (en Google Drive).

**Fuentes (en Google Drive):**
1. **Facturación** — `2026_MM_Facturacion_sem_*.xlsx` (hojas `Detalle` y `Concentrado`).
2. **Provisiones DS** — `FORMATO_PROVISIONES_P3_DS_YYYY_MMMYY.xlsx` (hoja `2026`).
3. **Provisiones Engineering** — `Provisiones_ES_MMMYY.xlsx` (hoja `Hoja1`).
4. **Overview Consulting** — `PROVISIONES_Overview_Projects_YYYY_MMM.xlsx` (una hoja por mes, ej. `2026.05`).

### Estructura del Summary (destino)

- **Sección A — Tablero KPI (filas 1–11):** fórmulas de consolidación y tipos de cambio capturados manualmente. **El agente nunca toca estas filas.**
- **Sección B — Tabla de provisiones (fila 12 en adelante):** la única sección que el agente escribe. Columnas:

| Col | Campo | Col | Campo |
|---|---|---|---|
| A | Cotización | K | T/C Provisión |
| B | Cierre (`Provision` / `Cancelar`, valores con espacios inconsistentes — normalizar con trim antes de comparar) | L | PROVISIÓN MXN |
| C | AÑO | M | usd |
| D | Periodo | N | MXN |
| E | CC (3000/2000/7000) | O | EUR |
| F | Cliente | P | CAD |
| G | Nombre Proyecto | Q | TOTAL MXN |
| H | Proyecto (código) | R | Referencia (facturas) |
| I | Moneda | S | Comentarios |
| J | Provisión (moneda original) | | |

> **Nota:** en la práctica aparecen filas sueltas dentro de la Sección B con texto libre en la columna G (notas tipo "Se facturó junto con Mayo") y sin datos en el resto de columnas. El parser debe identificarlas y excluirlas — no son filas de provisión.

---

## 3. Decisiones de diseño (acordadas con el cliente)

| Decisión | Elección |
|---|---|
| **Modelo de ejecución** | Servicio en un **droplet (DigitalOcean)** expuesto por **API**, consumido por una **interfaz web**. |
| **Disparador** | El usuario elige el mes y procesa desde la interfaz. |
| **Origen de archivos** | El backend **lee de Google Drive** vía cuenta de servicio. |
| **Hoja destino** | El agente **duplica la hoja del mes anterior**, limpia la Sección B y escribe los datos nuevos. |
| **Motor de hojas `.xlsm`** | **Python + `openpyxl`** (el archivo no tiene macros — no se requiere `keep_vba=True`; solo se preserva formato al duplicar). |
| **Rol de la IA** | **La IA interpreta, el código calcula.** Claude Opus 4.8 resuelve lo difuso (mapeo de estructura, clasificación, moneda); Python hace toda la aritmética. |
| **Archivos de muestra** | El cliente comparte el Summary y los 4 fuentes de un mes cerrado para fijar la estructura real. |

---

## 4. Arquitectura

```
┌──────────────── Droplet DigitalOcean (Docker Compose) ────────────────┐
│                                                                        │
│   [ Frontend SPA ]  ──HTTP──▶  [ Backend FastAPI (Python) ]           │
│   React + Vite                  ├── drive_client   (Google Drive API) │
│   - Elegir mes                  ├── interpreters/  (Claude Opus 4.8)   │
│   - Ver resumen Paso 7          ├── reconciler     (cálculo determin.) │
│   - Botón Confirmar/Rechazar    ├── summary_writer (openpyxl)          │
│                                 └── audit_log                          │
│   Caddy (HTTPS + sirve el front)                                       │
└────────────────────┬───────────────────────────┬─────────────────────┘
                      │ Google Drive API          │ Anthropic API
                      ▼ (cuenta de servicio)      ▼
              Drive (Summary + 4 fuentes)   Claude Opus 4.8
```

### Stack

- **Backend:** Python + **FastAPI**.
- **Manejo de `.xlsm`:** **`openpyxl`** (sin macros que preservar — solo formato).
- **IA:** **Claude Opus 4.8** (`claude-opus-4-8`) vía SDK oficial de Anthropic, con *structured outputs* para JSON garantizado.
- **Google Drive:** API oficial con **cuenta de servicio** (headless, sin OAuth de navegador).
- **Frontend:** SPA ligera (React + Vite).
- **Despliegue:** Docker Compose; **Caddy** como reverse proxy (HTTPS) y para servir el frontend.

---

## 5. Módulos (responsabilidad única)

| Módulo | Qué hace | ¿Usa IA? |
|---|---|---|
| **`drive_client`** | Localiza, descarga y sube los 5 archivos por nombre (cuenta de servicio). | No |
| **`interpreters/`** | Uno por fuente (DS, Engineering, Consulting, Facturación). Pasa a Claude el volcado de la hoja; Claude devuelve **el mapa de estructura** (fila de encabezado, columna del mes, columna de código de proyecto, moneda, STATUS, qué filas son proyectos) **y el patrón de extracción del código de proyecto**, distinto en cada fuente: limpio en DS, con guión (`código-cliente-descripción`) en Engineering y Facturación, multilínea (`código\ncliente\ndescripción`) en Consulting Overview — además, en Overview cada proyecto ocupa un bloque de varias filas (una por consultor), con el monto final como suma de varias celdas "Total honorarios" dentro del bloque. **En DS, cada mes es un bloque de 6 sub-columnas (PROVISION/NUM.FACTURA/MONTO/Diferencia+/Diferencia-/Acumulados); el valor que va al Summary es `PROVISION`, validado contra el cierre real de diciembre 2025 (6 proyectos, coincide exacto) — `MONTO` es lo facturado ese mes, no se usa aquí.** | **Sí** |
| **`reconciler`** | Núcleo determinista. Cruza provisiones vs facturas por **código de proyecto extraído** (no comparación literal de celda — cada fuente requiere su propio parser de código, ver `interpreters/`), clasifica Cancelar / Activa / Nueva, calcula montos (Provisión×T/C, TOTAL MXN, conversión por moneda). | No |
| **`summary_writer`** | `openpyxl`: duplica la hoja del mes anterior, limpia Sección B, escribe filas 12↓, **nunca toca filas 1–11**. | No |
| **`api`** | FastAPI: `POST /procesar` (Pasos 1–7) y `POST /confirmar` (Pasos 8–9). | No |
| **`audit_log`** | Registra cada fila escrita (valor anterior / nuevo). | No |
| **`lock`** | Bloquea por mes: si ya hay un `/procesar` activo (sin confirmar/rechazar) para ese mes, rechaza el segundo intento avisando quién lo tiene abierto, y notifica al primer usuario que alguien más intentó entrar. Se libera al confirmar, rechazar o expirar el token. | No |

---

## 6. El límite IA / código (criterio crítico para finanzas)

**Claude nunca devuelve montos calculados.** Recibe el contenido de una hoja y devuelve únicamente **estructura**, por ejemplo:

> "El encabezado está en la fila 4; la columna de Mayo es la H; el código de proyecto está en la columna B; la moneda en la columna I; estas filas son proyectos con STATUS = PROVISION."

Luego **Python lee los valores directamente de esas celdas** y ejecuta toda la aritmética.

**Consecuencia:** un error de la IA puede mover un *mapeo* (visible y corregible en el resumen del Paso 7), pero **jamás inventa un número**. Los totales financieros dependen 100% del código determinista.

---

## 7. Flujo de ejecución (dos pasos)

### `POST /procesar { mes }` — Pasos 1 a 7

1. **Localizar** los 5 archivos en Drive. Si falta alguno → **detener y reportar** cuál falta.
2. **Leer la hoja del mes anterior** del Summary → lista de provisiones activas (solo filas con `Cierre = "Provision"`; las `"Cancelar"` no se arrastran).
3. **Interpretar Facturación** (`Detalle` + `Concentrado`): índice de proyectos facturados este mes (facturas con estado `"Sin pagar"` o `"Pagado"`; **las `"Cancelado"` no cuentan**) y totales por segmento.
4. **Interpretar** las 3 fuentes de provisiones del mes (DS, Engineering, Consulting; en Consulting solo `STATUS = PROVISION`).
5. **Reconciliar:** por cada provisión del mes anterior, si su código (extraído según el patrón de su fuente) aparece facturado → cambiar su estatus a `Cancelar` en la misma fila (+ referencia de factura) — **confirmado por el cliente: detección por número de proyecto, no se agregan filas nuevas para la cancelación**; si no → sigue `Provision`. Detectar provisiones nuevas. **Calcular** todos los montos.
6. **Guardar** el plan de escritura en sesión (token).
7. **Devolver** el **resumen del Paso 7**: canceladas / activas / nuevas + totales del Concentrado + alertas + `token`.

### `POST /rechazar { token }` — descarta el plan

Botón "Rechazar" en la interfaz, junto al de "Confirmar". Invalida el token de sesión sin tocar el Summary — ningún archivo se descarga, modifica ni sube. Le da al usuario la certeza visible de que nada cambió si decide no aprobar el resumen del Paso 7.

### `POST /confirmar { token }` — Pasos 8 y 9

8. Descargar el Summary, **duplicar la hoja del mes anterior**, limpiar Sección B (con autorización explícita), escribir las filas (existentes primero, nuevas al final), respetar el T/C original para las existentes (no se revalúa); para las **nuevas**, usar el T/C del tablero KPI de la hoja del mes en curso (filas 6–8, capturado manualmente por el usuario antes de procesar — validado contra el cierre de diciembre 2025: el T/C de las provisiones nuevas de ese mes coincide exacto con el del tablero KPI, no con ningún T/C de las fuentes). **Sin tocar filas 1–11**.
9. Subir el archivo a Drive, registrar el log y **devolver el reporte final** (filas canceladas / provisiones / nuevas / total + pendientes manuales).

---

## 8. Contrato de la API

### `POST /procesar`
**Request:** `{ "mes": "2026_May" }`
**Response (200):**
```json
{
  "token": "uuid-de-sesion",
  "mes": "2026_May",
  "canceladas": [ { "cc": 3000, "cliente": "...", "proyecto": "...", "monto_mxn": 0, "referencia": "C-2026-00109" } ],
  "activas":    [ { "cc": 3000, "cliente": "...", "proyecto": "...", "monto_mxn_anterior": 0, "monto_mxn": 0 } ],
  "nuevas":     [ { "cc": 3000, "cliente": "...", "proyecto": "...", "monto_mxn": 0 } ],
  "totales": {
    "CONSULTING":  { "facturacion": 0, "canceladas": 0, "total": 0 },
    "DS":          { "facturacion": 0, "canceladas": 0, "total": 0 },
    "ENGINEERING": { "facturacion": 0, "canceladas": 0, "total": 0 }
  },
  "alertas": [ "string" ],
  "total_filas": 0
}
```

### `POST /confirmar`
**Request:** `{ "token": "uuid-de-sesion", "limpiar_seccion_b": true }`
**Response (200):**
```json
{
  "archivo": "2026_Summary_provision.xlsm",
  "hoja": "2026_May",
  "filas": { "canceladas": 0, "provisiones": 0, "nuevas": 0, "total": 0 },
  "pendientes_manuales": [ "Tipos de cambio USD/EUR/CAD (filas 6–8 del tablero KPI)" ]
}
```

---

## 9. Manejo de errores

| Situación | Acción |
|---|---|
| Archivo fuente no encontrado en Drive | Detener y reportar cuál falta. |
| Proyecto en fuente sin código de proyecto | Reportar en alertas; no escribir sin confirmación. |
| Hoja del mes anterior no existe | Preguntar si se construye desde cero. |
| Hoja del mes a procesar ya tiene datos | Preguntar si sobreescribir o agregar. |
| Factura encontrada pero estado `"Cancelado"` | Mantener `"Provision"` — no cancelar. |
| Moneda sin T/C disponible | Dejar celda T/C vacía y reportar en alertas. |
| Fuente sin columna de moneda (ej. Engineering) | No asumir moneda — reportar en alertas y pedir confirmación manual. |
| Header de mes con año inconsistente (ej. DS: meses Jul-Dic etiquetados "2025" siendo en realidad de 2026) | Matchear el bloque por **nombre de mes**, nunca por el año del header. |
| Discrepancia entre provisión fuente y Summary anterior | **Umbral fijo de 5% descartado** — validado contra datos reales de DS (Ene-May 2026): variaciones normales de -76% a +320% mes a mes por proyectos que arrancan/terminan. Un 5% fijo generaría alerta en casi toda fila con movimiento real. Pendiente definir con el cliente un criterio que no sea ruido (ver sección 14). |
| Otro usuario ya tiene un `/procesar` activo (sin confirmar/rechazar) para el mismo mes | **Bloquear** el segundo `/procesar` con mensaje claro de quién lo tiene abierto, **y avisar al primer usuario** que alguien más intentó entrar a ese mes — para que ambos lo tengan en cuenta antes de confirmar. |

---

## 10. Reglas críticas (invariantes)

1. Nunca modificar hojas de meses anteriores.
2. Nunca tocar las filas 1–11 (tablero KPI, T/C, fórmulas).
3. Siempre confirmar antes de escribir (resumen del Paso 7 obligatorio).
4. Una factura `"Cancelado"` no cuenta como facturada.
5. No asumir monedas ni T/C; si falta, dejar vacío y reportar.
6. Escribir la **provisión del mes**, no el acumulado.
7. No duplicar filas: si el proyecto ya existe, actualizar su monto — y mostrar monto anterior vs. nuevo en el resumen del Paso 7 para que el usuario apruebe el cambio a sabiendas.
8. Registrar cada fila escrita (valor anterior y nuevo).
9. Preservar formato del `.xlsm` (no tiene macros que preservar).
10. **Confidencialidad por defecto:** nunca subir, pegar ni compartir datos reales de P-TRES GROUP en servicios externos, repositorios o herramientas de terceros (ver sección 12).

---

## 11. Servicios, costos y dependencias

| Servicio | Para qué | Costo aprox. | Tipo |
|---|---|---|---|
| Droplet DigitalOcean | Servidor (backend + frontend) | ~$6–12 USD/mes | Fijo mensual |
| API de Claude (Anthropic) | Interpretación de archivos (~4–5 llamadas/corrida, mensual) | ~$1–5 USD/mes | Por uso |
| Dominio (opcional) | HTTPS con dominio propio | ~$1 USD/mes | Opcional |
| Google Drive API | Acceso a los archivos | **Gratis** | — |
| FastAPI / openpyxl / React / Vite / Caddy / Docker | Software base | **Gratis / open-source** | — |

**Total realista: ~$10–20 USD/mes.** Cuentas nuevas indispensables: **Anthropic** (API key) y **DigitalOcean**; cuenta de servicio de **Google Cloud** (gratis).

---

## 12. Seguridad

- **Confidencialidad de datos — regla de trabajo permanente:** ningún dato real de P-TRES GROUP (montos, clientes, proyectos, archivos completos) se sube a herramientas, servicios o repositorios externos al equipo de trabajo, ni se incluye en el código o en commits de este repositorio. Toda revisión, prueba o ejemplo se hace con archivos que quedan en máquinas locales del equipo. Esta regla aplica desde que se hace `git pull`/`git clone` de este repo en adelante — no requiere recordatorio en cada sesión.
- Secretos vía variables de entorno: JSON de cuenta de servicio de Google + `ANTHROPIC_API_KEY`. Nunca en el código ni en el repositorio.
- HTTPS mediante Caddy (Let's Encrypt) si se usa dominio.
- La interfaz es de uso interno; se recomienda autenticación básica/contraseña compartida (a definir en el plan).
- El agente solo escribe la Sección B de la hoja del mes en curso.

---

## 13. Fuera de alcance

- Segmento **Back Office (1000/BO)** — permanente, no "por ahora": BO es el área administrativa, solo genera gastos, nunca ingresos, no tendrá archivo fuente de provisiones.
- Edición de hojas de meses anteriores.
- Captura automática de tipos de cambio del tablero KPI (sigue siendo manual).
- Disparo automático por subida de archivo a Drive (posible mejora futura: notificar a la interfaz cuando llegue la Facturación).

## 13.1 Mejoras opcionales (no bloqueantes)

- **Columna de Acumulados (saldo pendiente) en el Summary**: el cliente confirmó que hoy el Summary solo toma la Provisión del mes actual de cada fuente (no el acumulado, coincide con el invariante 6), pero ofreció que se agregue una columna con el Acumulados si es viable. No es requisito — evaluar en el plan de implementación si se agrega sin afectar la Sección B actual.

---

## 14. Pendientes antes de implementar

1. ~~Recibir los archivos de muestra reales~~ — recibidos y revisados (Summary + Facturación + DS + Engineering + Consulting Overview de Mayo 2026). Estructura del tablero KPI confirmada; `openpyxl` sin `keep_vba` es suficiente (no hay macros).
2. ~~Mecanismo de detección de cancelación~~ — confirmado por el cliente: por número de proyecto, cambiando el estatus en la misma fila (no se agregan filas nuevas).
3. ~~¿Existe archivo de Back Office?~~ — confirmado que no, y no existirá (ver sección 13).
4. Confirmar el **mecanismo de autenticación** de la interfaz.
5. Confirmar la **carpeta/estructura en Drive** donde viven los 5 archivos.
6. Decidir el almacenamiento del **plan de escritura** entre `/procesar` y `/confirmar` (memoria, archivo temporal o Redis) — debe poder guardar también el bloqueo por mes del módulo `lock` (sección 5), así que conviene resolver ambos con el mismo mecanismo.
7. **Confirmar con el cliente la moneda de las provisiones de Engineering** — el archivo fuente (`Provisiones_ES_*.xlsx`) no tiene columna de moneda.
8. **Provisiones "reabiertas":** el diseño actual solo compara contra la hoja del mes anterior (paso 2). Si un proyecto se canceló hace varios meses y vuelve a aparecer con `STATUS/PROVISION` en una fuente, hoy se trataría como provisión "nueva" sin indicar que ya tuvo historial. Pendiente de hablar con el cliente: ¿tratarlo como nueva tal cual, o el agente debe buscar en hojas anteriores y avisar que es una reapertura?
9. **Criterio de alerta por discrepancia de monto:** el umbral fijo de 5% queda descartado (genera ruido — ver sección 9). Pendiente definir con el cliente un criterio razonable, ej. combinar % alto con un mínimo en monto absoluto, o no alertar y confiar en el delta anterior/nuevo que ya se muestra en el resumen del Paso 7.
10. ~~Validar que duplicar la hoja preserva el tablero KPI (Sección A) correctamente~~ — confirmado por Luis (2026-06-24): todas las fórmulas del tablero KPI son sumas (`SUM`/`SUMIF`) que referencian su propia hoja, no hojas cruzadas por nombre. `wb.copy_worksheet()` (implementación en `write.py`) las duplica intactas y Excel las recalcula solas contra los datos nuevos al abrir el archivo — no hay riesgo de que una fórmula se quede apuntando al mes anterior.
    - **Gap residual sin resolver:** los valores escritos a mano en el tablero KPI (ej. el T/C de filas 6-8, ver punto 8 de la sección 7) se duplican tal cual del mes anterior junto con las fórmulas. Si nadie actualiza ese T/C en la hoja nueva antes de confirmar, el agente usaría el T/C del mes pasado para las provisiones nuevas. Falta decidir si el flujo le pide ese valor al usuario explícitamente (input en `/procesar`) o si se documenta como paso manual previo obligatorio.
