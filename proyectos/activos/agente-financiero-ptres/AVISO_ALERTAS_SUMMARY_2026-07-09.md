# AVISO — Alertas de cierre del Summary depuradas (2026-07-09)

## Pendiente antes de cerrar esto
**Falta revisar los KPIs y verificar que las alertas hayan cambiado** en una corrida real del Summary (que el tablero KPI siga cuadrando y que las alertas nuevas salgan como se describe abajo). Aún no se validó end-to-end con la interfaz.

## Cambios en las alertas (`pipelines/summary/calculate.py`)

**1. Se quitaron las alertas "detectado solo en Facturación / Notas DS".**
Eran ruido: abajo del resumen ya se desglosa si un cierre viene de un archivo o de ambos. El campo `origen` se sigue guardando para ese desglose en la UI; solo se dejó de emitir la alerta.

**2. La alerta "no encontró fila abierta" ahora distingue dos casos.**
- Si el código **sí está** en el ledger vivo pero no casó año/periodo → *"no casó año/periodo con la provisión viva de ese código — requiere revisión manual"*. Esta es una brecha real de conciliación y sí hay que revisarla a mano.
- Si el código **no está** en el ledger → *"factura sin provisión previa — informativo, no se cierra nada"*. Es una factura de un proyecto que nunca se provisionó aquí; no hay nada que cerrar, es esperado.

Se verificó con los datos reales de Mayo 2026: los 8 códigos que antes alertaban no existen en ninguna hoja del ledger (2021→2026), así que todos caen en el caso informativo. La alerta ya no los marca como "requiere revisión manual".

**3. Código con formato sospechoso (`gxm` en vez de `gmx`).**
No es bug: son errores de captura en el archivo fuente (ej. `24gxm3000.037`, `24gxm3000.047`, con las letras transpuestas). La alerta funciona bien; se corrigen en el Excel de origen. Pendiente que Luis revise `24gmx3000.047`, que probablemente es el mismo proyecto que el typo `24gxm3000.047`.

## Lo demás que se hizo hoy (ya en `main`, sin desplegar al Droplet)

- **Fix de caché en la descarga del Excel** (commit `773bacb`): los nombres de cliente no salían en el Excel descargado porque el navegador cacheaba una versión previa. Se agregó `cache: 'no-store'` en `frontend/src/api.js` y `Cache-Control: no-store` en `/descargar`.
- **Fix de freeze panes del Summary** (commit `7ed6f9b`): el Excel congelaba filas y columnas; ahora solo congela hasta los encabezados (`A13`), igual que el P&L.

Estos dos ya están en `main` pero **el Droplet no se ha reconstruido todavía** — al desplegar entran junto con el cambio de alertas.
