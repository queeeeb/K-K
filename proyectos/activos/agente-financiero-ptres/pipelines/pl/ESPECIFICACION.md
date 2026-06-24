# Especificación de Diseño — Pipeline P&L (Estado de Resultados)

**Proyecto:** Agente Financiero P-TRES GROUP — pipeline `pl` (Estado de Resultados mensual).
**Fecha:** 2026-06-24
**Estado:** Diseño inicial — derivado del macro VBA validado (`pl-automatizacion/macro/GenerarPL.bas`).
**Relación con otros specs:** Implementa el contrato [`PipelineSpec`](../../core/ESPECIFICACION.md) del núcleo `core/`. Comparte forma con [`summary`](../summary/ESPECIFICACION.md) y `cashflow`.
**Referencia de lógica:** macro cerrado `pl-automatizacion/` — **NET PROFIT e INCOMES cuadran exacto contra la referencia del cliente de Marzo 2026** (commit `fdaeca3`). Es la fuente de verdad de la lógica de negocio; este pipeline la porta al agente, no se fusiona con el macro.

---

## 1. Resumen ejecutivo (para el cliente)

Hoy el Estado de Resultados mensual se genera con un macro de Excel que el usuario corre a mano sobre el export de Contpaqi. El macro funciona y los números cuadran, pero tiene un costo oculto: **toda la inteligencia está congelada en listas hardcodeadas** — los nombres de ~46 clientes, la traducción español→inglés de cada rubro, los alias de cada cliente, los casos especiales de cuentas. Cuando aparece un cliente nuevo, un rubro nuevo o cambia un nombre, el macro lo manda al cajón de "OTROS" o hay que editar el código.

Este pipeline hace el mismo trabajo, pero **la IA analiza todo el archivo de Contpaqi de forma dinámica**: reconoce la estructura jerárquica del reporte, clasifica cada cuenta a su rubro, desglosa las ventas por cliente y traduce los nombres — sin depender de que el cliente ya esté en una lista. El usuario elige el mes, **revisa un resumen** y **aprueba**. El sistema:

1. Toma el archivo de Contpaqi directamente de Google Drive.
2. **Interpreta** el reporte completo (máquina de estados: cuentas, segmentos, totales, movimientos).
3. **Clasifica** cada cuenta a su rubro del P&L y traduce los nombres ES→EN.
4. **Calcula** todos los montos con precisión determinista (el sistema calcula, nunca la IA).
5. Muestra un resumen para aprobación — **nada se escribe sin confirmar**.
6. Escribe las hojas `CONSOLIDATED` y `BY SEGMENT` con el formato de referencia.
7. Sube el archivo a Drive y entrega un reporte.

> El macro convirtió un trabajo manual en un botón. Este pipeline convierte un botón frágil (que se rompe con cada cliente nuevo) en uno que se adapta solo y siempre pide aprobación.

---

## 2. Contexto de negocio

### Insumo (una sola fuente)

Export de Contpaqi **"Movimientos Auxiliares por Segmento de Negocio"** (`.xlsx/.xls/.xlsm`), hoja 1.

No es una tabla limpia: es un **reporte jerárquico** donde el significado de cada fila depende de su tipo y del estado acumulado de las filas anteriores. Por eso requiere interpretación con máquina de estados, no un read de columnas fijo.

- **Periodo:** texto libre en `A3` (con fallback a `A2`) → va al encabezado del P&L.
- **Columnas relevantes** (1-indexadas): `A`=cuenta/etiqueta · `B`=tipo de fila (`"Diario"`, nombre de cuenta) · `D`=tercero/cliente · `E`=marcador `"Total Seg."` · `F`=cargos · `G`=abonos.

### Salida (dos hojas)

- **`CONSOLIDATED`** (3 columnas): `DESCRIPTION`, `TOTAL`, `%`.
- **`BY SEGMENT`** (11 columnas): `DESCRIPTION` + 4 segmentos × (`monto`, `%`) + `TOTAL` × (`monto`, `%`).

Segmentos del negocio y su orden de columna en `BY SEGMENT`:

| Índice | Código en Contpaqi | Etiqueta en P&L | Columnas (monto / %) |
|---|---|---|---|
| 0 | `BO` | BACK OFFICE | B / C |
| 1 | `CONS OPS` | CONSUL OP | D / E |
| 2 | `ING` | ENGINEERING | F / G |
| 3 | `DIGITAL SOLUTIONS` | DIGITAL SOLUTIONS | H / I |
| 4 | (acumulador) | TOTAL | J / K |

