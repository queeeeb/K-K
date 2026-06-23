# Especificación de Diseño — Agente de Provisiones (Summary)

**Proyecto:** Agente Automatizador del *Summary de Provisiones* — P-TRES GROUP, S.A.P.I. de C.V.
**Fecha:** 2026-06-23
**Estado:** Diseño aprobado — pendiente de plan de implementación
**Relación con otros agentes:** Independiente del [Agente P&L](../agente-pl-ptres/README.md). No comparte archivos ni lógica con él.

---

## 1. Resumen ejecutivo (para el cliente)

Hoy, armar la hoja mensual del **Summary de Provisiones** es un trabajo manual: abrir cinco archivos, comparar provisiones contra facturas una por una, decidir cuáles se cancelan y cuáles siguen, copiar montos, convertir monedas y vaciar todo en la hoja del mes.

Este agente hace ese trabajo en minutos. El usuario solo elige el mes, **revisa un resumen** y **aprueba**. El agente:

1. Toma los 5 archivos directamente de Google Drive.
2. **Interpreta** cada archivo aunque las columnas cambien de lugar mes a mes.
3. Hace el cruce de provisiones contra facturas (cancelar / mantener / agregar).
4. Calcula todos los montos con precisión (el sistema calcula, nunca la IA).
5. Muestra un resumen para aprobación — **nada se escribe sin confirmar**.
6. Escribe la hoja del mes en el Summary **sin dañar fórmulas, macros ni el tablero KPI**.
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
| 1000/BO | BACK OFFICE | No aplica por ahora |

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
| B | Cierre (`Provision ` / `Cancelar`) | L | PROVISIÓN MXN |
| C | AÑO | M | usd |
| D | Periodo | N | MXN |
| E | CC (3000/2000/7000) | O | EUR |
| F | Cliente | P | CAD |
| G | Nombre Proyecto | Q | TOTAL MXN |
| H | Proyecto (código) | R | Referencia (facturas) |
| I | Moneda | S | Comentarios |
| J | Provisión (moneda original) | | |

---

## 3. Decisiones de diseño (acordadas con el cliente)

| Decisión | Elección |
|---|---|
| **Modelo de ejecución** | Servicio en un **droplet (DigitalOcean)** expuesto por **API**, consumido por una **interfaz web**. |
| **Disparador** | El usuario elige el mes y procesa desde la interfaz. |
| **Origen de archivos** | El backend **lee de Google Drive** vía cuenta de servicio. |
| **Hoja destino** | El agente **duplica la hoja del mes anterior**, limpia la Sección B y escribe los datos nuevos. |
| **Motor de hojas `.xlsm`** | **Python + `openpyxl` con `keep_vba=True`** (única librería confiable para preservar macros y formato al duplicar). |
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
│   - Botón Confirmar             ├── summary_writer (openpyxl + VBA)    │
│                                 └── audit_log                          │
│   Caddy (HTTPS + sirve el front)                                       │
└────────────────────┬───────────────────────────┬─────────────────────┘
                      │ Google Drive API          │ Anthropic API
                      ▼ (cuenta de servicio)      ▼
              Drive (Summary + 4 fuentes)   Claude Opus 4.8
