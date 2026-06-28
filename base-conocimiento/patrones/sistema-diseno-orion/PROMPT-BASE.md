# Prompt base — Diseño Orión para un agente nuevo

Pegá este prompt en **Claude Design** (o dáselo a un agente de código) cuando arranques la
interfaz de un agente nuevo de K&K. Encapsula todo el sistema de diseño Orión para que la
página salga consistente **sin volver a explicar la identidad visual**.

**Cómo usarlo:** reemplazá los marcadores `{{...}}` por los datos del agente nuevo y borrá lo
que no aplique. Lo demás dejalo igual — eso *es* el sistema de diseño.

---

```
Diseñá la interfaz de "{{NOMBRE_DEL_AGENTE}}", una plataforma interna de K&K que
{{QUÉ AUTOMATIZA EN UNA FRASE}}. Construilo como un prototipo React clickeable, en un único
componente, con DATOS 100% FICTICIOS (nada real: clientes/montos/nombres inventados).

== IDENTIDAD DE MARCA (Sistema de Diseño "Orión by K&K") ==
- Las interfaces internas de K&K se llaman "Orión by K&K". Monograma "K&K" en un cuadrado
  redondeado, en fuente monoespaciada. La propiedad intelectual pertenece a K&K (ponelo en el footer).
- Estilo: dashboard financiero/enterprise, sobrio, data-dense, "Trust & Authority". Práctico,
  no decorativo. Es software de trabajo.

== COLOR ==
- Shell y acciones primarias: navy slate-900 (#0F172A), hover slate-800.
- Acento de marca: dorado amber-500 (#F59E0B) / amber-400 (monograma, icono de nav activo, highlights).
- Fondo de trabajo: slate-100; superficies en blanco con bordes slate-200; texto slate-900/600,
  atenuado slate-400/500.
- Semáforo (SIEMPRE color + icono, nunca solo color):
  verde emerald-600 = ok/activo/confirmar · rojo rose-600 = cancela/destructivo/rechazar ·
  azul blue-600 = nuevo/info · ámbar amber = pendiente/alerta.

== TIPOGRAFÍA ==
- UI: Inter (400/500/600/700).
- Cifras/montos: JetBrains Mono con tabular-nums, alineados a la derecha en tablas. TODO monto,
  código o referencia va en mono tabular. Es la firma visual del sistema.
- Cargá ambas por Google Fonts; dejá fallback de system fonts.

== LAYOUT (app shell) ==
- Sidebar navy w-64 (oculto en móvil) con secciones de navegación: {{SECCIONES/PIPELINES DEL AGENTE}}.
  Item activo resaltado con icono dorado; items no disponibles con chip "beta"/"pronto".
- Topbar h-16 sticky (bg-white/90 backdrop-blur): breadcrumb + contexto, búsqueda, notificaciones,
  badge "Sesión segura · 8h", avatar con iniciales.
- Área de trabajo: max-w-6xl centrado, padding px-6 lg:px-10.
- Footer con la nota de propiedad intelectual de K&K.

== COMPONENTES ==
- Cards rounded-xl con borde slate-200 y shadow-sm. Pills de estado rounded-md con ring e icono.
- Tablas densas: header con punto de color del grupo + título + contador; columnas numéricas a la
  derecha; hover de fila sutil; labels de columna en text-xs uppercase.
- Stat cards de KPI (valor grande, mono si es monto).
- Botones: primario navy; Confirmar verde; Rechazar en OUTLINE rojo (separado del primario);
  secundario con borde gris. UN SOLO CTA primario por pantalla.
- Inputs rounded-lg con icono y focus:ring-4. Labels visibles.
- Iconos: lucide-react exclusivamente, nunca emojis.

== LOGIN (sello de marca) ==
- Pantalla de login sobre navy con FONDO ANIMADO de la constelación de Orión (gradiente de espacio
  profundo #1D3050→#060C18, dos nebulosas suaves cálida/fría, estrellas titilantes en dos capas, y
  las líneas de la constelación con trazo dorado) y una tarjeta de acceso glassmorphic
  (bg-white/40 backdrop-blur). Título "Orión / by K&K". Mensaje "Autenticación JWT · 8h · sin registro público".

== FLUJO Y UX (reutilizá lo que aplique) ==
- Patrón de aprobación humana: {{DISPARAR}} → procesando (stepper con los pasos reales) →
  RESUMEN PARA REVISIÓN → Confirmar / Rechazar → reporte final.
- El paso de revisión es sagrado: aviso visible "Nada se ha guardado todavía"; mostrar exactamente
  qué va a pasar antes de aplicar; mostrar antes vs. después cuando un valor cambia.
- Si aplica concurrencia: bloqueo por recurso con mensaje de quién lo tiene abierto.
- Si hay IA: dejar visible "la IA interpreta; el sistema calcula" para dar confianza.
- Estados de error que tranquilizan ("no se modificó nada"). Alertas como advertencias, no errores fatales.
- Incluí una barra de "demo" para saltar entre pantallas y estados (normal / bloqueado / error).

== ACCESIBILIDAD ==
- Contraste ≥ 4.5:1; focus rings visibles; estados con icono + texto; touch targets cómodos;
  respetar prefers-reduced-motion; transiciones 150–300ms.

Entregable: un único componente React funcional, navegable de principio a fin con estado local
(sin backend), datos ficticios. Priorizá el flujo y la jerarquía visual por encima de cubrir cada
detalle. Tomá como referencia de calidad el agente "Orión" (Agente Financiero P3).
```

---

> Para detalles exactos de un token o componente, ver [TOKENS.md](TOKENS.md) y
> [COMPONENTES.md](COMPONENTES.md). Para el ejemplo vivo, ver
> `referencia/AgentePrototipo-orion.jsx`.