> Mapeo de columna: `montoCol = 2 + idx*2`, `pctCol = 3 + idx*2`. *(El macro escribe además una hoja `DEBUG` temporal — no se porta.)*

---

## 3. Cómo se tratan los datos del P&L — núcleo del parseo

Esta es la parte que el agente debe conocer a fondo. Se descompone en **interpretación (IA)** y **cálculo (código)** siguiendo el mismo límite que el pipeline Summary: *la IA dice qué es cada cosa, el código hace toda la aritmética.*

### 3.1 Estructura del insumo — máquina de estados (interpretación)

El reporte se recorre de arriba a abajo manteniendo tres variables de estado: **cuenta actual**, **segmento actual** y bandera **"dentro de Ventas Nacionales"**. Hay **4 tipos de fila** que la IA debe reconocer:

| Tipo de fila | Cómo se reconoce | Qué aporta |
|---|---|---|
| **A. Cuenta** | `A` con formato de cuenta contable: `NNNN-...` (largo ≥8, guion en la posición 5, primeros 4 dígitos numéricos). | Abre una cuenta nueva; su nombre está en `B`. Se clasifica a un grupo/rubro (§3.2). Activa el estado "Ventas Nacionales" si es la cuenta lump-sum de ventas nacionales. |
| **B. Movimiento detalle de Ventas Nacionales** | Estando dentro de Ventas Nacionales, con segmento activo y `B = "Diario"`. | El tercero está en `D`; el monto en `G`. Permite **desglosar la venta nacional por cliente individual** (§3.4). |
| **C. Segmento** | `A` empieza con `"Segmento:"`. | Fija el segmento activo (§2) para las filas siguientes. |
| **D. Total de segmento** | `E` empieza con `"Total Seg."`. | Cierra el acumulado de la cuenta+segmento actual: cargos en `F`, abonos en `G` (§3.3). |

> **Por qué IA y no regex fijo:** el formato exacto del export puede variar (filas de título, subtotales intermedios, etiquetas con espaciado inconsistente, columnas corridas). La IA recibe el volcado de la hoja y devuelve **el mapa de interpretación** (qué fila es de qué tipo, en qué columnas están cuenta/cargos/abonos/tercero, dónde empieza cada segmento). El código luego lee los valores de esas celdas. La IA **no** devuelve montos.

### 3.2 Clasificación cuenta → grupo → rubro (interpretación dinámica)

Cada cuenta se clasifica a un **grupo** del P&L por su número. El macro lo hace con una tabla fija de prefijos; **el agente lo hace de forma dinámica con la IA**, usando esta lógica como guía (y la lista de prefijos solo como referencia/validación, no como límite):

| Prefijo de cuenta | Grupo | Rubro del P&L | Signo |
|---|---|---|---|
| `4110` | Ventas / Accrued Revenue | **INCOMES** | ingreso |
| `4210` / `4310` / `4510` | Other Incomes | **OTHER INCOMES** | ingreso |
| `6100-001` | Sueldos y salarios | EXPENSES | gasto |
| `6100-002` | Previsión social | EXPENSES | gasto |
| `6100-004` | Contribuciones de seguridad social | EXPENSES | gasto |
| `6100-005` | Impuesto sobre nóminas | EXPENSES | gasto |
| `6100-006` | Gastos fijos | EXPENSES | gasto |
| `6100-007` | Gastos variables | EXPENSES | gasto |
| `6100-008` | Gastos financieros | EXPENSES | gasto |
| `6100-009` | Pérdida cambiaria | OTHER EXPENSES | gasto |
| `0000-000-80*` / `8000` | Impuestos al resultado del ejercicio | ACCRUED TAXES | gasto |
| cualquier otra | — | **se ignora** (no entra al P&L) | — |

**Requisito del cliente — la IA analiza todo, no solo lo hardcodeado:** si aparece una cuenta o un rubro que el macro mandaría a "OTROS PROJECTS" / "OTHER CLIENTS" / `"  " & nombre`, la IA debe **clasificarlo a su rubro correcto** según el número de cuenta y el nombre, y **reportarlo en alertas** como rubro nuevo para que el usuario lo valide — en vez de esconderlo silenciosamente en un cajón genérico.

### 3.3 Regla de signo (cálculo determinista — invariante crítico)

Al cerrar cada `Total Seg.` el valor de la cuenta en ese segmento se calcula así, **siempre por código**:

- **Cuentas de ingreso** (número empieza en `4`): `valor = abonos − cargos`
- **Cuentas de gasto** (resto): `valor = cargos − abonos`

