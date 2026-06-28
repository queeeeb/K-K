# Sistema de Diseño Orión — K&K

**Orión** es el sistema de diseño de las plataformas/agentes internos de K&K. Nació con el
**Agente Financiero P3** (primer agente con interfaz) y se documenta acá para que **todo
agente o página futura parta de la misma base visual y de UX, sin volver a discutir cómo
debe verse**.

> La marca de las interfaces es **"Orión by K&K"**. La propiedad intelectual de Orión y de
> los agentes pertenece a K&K.

---

## Qué hay en esta carpeta

| Archivo | Para qué sirve |
|---|---|
| **[PROMPT-BASE.md](PROMPT-BASE.md)** | ⭐ El más importante. Prompt listo para pegar en **Claude Design** o en un agente de código. Encapsula todo el sistema de diseño para que una página nueva salga consistente **sin repetir nada**. |
| **[SISTEMA-DISENO.md](SISTEMA-DISENO.md)** | Especificación completa: marca, fundamentos, color, tipografía, layout, motion, accesibilidad. La fuente de verdad. |
| **[TOKENS.md](TOKENS.md)** | Tokens exactos (paleta hex, escala tipográfica, spacing, radios, sombras) + snippet de configuración para Tailwind. |
| **[COMPONENTES.md](COMPONENTES.md)** | Catálogo de componentes reutilizables (Sidebar, Topbar, StatusPill, Money, Tabla, Stepper, etc.) con su anatomía y clases. |
| **[PATRONES-UX.md](PATRONES-UX.md)** | Patrones de producto reutilizables: flujo de aprobación humana, "la IA interpreta / el código calcula", bloqueo por recurso, sistema de estados. |
| **referencia/AgentePrototipo-orion.jsx** | Implementación canónica (código final del Agente Financiero P3). Úsala como ejemplo vivo. |
| **capturas/** | Referencia visual (login). |

---

## Cómo usarlo en un agente nuevo (flujo recomendado)

1. **Abrí [PROMPT-BASE.md](PROMPT-BASE.md)** y copialo. Reemplazá los marcadores
   `{{...}}` (nombre del producto, pipelines/secciones, flujo) por los del nuevo agente.
2. Pegalo en **Claude Design** (o dáselo a un agente de código) como contexto de diseño.
3. Para detalles finos (un color exacto, un componente puntual), consultá
   [TOKENS.md](TOKENS.md) y [COMPONENTES.md](COMPONENTES.md).
4. Usá **referencia/AgentePrototipo-orion.jsx** como implementación de ejemplo a imitar.

El objetivo: **no volver a explicar "que sea navy con dorado, Inter + mono tabular, con
sidebar, tablas densas y aprobación antes de escribir"** en cada agente. Eso ya está acá.

---

## Resumen de la identidad (TL;DR)

- **Estilo:** dashboard financiero/enterprise, *data-dense*, "Trust & Authority". Práctico, no decorativo.
- **Color:** navy `#0F172A` (shell + acciones) + dorado `#F59E0B` (marca/acento). Semántica: verde=ok/activa, rojo=cancela/destructivo, azul=nueva, ámbar=pendiente/alerta.
- **Tipografía:** **Inter** para UI + **JetBrains Mono** (tabular) para todos los montos/cifras.
- **Layout:** *app shell* con sidebar navy + topbar sticky + área de trabajo clara (`max-w-6xl`).
- **Sello:** login con fondo animado de la constelación de Orión + tarjeta glassmorphic.
- **UX no negociable:** nada se escribe sin confirmación explícita; un solo CTA primario por pantalla; números a la derecha en mono; estados por color **e** icono (nunca solo color).

Base técnica: **React + Tailwind + lucide-react**. Derivado del motor *UI/UX Pro Max*
(producto "Financial Dashboard / Banking", estilo Data-Dense).
