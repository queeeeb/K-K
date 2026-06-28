# Sistema de Diseño Orión — Especificación

Fuente de verdad del diseño de los agentes internos de K&K. Derivado del motor
*UI/UX Pro Max* (tipo de producto **Financial Dashboard / Banking**, estilo **Data-Dense /
Minimal Swiss**) y materializado en el **Agente Financiero P3** ("Orión").

---

## 1. Principios

1. **Práctico antes que decorativo.** Es software de trabajo: prioriza legibilidad de datos,
   escaneabilidad y claridad de acciones sobre el lucimiento visual.
2. **Trust & Authority.** Estética sobria de producto financiero serio. El usuario maneja
   dinero real: el diseño transmite control y precisión.
3. **La IA interpreta; el sistema calcula.** El diseño hace visible esa frontera para generar
   confianza (ver [PATRONES-UX.md](PATRONES-UX.md)).
4. **Nada se escribe sin confirmación.** El paso de revisión/aprobación es sagrado y debe ser
   visualmente imposible de confundir con "ya se guardó".
5. **Consistencia.** Mismo shell, mismos componentes, mismos tokens en todos los agentes.

---

## 2. Marca

- **Nombre de las interfaces:** *Orión* — con bajada **"by K&K"**.
- **Monograma:** cuadrado redondeado (`rounded-lg`) con las letras **K&K** en **mono**.
  - Sobre fondo oscuro: fondo dorado `amber-500`, texto `slate-900`.
  - Sobre fondo claro: fondo `slate-900`, texto `amber-400`.
- **Nota legal (footer):** "Orión by K&K — La propiedad intelectual y el agente pertenecen a
  K&K. © 2026 K&K · Uso interno."
- **Sello visual:** pantalla de login con **fondo animado de la constelación de Orión**
  (cielo profundo + nebulosas + estrellas titilantes + líneas de la constelación) y tarjeta
  de acceso **glassmorphic** (`bg-white/40 backdrop-blur-md`).

---

## 3. Color

Paleta basada en la escala **Tailwind slate** (neutros) + acentos semánticos. Hex exactos en
[TOKENS.md](TOKENS.md).

