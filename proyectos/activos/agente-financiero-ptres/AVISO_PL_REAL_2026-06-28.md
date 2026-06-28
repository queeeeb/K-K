# AVISO — Pipeline P&L real cableado (2026-06-28)

Se conectó el pipeline P&L a la API de Claude y se pueden descargar los reportes desde el frontend. Cambios en `agente-financiero-ptres/`:

**`pipelines/pl/extract.py` (nuevo)**
Parser determinista que lee el archivo Contpaqi y extrae cuentas con sus segmentos antes de mandarlos a Claude. El propósito es que Claude reciba solo lo que necesita clasificar (número y nombre de cuenta) y no procese estructura ni montos — así no se gastan tokens extra en la API.

**`pipelines/pl/interpret.py`**
Cambiado a Claude Haiku 4.5. Funciona igual que Opus para clasificar cuentas contables, pero cuesta 5× menos por corrida. Las pruebas con datos reales dieron el mismo resultado.

**`pipelines/summary/interpret.py`**
Pendiente de revisar — model swap a Sonnet 4.6 está commiteado pero no validado todavía con un caso real del Summary.

**`core/api.py` — endpoint `GET /descargar/{archivo}`**
Descarga autenticada del Excel generado. El archivo se sirve desde el volumen Docker (`/data/reportes/`), no desde Drive — los service accounts de Google no pueden crear archivos en Drive personal de Gmail.

**Frontend**
Botón "Descargar Excel" en la pantalla de resultado del P&L. Llama al endpoint con el JWT del usuario activo.

**`Caddyfile`**
Faltaba la ruta `/descargar/*` — Caddy mandaba esas peticiones al frontend en vez del backend, lo que hacía que el Excel descargado no abriera en Excel.

**Validación de contenido**
Comparado el Excel generado vs el P&L real de P3 Marzo 2026. Estructura de secciones idéntica, NET PROFIT cuadra exacto. Las cuentas que no aparecen en nuestro output tienen saldo 0 en Marzo y Contpaqi no las exporta — comportamiento correcto.