```

### Stack

- **Backend:** Python + **FastAPI**.
- **Manejo de `.xlsm`:** **`openpyxl`** (`keep_vba=True`).
- **IA:** **Claude Opus 4.8** (`claude-opus-4-8`) vía SDK oficial de Anthropic, con *structured outputs* para JSON garantizado.
- **Google Drive:** API oficial con **cuenta de servicio** (headless, sin OAuth de navegador).
- **Frontend:** SPA ligera (React + Vite).
- **Despliegue:** Docker Compose; **Caddy** como reverse proxy (HTTPS) y para servir el frontend.

---

## 5. Módulos (responsabilidad única)

| Módulo | Qué hace | ¿Usa IA? |
|---|---|---|
| **`drive_client`** | Localiza, descarga y sube los 5 archivos por nombre (cuenta de servicio). | No |
| **`interpreters/`** | Uno por fuente. Pasa a Claude el volcado de la hoja; Claude devuelve **el mapa de estructura** (fila de encabezado, columna del mes, columna de código de proyecto, moneda, STATUS, qué filas son proyectos). | **Sí** |
| **`reconciler`** | Núcleo determinista. Cruza provisiones vs facturas por **código exacto**, clasifica Cancelar / Activa / Nueva, calcula montos (Provisión×T/C, TOTAL MXN, conversión por moneda). | No |
| **`summary_writer`** | `openpyxl` con `keep_vba=True`: duplica la hoja del mes anterior, limpia Sección B, escribe filas 12↓, **nunca toca filas 1–11**. | No |
| **`api`** | FastAPI: `POST /procesar` (Pasos 1–7) y `POST /confirmar` (Pasos 8–9). | No |
| **`audit_log`** | Registra cada fila escrita (valor anterior / nuevo). | No |

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
5. **Reconciliar:** por cada provisión del mes anterior, si su código aparece facturado → `Cancelar` (+ referencia de factura); si no → sigue `Provision`. Detectar provisiones nuevas. **Calcular** todos los montos.
6. **Guardar** el plan de escritura en sesión (token).
7. **Devolver** el **resumen del Paso 7**: canceladas / activas / nuevas + totales del Concentrado + alertas + `token`.

### `POST /confirmar { token }` — Pasos 8 y 9

8. Descargar el Summary, **duplicar la hoja del mes anterior**, limpiar Sección B (con autorización explícita), escribir las filas (existentes primero, nuevas al final), respetar el T/C del mes anterior para las existentes, **sin tocar filas 1–11**.
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
  "activas":    [ { "cc": 3000, "cliente": "...", "proyecto": "...", "monto_mxn": 0 } ],
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
| Discrepancia > 5% entre provisión fuente y Summary anterior | Alertar como anomalía antes de escribir. |

---

## 10. Reglas críticas (invariantes)

1. Nunca modificar hojas de meses anteriores.
2. Nunca tocar las filas 1–11 (tablero KPI, T/C, fórmulas).
3. Siempre confirmar antes de escribir (resumen del Paso 7 obligatorio).
4. Una factura `"Cancelado"` no cuenta como facturada.
5. No asumir monedas ni T/C; si falta, dejar vacío y reportar.
6. Escribir la **provisión del mes**, no el acumulado.
7. No duplicar filas: si el proyecto ya existe, actualizar su monto.
8. Registrar cada fila escrita (valor anterior y nuevo).
9. Preservar macros y formato del `.xlsm`.

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

- Secretos vía variables de entorno: JSON de cuenta de servicio de Google + `ANTHROPIC_API_KEY`. Nunca en el código ni en el repositorio.
- HTTPS mediante Caddy (Let's Encrypt) si se usa dominio.
- La interfaz es de uso interno; se recomienda autenticación básica/contraseña compartida (a definir en el plan).
- El agente solo escribe la Sección B de la hoja del mes en curso.

---

## 13. Fuera de alcance (por ahora)

- Segmento **Back Office (1000/BO)**.
- Edición de hojas de meses anteriores.
- Captura automática de tipos de cambio del tablero KPI (sigue siendo manual).
- Disparo automático por subida de archivo a Drive (posible mejora futura: notificar a la interfaz cuando llegue la Facturación).

---

## 14. Pendientes antes de implementar

1. Recibir los **archivos de muestra reales** (Summary `.xlsm` + 4 fuentes de un mes cerrado) para fijar la estructura del tablero KPI y validar que `openpyxl` preserva macros y formato al duplicar la hoja.
2. Confirmar el **mecanismo de autenticación** de la interfaz.
3. Confirmar la **carpeta/estructura en Drive** donde viven los 5 archivos.
4. Decidir el almacenamiento del **plan de escritura** entre `/procesar` y `/confirmar` (memoria, archivo temporal o Redis).
