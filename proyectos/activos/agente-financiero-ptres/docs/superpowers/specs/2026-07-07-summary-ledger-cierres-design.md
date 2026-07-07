# Diseño — Summary como ledger, cierres cruzados y KPI desde Facturación

**Fecha:** 2026-07-07
**Pipeline:** `summary`
**Origen:** P3 corrigió la lógica de reconciliación. El Summary no es "una fila por proyecto que se actualiza"; es un **ledger** donde cada provisión mensual es su propia fila y se cierra individualmente cuando se factura.

## Contexto y hallazgo que motiva el cambio

Validado contra el Summary real de Mayo 2026 (`2026_Summary provision PRUEBAS AUTOMATIZACION.xlsm`, hoja `2026_May`): 131 filas de datos, 67 códigos únicos, 40 códigos con más de una fila. Ejemplo `19gmx7000.3836`: filas de Enero, Febrero, Marzo, Abril y Mayo; cuando se factura un mes, **esa** fila pasa a `Cierre=Cancelar` y el remanente se re-provisiona como fila nueva (Marzo aparece como `Cancelar` y `Provision` en la misma hoja). Existen incluso 3 filas del mismo código en el mismo mes.

El modelo anterior (`reconciliar()` actualizaba el monto de la fila "activa" del código) es incorrecto de raíz. Se reemplaza por el modelo de ledger.

## Regla de negocio (confirmada con P3)

1. **Se mantienen:** toda fila con periodo de un mes anterior y estatus distinto de `Cancelar` se conserva **intacta** — monto, periodo, año, T/C, todo. No se busca su monto en las fuentes ni se recalcula.
2. **Nuevas:** toda provisión que reporten las fuentes este mes se escribe como **fila nueva** con `Periodo`/`Año` del mes en curso, aunque el código ya exista en el ledger.
3. **Cierres:** cuando una provisión se factura, la fila del `(código, periodo)` correspondiente se marca `Cierre=Cancelar`. Los cierres parciales ("se partió marzo") no generan estado parcial: la fila del mes se cancela completa y el remanente reaparece como fila nueva por el camino normal.

## Arquitectura — qué cambia y qué no

**No cambia:** contrato `PipelineSpec`, flujo `/procesar` → revisión → `/confirmar`/`/rechazar`, `core/` completo, auth JWT, lock, uploads.

**Cambia dentro de `pipelines/summary/`:** `extract.py`, `calculate.py`, `write.py`, `spec.py`, un intérprete nuevo de notas de cierre, y `frontend/Resumen.jsx`.

---

## Sección 1 — Cierre cruzado (Facturación + notas DS)

Dos señales, cada una produce pares `(código, periodo_a_cerrar)`:

**Señal A — Facturación (determinista).** Hoja `Detalle` del archivo de Facturación del mes. Por cada factura: extraer el prefijo del código de proyecto (columna `Proyecto`, formato código+cliente+descripción con guión) y leer la columna **`Periodo`** (el mes de provisión que la factura cubre — NO `Fecha de factura`, regla confirmada con P3).

**Señal B — Notas de celda de DS (IA).** Archivo DS, bloque del mes en curso, columna `NUM.FACTURA`. La nota de celda es texto libre de captura manual (Estela Flores) con formatos inconsistentes: `DIC25`, `ENE26 3,899,741.57`, `feb26`, `ago` sin año, `se partió marzo`. Se manda a Claude junto con el código de la fila y el año del bloque como contexto; devuelve la lista de meses que la factura cubre, normalizados. Solo se le manda la nota y el código — nunca montos globales del archivo.

**Cruce — se cierra la unión, se alerta la asimetría:**
- Par en ambas señales → se cierra sin ruido.
- Par en una sola señal → **se cierra igual**, con alerta indicando el origen único (`solo Facturación` / `solo Notas DS`). Ninguna señal es completa por diseño de P3: Facturación no cubre los folios de Consulting; las notas dependen de captura manual. Exigir intersección dejaría cierres reales sin aplicar.
- Par que apunta a una fila inexistente en el ledger o ya `Cancelar` → alerta, no se toca nada.
- Nota ilegible/ambigua (Claude no extrae meses con confianza) → alerta con el texto crudo, sin cerrar.
- Monto de la nota no cuadra con la fila que se cancela → alerta informativa, se cancela igual (la partición reaparece como fila nueva).

Todos los cierres pasan por la pantalla de Resumen antes de escribirse.

## Sección 2 — Mantener histórico + filas nuevas

**`extract.py` (nuevo contrato):** lee el **ledger vivo** = todas las filas de la hoja del mes anterior (`2026_Abr` al procesar Mayo) cuya columna `Cierre` (normalizada con trim) **no** sea `Cancelar`. Cada fila se conserva con todos sus campos: Año, Periodo, CC, Cliente, Nombre Proyecto, Proyecto, Moneda, Provisión, T/C, PROVISON MXN, usd/MXN/EUR/CAD, TOTAL MXN, Referencia, Comentarios. No se recorren las 11 hojas históricas: la hoja del mes anterior ya arrastra todo lo vivo. `historial.py` (ya existe) sigue solo para marcar reaperturas y "código nunca visto".

**`reconciliar()` — tres grupos, sin `activas`:**
- `mantenidas`: filas vivas del histórico, copiadas sin modificar.
- `nuevas`: provisiones de las fuentes de este mes → fila nueva, `Periodo`/`Año` = mes en curso, marca `codigo_nuevo` si nunca se vio en ninguna hoja. Se genera aunque el código ya exista en `mantenidas`.
- `cierres`: pares `(código, periodo)` de la Sección 1 → localizan la fila exacta en `mantenidas` y le ponen `Cierre=Cancelar`.

