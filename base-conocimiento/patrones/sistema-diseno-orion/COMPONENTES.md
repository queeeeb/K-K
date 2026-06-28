# Catálogo de Componentes — Sistema de Diseño Orión

Componentes reutilizables del sistema, tal como existen en
`referencia/AgentePrototipo-orion.jsx`. Reusalos o replicá su anatomía en agentes nuevos.

---

## Estructura (shell)

### `Sidebar` — navegación primaria
- `aside` `w-64` `bg-slate-900`, oculto en móvil (`hidden lg:flex`).
- Header con el monograma `Brand`.
- Grupos con label `text-[11px] uppercase tracking-wider text-slate-500` ("General", "Pipelines").
- Items de nav: icono + texto; activo = `bg-white/10 text-white` con icono `amber-400`.
- Items deshabilitados (pipelines no listos): chip `beta` / `pronto`, `cursor-not-allowed`.
- Footer con "Cerrar sesión".

### `Topbar` — contexto y cuenta
- `header` `h-16` sticky, `bg-white/90 backdrop-blur`, borde inferior.
- Izquierda: breadcrumb (`Sección › Nombre`) + chip de contexto (mes) con icono.
- Derecha: búsqueda, campana con punto ámbar, **badge de sesión** (`emerald`, "Sesión segura · 8h"), avatar con iniciales.

### `Brand` — monograma + nombre
- Cuadrado `rounded-lg` con "K&K" en mono. Variante `dark` (sobre navy) e invertida (sobre claro).
- Nombre de producto ("Orión") + bajada ("by K&K").

### `Footer`
- Nota de propiedad intelectual de K&K.

---

## Átomos de datos

### `Money` — monto formateado
```jsx
const Money = ({ value, className }) => (
  <span className={`font-num tabular-nums ${className}`}>{mxn(value)}</span>
);
```
Usa el formateador de moneda local (`Intl.NumberFormat('es-MX', { style:'currency', currency:'MXN' })`).
**Siempre mono + tabular, alineado a la derecha** en tablas.

### `StatusPill` — chip de estado
- `inline-flex` `rounded-md` `ring-1`, con **icono + texto** (nunca solo color).
- Tonos: `cancel` (rose), `active` (emerald), `new` (blue), `review` (amber), `cc` (slate neutro).

### `Delta` — variación antes→ahora
- Mono; verde con `ArrowUpRight` si sube, rojo con `ArrowDownRight` si baja, `—` si igual.

---

## Estructuras de datos

### `Tabla` + `Row` — tabla densa
- Card `rounded-xl border`; header con **punto de color del tono** + título + contador (mono) + subtítulo.
- `thead` con labels `text-xs uppercase tracking-wide text-slate-400`, fondo `slate-50/50`.
- Columnas numéricas alineadas a la derecha (prop `align`); filas con hover `slate-50/70`.
- La 2ª columna (nombre/cliente) en `font-medium text-slate-800`; el resto `slate-600`.

### KPI / stat cards
- Grid `sm:grid-cols-3`; card `rounded-xl border p-4`.
- Label `text-xs uppercase` + icono; valor `text-2xl font-bold` (mono+tabular si es monto); sub-label atenuado.
- Variante "totales por segmento": valor grande + desglose (facturación / canceladas) bajo un divisor.

### `Stepper` — progreso de proceso
- Lista de pasos; completados con check verde (`emerald-600`), actual con `Loader2` girando sobre `amber-50`, pendientes en gris.
- Cada paso: título + sub-texto opcional.

---

## Acciones & feedback

### Botones
- **Primario:** `bg-slate-900 text-white hover:bg-slate-800 shadow-sm focus:ring-4`.
- **Confirmar (éxito):** `bg-emerald-600 hover:bg-emerald-700`.
- **Rechazar (destructivo):** `border border-rose-200 text-rose-600 hover:bg-rose-50` — *outline*, separado del primario.
- **Secundario / volver:** `border border-slate-300 text-slate-700 hover:bg-slate-50`.
- Regla: **un solo CTA primario por pantalla**.

### Inputs / select
- `rounded-lg border-slate-300`, icono a la izquierda, `focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10`.
- Label visible arriba (`text-sm font-medium text-slate-700`).

### `Loader` (pantalla de proceso)
- Card centrada `max-w-xl` con icono navy girando + Stepper + nota "Nada se escribe todavía".

### Avisos / estados de pantalla
- **Aviso de no-escritura:** barra `amber` con `ShieldCheck` — "Nada se ha guardado todavía".
- **Bloqueo (lock):** barra `amber` con `Lock` — quién tiene el recurso abierto.
- **Error:** card `rose` centrada con `XCircle` + causa + botón volver.
- **Éxito (reporte):** card `emerald` con `CheckCircle2` + grilla de conteos + pendientes manuales.
- **Alertas:** card con lista de advertencias (no errores fatales), `AlertTriangle` ámbar.

### Barra de acción fija
- `fixed bottom-0 lg:left-64`, `bg-white/95 backdrop-blur`, resumen a la izquierda + Rechazar/Confirmar a la derecha.

---

## Sello de marca

### `OrionSky` — fondo animado del login
- SVG de la constelación de Orión: gradiente de espacio profundo, dos nebulosas (cálida/fría),
  dos capas de estrellas (lejanas difusas + cercanas nítidas) con titileo, y las líneas de la
  constelación (halo difuso + trazo con gradiente dorado).
- Acompañado de una tarjeta de login **glassmorphic** (`bg-white/40 backdrop-blur-md`).
- Es el único momento "expresivo" del sistema; el resto es sobrio y funcional.

---

## Iconografía
- **lucide-react** exclusivamente (SVG, stroke consistente). Nunca emojis.
- Tamaños habituales: 13–18px inline, 26px en estados de pantalla.