El valor se acumula en `monto[cuenta][segmento]` y en el acumulador `monto[cuenta][TOTAL]`. **Esta regla nunca la decide la IA.**

### 3.4 Desglose de Ventas Nacionales por cliente (interpretación + normalización)

La cuenta lump-sum de ventas nacionales no se reporta como un solo monto: se **desglosa por cliente** a partir de los movimientos `"Diario"` (filas tipo B). El tercero viene en `D` y se **normaliza a un nombre canónico**:

- El macro usa una tabla fija de alias (ej. `"VOLKSWAGEN DE MEXICO, S.A. DE C.V." → "VOLKSWAGEN"`, `"SCOTIABANK INVERLAT" → "SCOTIA BANK"`, varios clientes → `"OTHER CLIENTS"`).
- **El agente lo hace con la IA:** reconoce que dos variantes de razón social son el mismo cliente y las une bajo un nombre canónico, sin requerir que el alias exacto esté en una lista. Los alias del macro quedan como **referencia/semilla**, no como el universo cerrado de clientes posibles.

### 3.5 Normalización y traducción de nombres ES → EN (interpretación)

Cada nombre de cuenta en español se traduce a su etiqueta en inglés del P&L (ej. `SUELDOS Y SALARIOS → GENERAL DEP`, `AGUINALDO → CHRISTMAS BONUS`, `IMPUESTOS SOBRE NOMINA → PAYROLL TAX`; provisiones de ingreso devengado → `ACCRUED REVENUE <CLIENTE>`).

- El macro tiene esa traducción como un diccionario gigante hardcodeado (función `EN`).
- **El agente la hace con la IA**, que traduce los rubros financieros español→inglés de forma consistente. El diccionario del macro sirve como **glosario de referencia** para mantener exactamente los mismos labels que la referencia del cliente (importante para que el P&L se vea idéntico mes a mes), pero un rubro nuevo no rompe el proceso: se traduce y se marca en alertas.

### 3.6 Subtotales y resultado (cálculo determinista)

Una vez clasificado y acumulado todo, el código calcula por segmento:

```
OPERATING PROFIT = INCOMES − EXPENSES(6001..6008)
NET PROFIT       = OPERATING PROFIT + OTHER INCOMES − OTHER EXPENSES(6009) − ACCRUED TAXES(8000)
```

**Base de los porcentajes (denominador):** los ingresos 4110 sumando el desglose por cliente (`4110NS`) y **excluyendo** la cuenta lump-sum de ventas nacionales (que se reemplaza por su desglose, para no contar doble). `% = monto / baseIngresos` por segmento; si la base es 0 → `0%`.

---

## 4. El límite IA / código (criterio crítico para finanzas)

Igual que en el pipeline Summary: **Claude nunca devuelve montos calculados.** Recibe el volcado del export de Contpaqi y devuelve únicamente **estructura y clasificación**:

> "Estas filas son cuentas, sus números están en la columna A y nombres en B; estas filas son `Total Seg.` con cargos en F y abonos en G; estos bloques `Diario` son el desglose de ventas nacionales con el cliente en D; la cuenta `6100-007` pertenece a Gastos Variables; `SUELDOS Y SALARIOS` se traduce como `GENERAL DEP`."

Luego **Python lee los valores de esas celdas, aplica las reglas de signo y hace toda la aritmética y los subtotales.**

**Consecuencia:** un error de la IA puede mover una *clasificación* o una *traducción* (visible y corregible en el resumen de aprobación), pero **jamás inventa un número**. Que NET PROFIT cuadre depende 100% del código determinista — el mismo cálculo ya validado contra Marzo 2026.

---

## 5. Enganche con el contrato `PipelineSpec`

| Pieza del contrato | Contenido en el pipeline P&L | ¿Usa IA? |
|---|---|---|
| **`name`** | `"pl"` | — |
| **`sources`** | 1 archivo: export Contpaqi *"Movimientos Auxiliares por Segmento de Negocio"* (patrón a confirmar con el cliente). | No |
| **`interpret`** | Recibe el volcado de la hoja. Devuelve: tipo de cada fila (máquina de estados §3.1), mapa de columnas, clasificación cuenta→grupo→rubro (§3.2), normalización de clientes de ventas nacionales (§3.4) y traducción ES→EN (§3.5). **Solo estructura, nunca montos.** | **Sí** |
| **`calculate`** | Aplica reglas de signo (§3.3), acumula por cuenta×segmento, calcula INCOMES/EXPENSES/OPERATING/OTHER/TAXES/NET y los `%` (§3.6). Devuelve el **plan**: filas del P&L con todos los montos por segmento y total. Determinista. | No |
| **`write`** | `openpyxl`: escribe las hojas `CONSOLIDATED` y `BY SEGMENT` con el orden de secciones, labels, formato numérico (`#,##0.00`), porcentajes (`0.00%`) y colores de referencia. | No |

