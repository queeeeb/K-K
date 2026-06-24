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
