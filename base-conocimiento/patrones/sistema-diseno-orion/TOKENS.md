# Tokens — Sistema de Diseño Orión

Valores exactos extraídos del código final del Agente Financiero P3. Expresados como tokens
Tailwind (la base técnica) con su hex de referencia.

---

## Color

### Neutros / shell (escala slate)
| Token | Hex | Uso |
|---|---|---|
| `slate-900` | `#0F172A` | Sidebar, botones primarios, texto principal, monograma |
| `slate-800` | `#1E293B` | Hover de botón primario |
| `slate-700` | `#334155` | Texto fuerte secundario |
| `slate-600` | `#475569` | Texto de cuerpo |
| `slate-500` | `#64748B` | Texto atenuado |
| `slate-400` | `#94A3B8` | Labels, placeholders, metadatos |
| `slate-200` | `#E2E8F0` | Bordes de cards |
| `slate-100` | `#F1F5F9` | Fondo de la app, divisores |
| `slate-50`  | `#F8FAFC` | Encabezados de card, hovers de fila |
| `white`     | `#FFFFFF` | Superficie de cards |

### Acento / marca
| Token | Hex | Uso |
|---|---|---|
| `amber-500` | `#F59E0B` | Monograma, highlights, punto de notificación |
| `amber-400` | `#FBBF24` | Icono de nav activo, acento sobre fondo navy |
| `amber-50`  | `#FFFBEB` | Fondo de alertas / pendientes |
| `amber-700/800/900` | — | Texto sobre fondos ámbar |

### Semánticos
| Significado | Token base | Hex | Fondo / borde / texto |
|---|---|---|---|
| Éxito / activa / confirmar | `emerald-600` | `#059669` | `emerald-50` / `emerald-200` / `emerald-700` |
| Destructivo / cancela / rechazar | `rose-600` | `#E11D48` | `rose-50` / `rose-200` / `rose-700` |
| Info / nueva | `blue-600` | `#2563EB` | `blue-50` / `blue-200` / `blue-700` |
| Pendiente / alerta | `amber-500` | `#F59E0B` | `amber-50` / `amber-200` / `amber-800` |
| Neutro (CC / chips) | `slate` | — | `slate-100` / `slate-200` / `slate-600` |

### Login — fondo "Orión" (constelación)
| Elemento | Valor |
|---|---|
| Gradiente espacio | radial `#1D3050` → `#101F36` → `#060C18` |
| Nebulosa A (cálida) | `#F59E0B` @ opacidad 0.28 → 0 |
| Nebulosa B (fría) | `#3B6FD4` @ opacidad 0.26 → 0 |
| Estrellas lejanas | `#9FB4D6` (blur suave) |
| Estrellas cercanas | `#FFFFFF` |
| Líneas constelación | `#FFCE8A` (halo) + gradiente dorado |
| Tarjeta de acceso | `bg-white/40 backdrop-blur-md ring-white/30 shadow-2xl` |

---

## Tipografía
| Token | Valor |
|---|---|
| Familia UI | `Inter`, fallback `ui-sans-serif, system-ui, sans-serif` |
| Familia números | `JetBrains Mono`, fallback `ui-monospace, monospace`, con `tabular-nums` |
| Pesos | 400 / 500 / 600 / 700 |
| Escala | `11px` · 12 (`xs`) · 14 (`sm`) · 16 (`base`) · 18 (`lg`) · 20 (`xl`) · 24 (`2xl`) · 30 (`3xl`) |

---

## Forma & elevación
| Token | Valor | Uso |
|---|---|---|
| Radio | `rounded-md` 6px | pills, botones chicos |
| Radio | `rounded-lg` 8px | botones, inputs, nav |
| Radio | `rounded-xl` 12px | cards |
| Radio | `rounded-2xl` 16px | tarjeta de login |
| Radio | `rounded-full` | avatares, barra demo, puntos |
| Sombra | `shadow-sm` | cards, botones |
| Sombra | `shadow-xl` | barra de demo |
| Sombra | `shadow-2xl` | tarjeta de login |
| Foco | `focus:ring-4` + `ring-<color>/10–25` | todo interactivo |

---

## Layout
| Token | Valor |
|---|---|
| Sidebar | `w-64` (16rem), `bg-slate-900` |
| Topbar | `h-16`, sticky, `bg-white/90 backdrop-blur` |
| Contenido | `max-w-6xl mx-auto`, padding `px-6 lg:px-10 py-6` |
| Barra de acción | `fixed bottom-0 lg:left-64` |
| Breakpoints | `sm 640` · `md 768` · `lg 1024` |
| Ritmo de espaciado | 8pt — gaps `3 / 4 / 6`, padding de card `4 / 5` |

---

## Snippet de configuración (Tailwind)

Para arrancar un proyecto nuevo con estos tokens (Inter + JetBrains Mono + acento ámbar):

```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      fontFamily: {
        ui:  ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        num: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      // La paleta usa los colores Tailwind por defecto:
      //   shell/primario = slate, acento = amber,
      //   éxito = emerald, destructivo = rose, info = blue, alerta = amber
    },
  },
};
```

```css
/* index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
.font-ui  { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
.font-num { font-family: 'JetBrains Mono', ui-monospace, monospace; font-feature-settings: 'tnum' 1; }
```
