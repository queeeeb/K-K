# Agente Financiero — P-TRES GROUP

Plataforma que automatiza 3 entregables mensuales de P3 a partir de archivos en Google Drive:

| Pipeline | Qué genera | Estado |
|---|---|---|
| **Summary** (`pipelines/summary/`) | Hoja mensual de Provisiones (`2026_Summary_provision.xlsm`) | Diseño aprobado — ver `ESPECIFICACION.md`. Primer pipeline a construir. |
| **P&L** (`pipelines/pl/`) | Estado de resultados mensual (hoy existe como macro VBA en `pl-automatizacion/`) | Diseño inicial — ver `ESPECIFICACION.md`. Porta la lógica validada del macro, pero la IA interpreta/clasifica todo dinámicamente (no catálogos congelados). |
| **Cash Flow** (`pipelines/cashflow/`) | Estatus de cobranza/AR a partir de Facturación | Pendiente de diseño — falta archivo de referencia del cliente. |

## Por qué una plataforma y no 3 agentes sueltos

Los 3 pipelines comparten la misma forma: leer fuentes de Drive → interpretar (Claude) → reconciliar/calcular (Python, determinista) → escribir un Excel destino. En vez de repetir esa forma 3 veces, el núcleo compartido (`core/`) vive una sola vez y cada pipeline se conecta a él:

- **`core/`** — lo que no cambia entre pipelines: cliente de Google Drive, bloqueo por mes (`lock`), bitácora de cambios (`audit_log`), y el router genérico de la API (`POST /procesar/{pipeline}`, `POST /confirmar/{pipeline}`).
- **`pipelines/<nombre>/`** — lo que sí cambia: qué fuentes espera, cómo las interpreta, cómo reconcilia/calcula, cómo escribe el destino.

Se construye primero el **Summary** (el más complejo: 4 fuentes con formato distinto cada una) porque si el núcleo aguanta ese caso, P&L y Cash Flow —más simples— se conectan después sin tocar `core/`.

Hoy `core/` está vacío: el contrato (`PipelineSpec`) se va a definir extrayéndolo del Summary real, no diseñándolo en abstracto antes de tener un caso construido.

## Relación con otros proyectos del repo

- `pl-automatizacion/` — macro VBA de P&L, **proyecto cerrado y separado**, no se modifica. Es la referencia de lógica de negocio para construir `pipelines/pl/`, no se fusiona con esta plataforma.

## Autenticación

Todos los endpoints de escritura (`/procesar/{pipeline}`, `/confirmar/{pipeline}`, `/rechazar/{pipeline}`) requieren un JWT en el header `Authorization: Bearer <token>`.

- **Obtener un token:** `POST /login` con `{"usuario": "...", "password": "..."}` → `{"access_token": "...", "token_type": "bearer", "expires_in": 28800}` (8 horas).
- **Crear un usuario nuevo:** `uv run python scripts/crear_usuario.py <username> <password>` — no hay endpoint público de registro, a propósito.
- **Variable de entorno requerida en el servidor:** `AGENTE_JWT_SECRET` — secreto de firma del JWT, nunca con valor por default. Generar uno con `python -c "import secrets; print(secrets.token_hex(32))"` y guardarlo fuera del repo.
- Cada persona de P3 tiene su propio usuario; el campo `locked_by` del módulo `lock` se llena con el usuario autenticado, no con un campo libre del request.