**Alerta >20% / $50k MXN:** se conserva pero reinterpretada — compara la fila nueva contra la última fila viva del mismo código, como dato **informativo** en el Resumen. No modifica montos.

**Shape del plan (entre `/procesar` y `/confirmar`):**
```
resumen: { mantenidas: [...], nuevas: [...], cierres: [...], alertas: [...] }
detalle: { filas: [ [A..S por fila] ] }   # mantenidas-vivas + cerradas + nuevas
```

## Sección 3 — `write.py` y tablero KPI

**Filas de datos (13 en adelante):** se escriben desde `detalle.filas` en orden: mantenidas-vivas (intactas) → cerradas (`Cierre=Cancelar`, columnas M-Q usd/MXN/EUR/CAD/TOTAL MXN llenas — solo se llenan al cancelar) → nuevas (Periodo/Año del mes, monto convertido con T/C del tablero). Desaparece el branch de "actualizar monto de activa".

**Tablero KPI (filas 1-11):** columnas I=3000, J=2000, K=7000. Mapeo de unidad confirmado: **3000=Consulting, 2000=Engineering, 7000=Digital Services**.

- **Filas 2 y 4** (`Provisiones`, `C.Provisiones` por segmento): fórmulas `SUMIF`/`SUMIFS` dinámicas sobre el rango real `E13:última_fila`, ya implementadas en `_actualizar_formulas_kpi`. Solo confirmar que el último renglón se calcula sobre el total real escrito (ahora hay más filas por el ledger completo).
- **Filas 3 y 5** (`Facturacion`, `C.Facturacion`): **valores que vienen de un archivo externo**, por eso nunca tuvieron fórmula. Se leen de la hoja **`Concentrado`** del archivo de Facturación:
  - Fila 3 `Facturacion` = "Facturado bruto" por unidad (Consulting → I3, Engineering → J3, Digital Services → K3).
  - Fila 5 `C.Facturacion` = "Canceladas" por unidad.
  - Verificado: I3=6,050,968.44 = Consulting bruto; J3=1,784,778.64 = Engineering bruto; K3=5,871,693.18 = DS bruto.
  - Si `Concentrado` no existe o su estructura no coincide → **alerta y se dejan en blanco**. Nunca heredar el valor del mes anterior (ese era el bug: valores viejos hardcodeados).
- **Fila 11 `Prov. Antiguas por facturar`:** suma de `PROVISON MXN` (columna L) de las filas en estatus Provisión con periodo de meses anteriores (no el mes en curso), agrupada por unidad de negocio.
  - **Validación parcial:** la regla reproduce **DS (7000) exacto** (1,860,774.24). Pero **NO** reproduce Consulting ni Engineering en el archivo real:
    - Consulting (3000): regla da 5,336,556.19 vs 4,149,324.83 real → la fórmula manual excluye ~1,187,231 de renglones que sí cumplen la condición.
    - Engineering (2000): regla da 279,916.80 vs 0 real → `J11` está puesto en 0 a mano.
  - **Pendiente con P3:** confirmar qué renglones excluye Consulting y por qué Engineering va en 0. Hasta resolverlo, la fila 11 se calcula con la regla base y se marca en alertas como "valor calculado, sujeto a confirmación de criterio de exclusión".
- **Filas 6-8** (T/C USD/EUR/CAD, capturadas a mano): se heredan del mes anterior tal cual (comportamiento ya existente). Gap conocido: si nadie las actualiza, se usa el T/C viejo para conversiones — pendiente ya documentado.

## Sección 4 — Frontend `Resumen.jsx`

Desaparece la tabla "Activas (monto anterior vs nuevo)". Layout nuevo:
- **Se mantienen:** colapsable, cuenta grande, tabla oculta por defecto (auditoría).
- **Nuevas del mes:** tabla visible; conserva la tarjeta "Códigos nuevos sin nombre de cliente" (Guardar y continuar / Continuar sin nombrar). Pill "Reapertura" si el código estuvo cancelado antes.
- **Cierres detectados:** tabla visible con código, periodo cerrado y badge de origen (`Facturación` / `Notas DS` / `Ambas`).
- **Alertas:** cierres unilaterales, notas ilegibles, cierres a fila inexistente, montos de partición que no cuadran, T/C faltante, variación >20%/$50k, `Concentrado` ausente, fila 11 sujeta a confirmación.

Contadores del encabezado: "Se mantienen / Nuevas / Cierres / Alertas". `ResumenPL.jsx` y `api.js`/`nombrar` no se tocan.

## Testing

- Fixtures sintéticos (regenerados por `conftest.py`, no se commitean spreadsheets).
- Ledger: fila viva del mes anterior se copia intacta; código repetido genera fila nueva sin tocar la vieja.
- Cierre por `(código, periodo)`: cierra la fila correcta, no todas las del código.
- Cruce: par en ambas señales sin alerta; par unilateral con alerta de origen; par a fila inexistente sin escritura + alerta.
- Notas DS: nota multi-mes → múltiples pares; nota ilegible → alerta sin cierre.
- KPI: filas 3/5 pobladas desde `Concentrado`; `Concentrado` ausente → blanco + alerta; fila 11 calculada por unidad.

## Fuera de alcance

- Reproducir la curación manual exacta de la fila 11 en Consulting/Engineering (bloqueado por P3).
- Cash Flow (sin archivo de referencia).
- Actualización automática de T/C de las filas 6-8.
- Despliegue DigitalOcean.
