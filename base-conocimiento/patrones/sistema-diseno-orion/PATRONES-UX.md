# Patrones de UX reutilizables — Orión

Patrones de producto (no solo visuales) que nacieron en el Agente Financiero P3 y que
**conviene reutilizar en cualquier agente de K&K** que automatice un proceso con un humano
que revisa y aprueba. No son obligatorios todos en cada agente, pero cuando apliquen, se
resuelven así.

---

## 1. Flujo de aprobación humana (procesar → revisar → confirmar/rechazar)

El patrón central. Un agente nunca aplica cambios irreversibles sin que el usuario apruebe.

```
[Disparar]  →  [Procesando…]  →  [Resumen para revisión]  →  Confirmar → [Reporte final]
                                          │
                                          └──────────────── Rechazar → [Descartado]
```

- **Disparar:** el usuario elige el alcance (mes, periodo, lote) y arranca.
- **Procesando:** `Stepper` con los pasos reales del agente. Refuerzo: *"Nada se escribe todavía."*
- **Resumen (paso sagrado):** muestra **exactamente** lo que va a pasar, agrupado y escaneable,
  **antes** de tocar nada. Aviso visible "Nada se ha guardado". Totales + detalle + alertas.
- **Confirmar / Rechazar:** dos botones diferenciados. Rechazar da certeza explícita:
  *"descarta el plan; ningún archivo se modifica."*
- **Reporte final:** qué se escribió, conteos, y **pendientes manuales** si quedaron.

Reglas de oro:
- Visualmente **imposible confundir** "ver resumen" con "ya se aplicó".
- Mostrar el **antes vs. después** cuando un valor cambia (componente `Delta`).
- El resumen es la última línea de defensa: que sea claro, no bonito.

---

## 2. "La IA interpreta; el código calcula"

En agentes financieros/críticos, hacer **visible** que la IA no inventa números:
- Un texto discreto y permanente: *"La IA interpreta la estructura de los archivos; el sistema
  calcula los montos de forma determinista."*
- El stepper separa "Interpretando con IA" de "Calculando (motor determinista)".
- Genera confianza para finanzas: un error de IA mueve un *mapeo* (visible y corregible en el
  resumen), nunca un total.

---

## 3. Bloqueo por recurso concurrente (lock)

Cuando dos personas podrían operar sobre el mismo recurso (un mes, un lote):
- Si otro usuario ya tiene un proceso abierto, **bloquear** el segundo con mensaje claro:
  *"Lo está procesando Ana López — no puedes iniciar otro hasta que confirme o rechace."*
- **Avisar también al primer usuario** que alguien intentó entrar.
- Estado visual: barra `amber` con `Lock`, botón primario deshabilitado.

---

## 4. Sistema de estados por color + icono

Semáforo consistente en toda la plataforma (ver `StatusPill`):

| Estado | Color | Icono típico | Significado |
|---|---|---|---|
| Activa / OK / hecho | verde (emerald) | `CheckCircle2` | sigue / se completó |
| Cancela / destructivo | rojo (rose) | `XCircle` | se elimina / se rechaza |
| Nueva / info | azul (blue) | — | recién detectada |
| Pendiente / alerta | ámbar (amber) | `Clock` / `AlertTriangle` | requiere revisión |

**Nunca** comunicar el estado solo con color: siempre icono y/o texto.

---

## 5. Sesión y seguridad visibles

- Badge de **sesión segura** en el topbar (ej. "Sesión segura · 8h") — refleja el JWT con
  expiración. Login deja claro "sin registro público".
- Pantallas de error que **tranquilizan**: dicen explícitamente que *no se modificó nada*.

---

## 6. Datos densos, legibles

- Montos/cifras en **mono tabular**, alineados a la derecha.
- Tablas agrupadas por significado (canceladas / activas / nuevas), cada grupo con su color.
- Totales primero (stat cards), detalle después.
- Alertas como **advertencias**, no errores fatales — el usuario decide.

---

## 7. Confidencialidad en prototipos

Todo mockup/demo usa **datos 100% ficticios** (clientes, proyectos, montos inventados).
Ningún dato real de cliente entra a una herramienta externa, prototipo o commit
(regla permanente de K&K). El prototipo Orión incluye un "escenario de demo" para mostrar
estados (normal / bloqueado / error) sin datos reales.
