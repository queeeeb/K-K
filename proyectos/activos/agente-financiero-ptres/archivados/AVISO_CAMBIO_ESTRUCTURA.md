# Aviso de cambio de estructura — para Oswaldo

**Fecha:** 2026-06-24

## Qué cambió

La carpeta `agente-provisiones-ptres/` (con `ESPECIFICACION.md` del Summary) se renombró y reorganizó como `agente-financiero-ptres/`. El contenido del spec **no cambió ni una línea** — solo se movió de carpeta.

```
ANTES:
proyectos/activos/agente-provisiones-ptres/ESPECIFICACION.md

AHORA:
proyectos/activos/agente-financiero-ptres/
├── README.md                          ← nuevo, explica la plataforma
├── core/                              ← vacío por ahora
└── pipelines/
    ├── summary/ESPECIFICACION.md      ← el mismo spec, solo movido
    ├── pl/                            ← vacío
    └── cashflow/                      ← vacío
```

## Por qué

P3 pidió que el agente, además del Summary de Provisiones (lo único que tenía spec hasta ahora), genere también el **P&L** (la lógica ya validada en la macro de `pl-automatizacion/`) y un **Cash Flow** nuevo (estatus de cobranza, basado en Facturación — aún sin archivo de referencia del cliente).

Los 3 son la misma forma de trabajo: leer archivos de Drive → interpretarlos con IA → calcular con código determinista → escribir un Excel. En vez de construir 3 agentes sueltos que repiten esa lógica, se construye una sola plataforma con un núcleo compartido (`core/`) y cada entregable como una pieza conectable (`pipelines/`).

## Qué NO cambió

- El diseño del Summary (`pipelines/summary/ESPECIFICACION.md`) sigue siendo el mismo, palabra por palabra.
- El macro de P&L en `pl-automatizacion/` sigue como proyecto cerrado, sin tocar — es la referencia de lógica para portar a `pipelines/pl/`, no se fusiona.
- El stack, costo (~$10-20 USD/mes) y arquitectura del droplet siguen igual.

## Qué sigue

Se construye primero `pipelines/summary/` completo (es el más complejo). De ahí se extrae el contrato genérico que va a vivir en `core/` (`PipelineSpec`), para que P&L y Cash Flow se agreguen después sin rehacer nada del núcleo.

---

## Actualización — Contrato PipelineSpec y plan de implementación (2026-06-24)

### Qué se hizo

1. **Se definió el contrato `PipelineSpec`** en `core/ESPECIFICACION.md` (commit `9f320fe`): 4 piezas — `sources`, `interpret`, `calculate`, `write` — que cada pipeline implementa para conectarse al núcleo. `core/api` orquesta igual para los 3 pipelines vía `POST /procesar/{pipeline}` y `POST /confirmar/{pipeline}`.
2. **Se escribió el plan de implementación del backend** (sin frontend todavía) en `docs/superpowers/plans/2026-06-24-agente-financiero-core-summary-backend.md`: 12 tareas con TDD que construyen `core/` (SQLite para plan+lock, lock por mes, audit log, registry) y el pipeline Summary completo (4 interpreters con IA, reconciliación determinista, escritura con `openpyxl`), probado con archivos de prueba sintéticos (sin datos reales de P3).

### Por qué

Se decidió backend primero (sin UI) porque el riesgo real del proyecto está en interpretar las 4 fuentes y calcular bien los montos — eso se prueba completo con la API directo, sin necesitar la interfaz. El frontend se hace en un plan separado una vez que el backend esté validado.

### Decisiones técnicas tomadas (para que no sorprendan en el código)

- **`uv`** como manejador de dependencias Python (en vez de pip/poetry) — reproducible y simple para un proyecto nuevo.
- **SQLite local** (no Redis) para guardar el plan de escritura y el bloqueo por mes entre `/procesar` y `/confirmar` — el volumen real (~1 corrida/mes por pipeline) no justifica más infraestructura.
- **Fixtures sintéticos** (datos inventados, mismo formato de columnas que los archivos reales) para todos los tests — ningún dato real de P3 se sube al repo.

### Qué sigue

Ejecutar el plan (`docs/superpowers/plans/2026-06-24-agente-financiero-core-summary-backend.md`). Queda fuera de este plan, a propósito: conectar Drive/Claude reales (pendiente confirmar carpeta de Drive con el cliente) y el frontend.