**Orden fijo de secciones en la salida** (lo respeta `write`, no la IA): Incomes (National Sales desglosado por cliente + clientes internacionales directos `4110-002` + Accrued Revenue) → Expenses (6001–6008) → **Operating Profit** → Other Incomes (4210/4310/4510) → Other Expenses (6009) → Accrued Taxes (8000) → **Net Profit**.

> El catálogo fijo de clientes/rubros del macro deja de ser el mecanismo que decide qué se muestra; pasa a ser una **plantilla de referencia de orden y labels** para que el P&L conserve la misma forma visual que la referencia del cliente. Lo que entra y cómo se clasifica lo determina la IA sobre los datos reales del mes.

---

## 6. Reglas críticas (invariantes)

1. **La IA interpreta y clasifica; el código calcula.** La IA nunca devuelve un monto.
2. **Regla de signo fija:** ingreso (cuenta `4...`) = `abonos − cargos`; gasto = `cargos − abonos`. Solo en código.
3. **Cuentas no clasificables a un grupo conocido se ignoran** para el P&L, pero **se reportan en alertas** — nunca se calcula con una cuenta que no se entendió.
4. **Nada de cajones silenciosos:** un cliente o rubro nuevo se clasifica a su rubro real y se marca como nuevo en el resumen; no se esconde en "OTHER CLIENTS" / "OTHERS PROJECTS" sin avisar.
5. **Base de % excluye la cuenta lump-sum de ventas nacionales** (se usa su desglose por cliente, para no contar doble).
6. **NET PROFIT debe cuadrar** contra la lógica validada del macro (referencia Marzo 2026). Cualquier desviación es un error a investigar, no a normalizar.
7. **Siempre confirmar antes de escribir** — resumen de aprobación obligatorio.
8. **Confidencialidad:** ningún dato real de P-TRES GROUP (cuentas, clientes, montos, archivo de Contpaqi) se sube a servicios externos ni se incluye en commits del repo. Pruebas con fixtures sintéticos del mismo formato.

---

## 7. Diferencias frente al macro (qué deja de estar hardcodeado)

| En el macro (hardcodeado) | En el agente (dinámico con IA) |
|---|---|
| `GetGrp` — tabla fija de prefijos cuenta→grupo. | La IA clasifica por número y nombre; la tabla queda como guía/validación. |
| `ENNatSales` — alias fijos de clientes de ventas nacionales. | La IA reconoce variantes de razón social del mismo cliente; alias como semilla. |
| `EN` — diccionario fijo ES→EN de cada rubro. | La IA traduce; el diccionario es glosario de referencia para mantener labels idénticos. |
| `InitCatalog` — lista fija de ~46 clientes y rubros que define qué se muestra. | Plantilla de **orden y labels** de referencia; el contenido lo determinan los datos reales. |
| Caso especial `6100-007-033-007 → "ESTACIONAMIENTOS VIAJE"`. | La IA maneja casos especiales y los reporta; documentar los conocidos como referencia. |
| Clientes desconocidos → "OTHER CLIENTS" / "OTHERS PROJECTS" sin aviso. | Se clasifican y se marcan como nuevos en el resumen para validación. |

---

## 8. Pendientes antes de implementar

1. Confirmar con el cliente el **patrón de nombre** del export de Contpaqi en Drive y la carpeta donde vive.
2. Confirmar **qué labels deben quedar idénticos** a la referencia (para fijar el glosario ES→EN como contrato visual) y cuáles pueden traducirse libremente.
3. Definir el **shape del `plan`** que devuelve `calculate` y cómo lo renderiza el frontend (¿el mismo shape que Summary o uno propio del P&L? — pendiente común del contrato `core`).
4. Conseguir un **export de Contpaqi de muestra** (o fixture sintético equivalente) para fijar la estructura real de filas/columnas y validar que NET PROFIT cuadra contra el macro.
5. Decidir **criterio de alerta** para cuentas/clientes/rubros nuevos no vistos antes (umbral, lista de validación, o solo marcar en el resumen).
6. Confirmar si los **segmentos** (`BO`, `CONS OPS`, `ING`, `DIGITAL SOLUTIONS`) son fijos o pueden cambiar — hoy el macro los tiene fijos.
