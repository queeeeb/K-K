# Plantilla de Presentación Ejecutiva — Estilo "Orión by K&K"

Deck de venta **autocontenido** (un solo archivo HTML) con la identidad visual de
K&K: dashboard enterprise financiero, *deep-space* navy + dorado, constelación
animada en la portada y cifras en tipografía mono tabular. Pensado para **presentar
un producto/servicio a un cliente** y cerrar la venta.

Nació del pitch del Agente Financiero (Orión) y se generalizó acá para que cualquier
proyecto futuro arranque con el mismo formato sin rehacer el diseño.

## Archivos

| Archivo | Para qué |
|---|---|
| `plantilla-deck.html` | El deck. Ábrelo en el navegador o publícalo como Artefacto. Trae marcadores `{{...}}` para reemplazar. |
| `README.md` | Este archivo. |

## Cómo usarla

1. **Copia** `plantilla-deck.html` a la carpeta del proyecto/cliente (o a tu scratchpad).
2. **Reemplaza** cada marcador `{{...}}` por el texto real. Busca `{{` para encontrarlos todos.
3. **Presenta**: ábrelo en el navegador (F11 = pantalla completa) o publícalo como
   **Artefacto en claude.ai** para tener un link.
4. Navega con **scroll** o con las flechas **← / →**. Arriba a la derecha hay un
   botón para alternar **tema claro/oscuro**.

## Estructura (arco de venta)

Cada `<section>` es una diapositiva, en este orden:

1. **Portada** — marca + promesa gancho al cliente.
2. **El problema** — 3 dolores actuales (sólo el título en pantalla; el detalle lo dices tú).
3. **Solución / cómo funciona** — flujo de 4 pasos + un banner de refuerzo.
4. **Por qué confiar** — 4 garantías de control.
5. **Seguridad y confidencialidad** — 4 pilares + la regla de confidencialidad de K&K.
6. **Lo que ganas** — 3 cifras de impacto + 3 beneficios.
7. **Un modelo que crece** — núcleo + módulos (escalabilidad). *Opcional.*
8. **Cierre** — titular + llamado a la acción.

**Agregar/quitar secciones:** duplica o borra un bloque `<section>`. Si cambias los
`id`, actualiza también el arreglo `ids` del `<script>` final (nav por teclado) y la
numeración de los `.eyebrow`.

## Menos texto, más decir

Una presentación se **dice**, no se lee. La plantilla ya deja varias tarjetas con
sólo el título a propósito — el desarrollo va en tu discurso, no en la pantalla.
Mantén ese criterio al llenar los `{{...}}`.

## Sistema de diseño (tokens)

- **Color:** navy `#0F172A` / deep-space `#060C18` en diapositivas de impacto;
  superficies claras slate (`#F8FAFC` / `#FFFFFF`, bordes `#E2E8F0`) en las de
  contenido. Acento **dorado** `#F59E0B` / `#FBBF24`.
- **Semánticos:** verde `#059669` (ok), rojo `#E11D48` (problema), azul `#2563EB` (info).
- **Tipografía:** sans del sistema para UI; **todas las cifras** en mono tabular.
- Los tokens viven como variables CSS (`:root`) al inicio del `<style>`; soporta
  tema claro y oscuro.

## Confidencialidad (obligatorio)

Según el `CLAUDE.md` del repo: **ningún dato real de cliente** (montos, nombres de
proyecto, archivos, URLs internas) se commitea a este repo. Esta plantilla sólo
contiene marcadores `{{...}}`.

> El deck **final** (con el nombre del cliente, cifras y links reales) se entrega
> como archivo/artefacto aparte y **no** se sube al git.