| Rol | Token Tailwind | Uso |
|---|---|---|
| **Shell / primario** | `slate-900` (#0F172A) | Sidebar, botones primarios, texto principal, monograma claro |
| Hover primario | `slate-800` (#1E293B) | Hover de botones navy |
| **Acento / marca** | `amber-500` (#F59E0B), `amber-400` | Monograma, icono de nav activo, highlights, notificación |
| Fondo app | `slate-100` (#F1F5F9) | Fondo del área de trabajo |
| Superficie | `white` + `slate-50` (#F8FAFC) | Cards y encabezados sutiles |
| Bordes | `slate-200` (#E2E8F0), `slate-100` | Bordes de cards, divisores |
| Texto cuerpo | `slate-600/700` | Texto general |
| Texto atenuado | `slate-400/500` | Labels, metadatos, placeholders |
| **Éxito / activo / confirmar** | `emerald-600` (#059669) + `emerald-50/200/700` | Estado activo, botón Confirmar, reporte ok |
| **Destructivo / cancela / rechazar** | `rose-600` + `rose-50/200/700` | Estado cancelado, botón Rechazar, líneas tachadas |
| **Info / nueva** | `blue-600` + `blue-50/200/700` | Estado "nueva", datos informativos |
| **Pendiente / alerta** | `amber` family | Estado "pendiente de aprobación", alertas, pendientes manuales |

**Reglas:**
- El color **nunca** es el único portador de significado: todo estado lleva **icono + texto**.
- Contraste mínimo 4.5:1 para texto (cuerpo `slate-600`↑ sobre blanco cumple).
- Semáforo consistente en toda la plataforma: verde/rojo/azul/ámbar siempre significan lo mismo.

---

## 4. Tipografía

- **UI:** **Inter** (`400, 500, 600, 700`). Fallback: `ui-sans-serif, system-ui, sans-serif`.
- **Cifras/montos:** **JetBrains Mono** (`400, 500, 600`) con `tabular-nums`
  (`font-feature-settings: 'tnum'`). Fallback: `ui-monospace, monospace`.
  - **Todo monto, código, referencia o cifra va en mono y alineado a la derecha** en tablas.
    Es la firma visual del sistema y evita que las columnas "bailen".
- **Escala** (Tailwind): `11px` · `xs 12` · `sm 14` · `base 16` · `lg 18` · `xl 20` · `2xl 24` · `3xl 30`.
- **Jerarquía por peso:** títulos `bold (700)` / semibold (600); labels `medium (500)`; cuerpo `regular (400)`.
- Labels de sección y de tabla: `text-xs uppercase tracking-wide` en `slate-400/500`.

Carga vía Google Fonts:
```
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

---

## 5. Layout & espaciado

- **App shell:**
  - **Sidebar** `w-64`, fondo `slate-900`, oculto en móvil (`hidden lg:flex`). Secciones
    "General" y "Pipelines" (o las secciones del agente).
  - **Topbar** `h-16`, sticky, `bg-white/90 backdrop-blur`, borde inferior `slate-200`.
    Breadcrumb + contexto (mes), búsqueda, notificaciones, badge de sesión, avatar.
  - **Área de trabajo:** `main` con `px-6 py-6 lg:px-10`, contenido en `max-w-6xl mx-auto`.
  - **Footer** con la nota de propiedad intelectual.
- **Ritmo de 8pt.** Gaps habituales `gap-3 / gap-4 / gap-6`. Padding de card `p-4 / p-5`.
- **Barra de acción fija** (en pantallas de aprobación): `fixed bottom-0`, con `lg:left-64`
  para respetar el ancho del sidebar.
- **Responsive:** mobile-first; breakpoints `sm 640 / md 768 / lg 1024`. Sin scroll horizontal.

---

## 6. Forma, elevación y efectos

- **Radios:** `rounded-md` (pills, botones chicos) · `rounded-lg` (botones, inputs, nav) ·
  `rounded-xl` (cards) · `rounded-2xl` (tarjeta de login) · `rounded-full` (avatares, pills demo).
- **Sombras:** `shadow-sm` en cards y botones; `shadow-2xl` en la tarjeta glass del login;
  `shadow-xl` en la barra de demo.
- **Blur:** `backdrop-blur` en topbar, barra de acción y tarjeta de login (propósito, no adorno).
- **Foco:** siempre visible — `focus:ring-4` con `ring-<color>/10–25`; inputs
  `focus:border-slate-900 focus:ring-slate-900/10`.

---

## 7. Movimiento

- Transiciones de 150–300ms (`transition-colors`, hover de nav/botones/filas).
- Loaders con `animate-spin` (icono `Loader2`).
- **Stepper** de proceso: pasos que se completan con check verde.
- Login: keyframes propios (`twinkle`, `pulse`, `drift`) de 4–11s para las estrellas y
  nebulosas de la constelación. Sutil, nunca distrae del formulario.
- Respetar `prefers-reduced-motion` al implementar en producción.

---

## 8. Accesibilidad (checklist mínimo)

- [ ] Contraste de texto ≥ 4.5:1 (cuerpo) en claro.
- [ ] Estados con **icono + texto**, no solo color.
- [ ] Focus rings visibles en todo elemento interactivo.
- [ ] Labels visibles en inputs (no solo placeholder); error junto al campo.
- [ ] Un solo CTA primario por pantalla; el destructivo separado y diferenciado (outline rojo).
- [ ] Iconos SVG (lucide), nunca emojis.
- [ ] Números tabulares para columnas de datos/montos.
- [ ] Touch targets cómodos; sin depender de hover para acciones principales.

---

## 9. Base técnica

- **React + Tailwind CSS + lucide-react.** Sin librerías de UI pesadas.
- Componentes funcionales con estado local; ver catálogo en [COMPONENTES.md](COMPONENTES.md).
- La implementación canónica vive en `referencia/AgentePrototipo-orion.jsx`.
