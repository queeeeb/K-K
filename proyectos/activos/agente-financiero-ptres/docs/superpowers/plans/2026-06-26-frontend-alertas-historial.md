# Frontend Orión + Backend Alertas/Historial — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir alertas e historial (monto anterior) al resumen del backend, y construir el frontend React+Vite+Tailwind de Orión cableado contra la API real.

**Architecture:** El backend agrega dos campos al resumen (`alertas` y `monto_mxn_anterior` en activas) sin tocar el contrato `PipelineSpec`. El frontend vive en `frontend/` dentro de `agente-financiero-ptres/`, con un cliente API centralizado (`api.js`) y una máquina de estados sencilla en `App.jsx`. Los iconos usan `lucide-react` (paquete npm, no UMD). No hay router — la navegación es state puro.

**Tech Stack:** Python/FastAPI (backend), React 18, Vite 5, Tailwind CSS 3, lucide-react, Inter + JetBrains Mono (Google Fonts CDN).

## Global Constraints

- Python ≥ 3.12; sin dependencias nuevas de producción en el backend.
- Sin mock de red en los tests del backend — se usa `TestClient` de FastAPI + monkeypatch de `interpret`.
- Frontend: sin router externo (react-router), sin estado global (redux/zustand) — `useState` en `App.jsx` es suficiente.
- Colores de marca: navy `#0F172A` (tailwind: `slate-900`) + dorado `#A16207`/`amber-400`. **Sin paletas genéricas alternativas.**
- Campo `ref` en canceladas: **fuera de alcance** (no viene de ninguna fuente todavía).
- El campo `monto_mxn_anterior` en activas es igual a `monto_mxn` por ahora (no hay fuente de monto actual); se expone el campo para que el frontend lo muestre sin romper cuando Drive esté conectado.
- `frontend/.gitignore` hereda el `.gitignore` raíz (no sube `.xlsx`/`.xlsm`). El `frontend/` tampoco sube `node_modules/` ni `dist/`.
- Todos los tests del backend deben pasar antes de cada commit: `uv run pytest -q`.
- Rama activa: `docs/spec-agente-provisiones` (mismo PR #5).

---

## File Structure

### Backend (modificaciones)

```
pipelines/summary/
├── calculate.py              ← añade alertas + monto_mxn_anterior a activas
├── spec.py                   ← pasa alertas y counts al detalle; actualiza reporte
└── tests/
    └── test_calculate.py     ← actualiza assertions para nuevos campos
```

### Frontend (nuevo)

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.jsx              ← monta React
    ├── App.jsx               ← máquina de estados: screen + token JWT + plan
    ├── api.js                ← cliente HTTP: login, procesar, confirmar, rechazar
    └── components/
        ├── OrionSky.jsx      ← SVG constelación (fondo del login)
        ├── Brand.jsx         ← logo K&K / Orión
        ├── Sidebar.jsx       ← nav lateral (navy)
        ├── Topbar.jsx        ← barra superior con breadcrumb y usuario
        ├── Money.jsx         ← formatea MXN con JetBrains Mono
        ├── StatusPill.jsx    ← pastillas de color (cancel/active/new/review/cc)
        ├── Delta.jsx         ← ΔMXn con flecha y color
        ├── Stepper.jsx       ← lista de pasos animada
        ├── Tabla.jsx         ← tabla con header coloreado
        ├── Login.jsx         ← pantalla de inicio de sesión
        ├── Panel.jsx         ← panel de ejecución (KPIs + botón Procesar)
        ├── Loader.jsx        ← pantalla de carga (procesando / escribiendo)
        ├── ErrorScreen.jsx   ← error de archivo faltante
        ├── Resumen.jsx       ← revisión del plan (Canceladas/Activas/Nuevas)
        ├── Reporte.jsx       ← confirmación de escritura exitosa
        └── Rechazado.jsx     ← plan descartado
```

---

## Task 1: Backend — alertas + monto_mxn_anterior + counts en reporte

**Files:**
- Modify: `pipelines/summary/calculate.py`
- Modify: `pipelines/summary/spec.py`
- Modify: `pipelines/summary/tests/test_calculate.py`

**Interfaces:**
- Produces:
  - `reconciliar(..., alertas=[]) -> { canceladas, activas, nuevas, alertas }`
  - Cada item de `activas` tiene campo adicional `monto_mxn_anterior: float`
  - `plan["resumen"]` incluye `alertas: list[str]`
  - `plan["detalle"]["counts"]` incluye `{ canceladas, activas, nuevas }`
  - `write(detalle, ...)` retorna `{ archivo, filas_escritas, canceladas, activas, nuevas }`

- [ ] **Step 1: Escribir tests fallidos para nuevos campos**

```python
# pipelines/summary/tests/test_calculate.py
# Agregar al final del archivo existente:

def test_reconciliar_activas_tienen_monto_anterior():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1500, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = []

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_nuevas=[])

    assert resultado["activas"][0]["monto_mxn_anterior"] == 1500
    assert resultado["activas"][0]["monto_mxn"] == 1500


def test_reconciliar_incluye_alertas_vacias_por_defecto():
    resultado = reconciliar([], [], [])
    assert resultado["alertas"] == []


def test_reconciliar_acepta_alertas():
    alertas = ["Proyecto sin código en DS — fila 24."]
    resultado = reconciliar([], [], [], alertas=alertas)
    assert resultado["alertas"] == alertas
```

- [ ] **Step 2: Correr tests y verificar que fallan**

```
cd C:\Users\luism\PROJECTS\K-K\proyectos\activos\agente-financiero-ptres
uv run pytest pipelines/summary/tests/test_calculate.py -v
```

Esperado: 3 tests FAIL (`KeyError: 'monto_mxn_anterior'`, `KeyError: 'alertas'`).

- [ ] **Step 3: Actualizar `calculate.py`**

```python
# pipelines/summary/calculate.py  — reemplazar el archivo completo

def extraer_codigo(texto: str, formato: str) -> str:
    if formato == "limpio":
        return texto.strip()
    if formato == "guion":
        return texto.split("-")[0].strip()
    if formato == "multilinea":
        return texto.split("\n")[0].strip()
    raise ValueError(f"Formato de código desconocido: {formato}")


def reconciliar(
    provisiones_mes_anterior: list[dict],
    facturas_mes: list[dict],
    provisiones_nuevas: list[dict],
    alertas: list[str] | None = None,
) -> dict:
    facturados = {
        extraer_codigo(f["proyecto"], formato="guion")
        for f in facturas_mes
        if f["estado"] in ("Sin pagar", "Pagado")
    }

    canceladas = []
    activas = []
    for provision in provisiones_mes_anterior:
        codigo = extraer_codigo(provision["proyecto"], formato="limpio")
        if codigo in facturados:
            canceladas.append(provision)
        else:
            activas.append({**provision, "monto_mxn_anterior": provision["monto_mxn"]})

    return {
        "canceladas": canceladas,
        "activas": activas,
        "nuevas": list(provisiones_nuevas),
        "alertas": alertas or [],
    }
```

- [ ] **Step 4: Actualizar `spec.py` para incluir counts en detalle y reporte**

```python
# pipelines/summary/spec.py  — reemplazar el archivo completo

from core.pipeline_spec import PipelineSpec
from pipelines.summary.calculate import reconciliar
from pipelines.summary.write import escribir_hoja_mes

SOURCES = [
    "{mes}_Facturacion_sem.xlsx",
    "FORMATO_PROVISIONES_P3_DS_{mes}.xlsx",
    "Provisiones_ES_{mes}.xlsx",
    "PROVISIONES_Overview_Projects_{mes}.xlsx",
]


def build_summary_spec(
    interpret_override,
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
) -> PipelineSpec:
    def calculate(estructura: dict, estado_anterior) -> dict:
        resultado = reconciliar(
            provisiones_mes_anterior=estructura["provisiones_mes_anterior"],
            facturas_mes=estructura["facturas_mes"],
            provisiones_nuevas=estructura["provisiones_nuevas"],
            alertas=estructura.get("alertas", []),
        )
        filas = [
            [
                "", "Provision", 2026, hoja_mes_nuevo.split("_")[1], p["cc"], p["cliente"], "",
                p["proyecto"], "MXN", p["monto_mxn"], 1, p["monto_mxn"], 0, p["monto_mxn"], 0, 0,
                p["monto_mxn"], "", "",
            ]
            for p in resultado["activas"] + resultado["nuevas"]
        ]
        counts = {
            "canceladas": len(resultado["canceladas"]),
            "activas": len(resultado["activas"]),
            "nuevas": len(resultado["nuevas"]),
        }
        return {"resumen": resultado, "detalle": {"filas": filas, "counts": counts}}

    def write(detalle: dict, archivo_destino) -> dict:
        escribir_hoja_mes(
            ruta_origen=ruta_origen,
            ruta_destino=ruta_destino,
            hoja_mes_anterior=hoja_mes_anterior,
            hoja_mes_nuevo=hoja_mes_nuevo,
            filas=detalle["filas"],
        )
        counts = detalle["counts"]
        return {
            "archivo": ruta_destino,
            "filas_escritas": counts["activas"] + counts["nuevas"],
            "canceladas": counts["canceladas"],
            "activas": counts["activas"],
            "nuevas": counts["nuevas"],
        }

    return PipelineSpec(
        name="summary",
        sources=SOURCES,
        interpret=interpret_override,
        calculate=calculate,
        write=write,
    )
```

- [ ] **Step 5: Actualizar el test e2e para el nuevo shape de reporte**

Abrir `pipelines/summary/tests/test_spec_end_to_end.py` y actualizar `test_procesar_confirmar_escribe_archivo`:

```python
def test_procesar_confirmar_escribe_archivo(client):
    test_client, destino, headers = client

    procesar = test_client.post("/procesar/summary", json={"mes": "2026_May"}, headers=headers)
    assert procesar.status_code == 200
    resumen = procesar.json()["resumen"]
    assert len(resumen["canceladas"]) == 1
    assert len(resumen["nuevas"]) == 1
    assert "alertas" in resumen
    assert resumen["activas"][0]["monto_mxn_anterior"] == resumen["activas"][0]["monto_mxn"]

    confirmar = test_client.post("/confirmar/summary", json={"token": procesar.json()["token"]}, headers=headers)
    assert confirmar.status_code == 200
    reporte = confirmar.json()["reporte"]
    assert reporte["canceladas"] == 1
    assert reporte["nuevas"] == 1
    assert "filas_escritas" in reporte

    wb = load_workbook(destino)
    hoja = wb["2026_May"]
    assert hoja.cell(row=13, column=8).value == "26gmx2000.005"
    for row in range(1, 12):
        assert hoja.cell(row=row, column=1).value == f"KPI fila {row}"
```

- [ ] **Step 6: Correr suite completa y verificar verde**

```
uv run pytest -q
```

Esperado: todos los tests pasan (número exacto depende de los que ya existían; sin rojos).

- [ ] **Step 7: Commit**

```
git add pipelines/summary/calculate.py pipelines/summary/spec.py pipelines/summary/tests/test_calculate.py pipelines/summary/tests/test_spec_end_to_end.py
git commit -m "feat(summary): alertas, monto_mxn_anterior en activas, counts en reporte"
```

---

## Task 2: Frontend — scaffold Vite + React + Tailwind

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/.gitignore`

**Interfaces:**
- Produces: servidor de desarrollo `npm run dev` corriendo en `localhost:5173`, mostrando `<h1>Orión</h1>` en fondo `#0F172A`.

- [ ] **Step 1: Crear `frontend/package.json`**

```json
{
  "name": "orion-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lucide-react": "^0.471.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "vite": "^5.4.11"
  }
}
```

- [ ] **Step 2: Crear `frontend/vite.config.js`**

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/login': 'http://127.0.0.1:8000',
      '/procesar': 'http://127.0.0.1:8000',
      '/confirmar': 'http://127.0.0.1:8000',
      '/rechazar': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
```

- [ ] **Step 3: Crear `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 4: Crear `frontend/postcss.config.js`**

```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

- [ ] **Step 5: Crear `frontend/index.html`**

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Orión · K&K</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  </head>
  <body class="bg-slate-900">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Crear `frontend/src/main.jsx`**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 7: Crear `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

.font-ui  { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
.font-num { font-family: 'JetBrains Mono', ui-monospace, monospace; font-feature-settings: 'tnum' 1; }
```

- [ ] **Step 8: Crear `frontend/.gitignore`**

```
node_modules/
dist/
.env
.env.local
```

- [ ] **Step 9: Crear placeholder `frontend/src/App.jsx`**

```jsx
export default function App() {
  return <h1 className="text-white text-3xl font-bold p-8 font-ui">Orión</h1>
}
```

- [ ] **Step 10: Instalar dependencias y verificar servidor**

```
cd C:\Users\luism\PROJECTS\K-K\proyectos\activos\agente-financiero-ptres\frontend
npm install
npm run dev
```

Esperado: `http://localhost:5173` muestra "Orión" en texto blanco sobre fondo oscuro.

- [ ] **Step 11: Commit**

```
git add frontend/
git commit -m "feat(frontend): scaffold Vite + React + Tailwind"
```

---

## Task 3: API client + gestión de token JWT

**Files:**
- Create: `frontend/src/api.js`

**Interfaces:**
- Produces:
  ```js
  api.login(usuario, password)
    → { access_token, token_type, expires_in }   // lanza Error con message si falla

  api.procesar(pipeline, mes)
    → { token, resumen }                          // lanza { locked: true, locked_by } si 409

  api.confirmar(pipeline, token)
    → { reporte }

  api.rechazar(pipeline, token)
    → { status: 'rechazado' }
  ```
  - `api.setToken(jwt)` / `api.clearToken()` — gestión interna en `localStorage`

- [ ] **Step 1: Crear `frontend/src/api.js`**

```js
const BASE = ''  // proxy de Vite redirige al backend

let _token = localStorage.getItem('orion_jwt') || null

function setToken(jwt) {
  _token = jwt
  if (jwt) localStorage.setItem('orion_jwt', jwt)
  else localStorage.removeItem('orion_jwt')
}

function clearToken() {
  setToken(null)
}

async function _fetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  const res = await fetch(BASE + path, { ...options, headers })
  if (res.status === 409) {
    const body = await res.json()
    const err = new Error('Mes bloqueado')
    err.locked = true
    err.locked_by = body.detail?.replace('Locked by ', '') ?? 'otro usuario'
    throw err
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Error ${res.status}`)
  }
  return res.json()
}

async function login(usuario, password) {
  const data = await _fetch('/login', {
    method: 'POST',
    body: JSON.stringify({ usuario, password }),
  })
  setToken(data.access_token)
  return data
}

async function procesar(pipeline, mes) {
  return _fetch(`/procesar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ mes }),
  })
}

async function confirmar(pipeline, token) {
  return _fetch(`/confirmar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

async function rechazar(pipeline, token) {
  return _fetch(`/rechazar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

function getToken() { return _token }

export default { login, procesar, confirmar, rechazar, setToken, clearToken, getToken }
```

- [ ] **Step 2: Verificar manualmente (no hay test unitario para el cliente HTTP)**

Abrir `http://localhost:5173` con el backend corriendo, abrir DevTools → Network, y verificar que `/login` con credenciales correctas retorna 200 con `access_token`. Esto se testea en profundidad en Task 6 (Login screen).

- [ ] **Step 3: Commit**

```
git add frontend/src/api.js
git commit -m "feat(frontend): cliente API con JWT y gestión de token"
```

---

## Task 4: Componentes compartidos (atoms)

**Files:**
- Create: `frontend/src/components/OrionSky.jsx`
- Create: `frontend/src/components/Brand.jsx`
- Create: `frontend/src/components/Money.jsx`
- Create: `frontend/src/components/StatusPill.jsx`
- Create: `frontend/src/components/Delta.jsx`
- Create: `frontend/src/components/Stepper.jsx`
- Create: `frontend/src/components/Tabla.jsx`

**Interfaces:**
- `<OrionSky />` — sin props, fondo SVG del login
- `<Brand dark={bool} />` — logo. `dark=true` (default) para fondo navy
- `<Money value={number} className="" />` — formatea MXN
- `<StatusPill tone="cancel|active|new|review|cc">{children}</StatusPill>`
- `<Delta antes={number} ahora={number} />`
- `<Stepper pasos={[{txt, sub?, icon}]} activo={number} />`
- `<Tabla tone="cancel|active|new" titulo head={[]} align={[bool]} children />`
- `<Row cells={[]} align={[bool]} />` (exportado desde Tabla.jsx)

- [ ] **Step 1: Crear `OrionSky.jsx`**

Copiar directamente la función `OrionSky` y los arrays `ORION`/`FAR`/`NEAR` del prototipo `AgentePrototipo.jsx` sin modificar la lógica SVG:

```jsx
const ORION = [
  { x: 500, y: 70,  r: 3.0, c: "#fff4dd", g: 9  },
  { x: 360, y: 235, r: 6.0, c: "#ffb27a", g: 22 },
  { x: 650, y: 195, r: 4.4, c: "#eaf2ff", g: 15 },
  { x: 430, y: 360, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 505, y: 388, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 580, y: 412, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 320, y: 560, r: 6.0, c: "#cfe2ff", g: 22 },
  { x: 690, y: 540, r: 4.4, c: "#dbe7ff", g: 15 },
  { x: 780, y: 120, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 850, y: 55,  r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 235, y: 205, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 215, y: 100, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 240, y: 345, r: 2.6, c: "#ffe9c2", g: 8  },
]

const _seed = (() => { let s = 1723; return () => (s = (s * 9301 + 49297) % 233280) / 233280 })()
const FAR  = Array.from({ length: 70 }, () => ({ x: _seed()*1000, y: _seed()*620, r: _seed()*0.8+0.3,  o: _seed()*0.35+0.1,  d: _seed()*6 }))
const NEAR = Array.from({ length: 30 }, () => ({ x: _seed()*1000, y: _seed()*620, r: _seed()*1.2+0.7, o: _seed()*0.5+0.45, d: _seed()*5 }))

export default function OrionSky() {
  return (
    <div className="absolute inset-0 overflow-hidden">
      <style>{`
        @keyframes orionTwinkle { 0%,100%{opacity:.15} 50%{opacity:.7} }
        @keyframes orionPulse   { 0%,100%{opacity:.55} 50%{opacity:1} }
        @keyframes nebDrift     { 0%,100%{opacity:.55} 50%{opacity:.95} }
      `}</style>
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid slice" fill="none" aria-hidden="true">
        <defs>
          <radialGradient id="spaceGlow" cx="46%" cy="40%" r="75%">
            <stop offset="0%"   stopColor="#1d3050" />
            <stop offset="42%"  stopColor="#101f36" />
            <stop offset="100%" stopColor="#060c18" />
          </radialGradient>
          <radialGradient id="nebA" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#f59e0b" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="nebB" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#3b6fd4" stopOpacity="0.26" />
            <stop offset="100%" stopColor="#3b6fd4" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%"   stopColor="#ffd79b" stopOpacity="0.0" />
            <stop offset="50%"  stopColor="#ffce8a" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#ffd79b" stopOpacity="0.0" />
          </linearGradient>
          <filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" /></filter>
          <filter id="glow" x="-400%" y="-400%" width="900%" height="900%">
            <feGaussianBlur stdDeviation="6" result="b" />
            <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        <rect width="1000" height="620" fill="url(#spaceGlow)" />
        <g style={{ animation: "nebDrift 9s ease-in-out infinite" }}>
          <ellipse cx="430" cy="380" rx="340" ry="250" fill="url(#nebA)" />
        </g>
        <g style={{ animation: "nebDrift 11s ease-in-out 1.5s infinite" }}>
          <ellipse cx="700" cy="170" rx="280" ry="210" fill="url(#nebB)" />
          <ellipse cx="240" cy="520" rx="240" ry="190" fill="url(#nebB)" />
        </g>
        <g fill="#9fb4d6" filter="url(#soft)">
          {FAR.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
              style={{ animation: `orionTwinkle ${4+s.d}s ease-in-out ${s.d}s infinite` }} />
          ))}
        </g>
        <g fill="#ffffff">
          {NEAR.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
              style={{ animation: `orionTwinkle ${3+s.d}s ease-in-out ${s.d}s infinite` }} />
          ))}
        </g>
        <g fill="none" strokeLinecap="round" strokeLinejoin="round">
          <g stroke="#ffce8a" strokeWidth="3" opacity="0.18" filter="url(#soft)">
            <polyline points="500,70 360,235 650,195 500,70" />
            <polyline points="360,235 430,360 505,388 580,412 650,195" />
            <line x1="430" y1="360" x2="320" y2="560" />
            <line x1="580" y1="412" x2="690" y2="540" />
            <polyline points="650,195 780,120 850,55" />
            <polyline points="360,235 235,205 215,100" />
            <line x1="235" y1="205" x2="240" y2="345" />
          </g>
          <g stroke="url(#lineGrad)" strokeWidth="1.1" opacity="0.65">
            <polyline points="500,70 360,235 650,195 500,70" />
            <polyline points="360,235 430,360 505,388 580,412 650,195" />
            <line x1="430" y1="360" x2="320" y2="560" />
            <line x1="580" y1="412" x2="690" y2="540" />
            <polyline points="650,195 780,120 850,55" />
            <polyline points="360,235 235,205 215,100" />
            <line x1="235" y1="205" x2="240" y2="345" />
          </g>
        </g>
        <g filter="url(#soft)">
          {ORION.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.g} fill={s.c} opacity="0.16"
              style={{ animation: `orionPulse ${5+(i%4)}s ease-in-out ${i*0.4}s infinite` }} />
          ))}
        </g>
        <g filter="url(#glow)">
          {ORION.map((s, i) => (
            <circle key={i} cx={s.x} cy={s.y} r={s.r} fill={s.c}
              style={{ animation: `orionPulse ${4+(i%3)}s ease-in-out ${i*0.3}s infinite` }} />
          ))}
        </g>
      </svg>
    </div>
  )
}
```

- [ ] **Step 2: Crear `Brand.jsx`**

```jsx
export default function Brand({ dark = true }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg font-num text-[11px] font-bold tracking-tight ${dark ? "bg-amber-500 text-slate-900" : "bg-slate-900 text-amber-400"}`}>
        K&amp;K
      </div>
      <div className="leading-tight">
        <p className={`text-lg font-bold leading-none ${dark ? "text-white" : "text-slate-900"}`}>Orión</p>
        <p className={`text-[11px] ${dark ? "text-slate-400" : "text-slate-500"}`}>by K&amp;K</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Crear `Money.jsx`**

```jsx
const fmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })

export default function Money({ value, className = '' }) {
  return <span className={`font-num tabular-nums ${className}`}>{fmt.format(value)}</span>
}
```

- [ ] **Step 4: Crear `StatusPill.jsx`**

```jsx
const TONES = {
  cancel: 'bg-rose-50 text-rose-700 ring-rose-200',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  new:    'bg-blue-50 text-blue-700 ring-blue-200',
  review: 'bg-amber-50 text-amber-800 ring-amber-200',
  cc:     'bg-slate-100 text-slate-600 ring-slate-200',
}

export default function StatusPill({ tone, children }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${TONES[tone]}`}>
      {children}
    </span>
  )
}
```

- [ ] **Step 5: Crear `Delta.jsx`**

```jsx
import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

const fmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })

export default function Delta({ antes, ahora }) {
  const d = ahora - antes
  if (d === 0) return <span className="font-num text-slate-400">—</span>
  const up = d > 0
  return (
    <span className={`inline-flex items-center gap-0.5 font-num font-medium ${up ? 'text-emerald-600' : 'text-rose-600'}`}>
      {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
      {up ? '+' : '−'}{fmt.format(Math.abs(d))}
    </span>
  )
}
```

- [ ] **Step 6: Crear `Stepper.jsx`**

```jsx
import { Check, Loader2 } from 'lucide-react'

export default function Stepper({ pasos, activo }) {
  return (
    <ul className="space-y-1">
      {pasos.map((p, i) => {
        const Icon = p.icon
        const done = i < activo, current = i === activo
        return (
          <li key={i} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${current ? 'bg-slate-50' : ''}`}>
            <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ring-1 transition-colors ${
              done    ? 'bg-emerald-600 text-white ring-emerald-600' :
              current ? 'bg-amber-50 text-amber-700 ring-amber-200' :
                        'bg-white text-slate-300 ring-slate-200'}`}>
              {done ? <Check size={16} /> : current ? <Loader2 size={16} className="animate-spin" /> : <Icon size={15} />}
            </span>
            <div className="min-w-0">
              <p className={`text-sm leading-tight ${done ? 'text-slate-400' : current ? 'font-semibold text-slate-900' : 'text-slate-400'}`}>{p.txt}</p>
              {p.sub && <p className="text-xs text-slate-400">{p.sub}</p>}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
```

- [ ] **Step 7: Crear `Tabla.jsx`**

```jsx
import React from 'react'

const TONE_BAR = { cancel: 'bg-rose-500', active: 'bg-emerald-500', new: 'bg-blue-500' }

export function Row({ cells, align }) {
  return (
    <tr className="transition-colors hover:bg-slate-50/70">
      {cells.map((c, j) => (
        <td key={j} className={`px-4 py-2.5 ${align[j] ? 'text-right' : 'text-left'} ${j === 1 ? 'font-medium text-slate-800' : 'text-slate-600'}`}>
          {c}
        </td>
      ))}
    </tr>
  )
}

export default function Tabla({ tone, titulo, sub, head, align, children }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-4 py-3">
        <span className={`h-2.5 w-2.5 rounded-full ${TONE_BAR[tone]}`} />
        <h3 className="text-sm font-semibold text-slate-900">{titulo}</h3>
        <span className="font-num text-xs text-slate-400">{React.Children.count(children)}</span>
        <span className="ml-auto hidden text-xs text-slate-400 sm:inline">{sub}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              {head.map((h, i) => (
                <th key={h} className={`px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 ${align[i] ? 'text-right' : 'text-left'}`}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">{children}</tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 8: Verificar en el dev server que no hay errores de consola**

Importar temporalmente `Brand` en `App.jsx`, correr `npm run dev`, verificar que el logo renderiza sin errores. Luego revertir `App.jsx` al placeholder.

- [ ] **Step 9: Commit**

```
git add frontend/src/components/
git commit -m "feat(frontend): atoms — OrionSky, Brand, Money, StatusPill, Delta, Stepper, Tabla"
```

---

## Task 5: App shell — App.jsx, Sidebar, Topbar

**Files:**
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/components/Sidebar.jsx`
- Create: `frontend/src/components/Topbar.jsx`

**Interfaces:**
- `App.jsx` exporta la máquina de estados con screen: `'login' | 'panel' | 'processing' | 'error' | 'summary' | 'writing' | 'report' | 'rejected'`
- Props de contexto descendentes: `usuario`, `pipeline`, `mes`, `plan` (resumen del backend), `planToken`, `reporte`
- `<Sidebar pipeline setPipeline onLogout />` (pipelines: `summary` activo, `pl` beta, `cashflow` pronto)
- `<Topbar usuario pact mes />` donde `pact = { id, full, desc, icon }`

- [ ] **Step 1: Reemplazar `App.jsx` con shell completo**

```jsx
import { useState } from 'react'
import { FileSpreadsheet, TrendingUp, Wallet } from 'lucide-react'
import api from './api'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Login    from './components/Login'
import Panel    from './components/Panel'
import Loader   from './components/Loader'
import ErrorScreen from './components/ErrorScreen'
import Resumen  from './components/Resumen'
import Reporte  from './components/Reporte'
import Rechazado from './components/Rechazado'

export const PIPELINES = [
  { id: 'summary',  nombre: 'Summary',   full: 'Summary · Provisiones',      desc: 'Hoja mensual de provisiones',   icon: FileSpreadsheet, estado: 'activo' },
  { id: 'pl',       nombre: 'P&L',       full: 'P&L · Estado de resultados', desc: 'Estado de resultados mensual',  icon: TrendingUp,      estado: 'construccion' },
  { id: 'cashflow', nombre: 'Cash Flow', full: 'Cash Flow · Cobranza',       desc: 'Estatus de cobranza / AR',      icon: Wallet,          estado: 'proximamente' },
]

// mes display "2026 — Mayo" ↔ api key "2026-05"
const MESES = [
  { label: '2026 — Marzo', value: '2026-03' },
  { label: '2026 — Abril', value: '2026-04' },
  { label: '2026 — Mayo',  value: '2026-05' },
  { label: '2026 — Junio', value: '2026-06' },
]

export { MESES }

export default function App() {
  const [screen,     setScreen]     = useState(api.getToken() ? 'panel' : 'login')
  const [usuario,    setUsuario]    = useState('')
  const [pipeline,   setPipeline]   = useState('summary')
  const [mes,        setMes]        = useState('2026-05')
  const [plan,       setPlan]       = useState(null)   // { resumen, token }
  const [reporte,    setReporte]    = useState(null)
  const [errorMsg,   setErrorMsg]   = useState('')
  const [lockedBy,   setLockedBy]   = useState('')

  const pact = PIPELINES.find(p => p.id === pipeline)

  function handleLogout() {
    api.clearToken()
    setUsuario('')
    setPlan(null)
    setReporte(null)
    setScreen('login')
  }

  const sharedProps = { usuario, pipeline, setPipeline, mes, setMes, plan, planToken: plan?.token, reporte, pact, MESES, lockedBy, errorMsg }

  if (screen === 'login') {
    return <Login onSuccess={(u) => { setUsuario(u); setScreen('panel') }} />
  }

  return (
    <div className="font-ui min-h-screen bg-slate-100 text-slate-900 antialiased flex">
      <Sidebar pipeline={pipeline} setPipeline={setPipeline} onLogout={handleLogout} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar usuario={usuario} pact={pact} mes={mes} MESES={MESES} />
        <main className="flex-1 overflow-y-auto px-6 py-6 lg:px-10">
          <div className="mx-auto max-w-6xl">
            {screen === 'panel' && (
              <Panel
                {...sharedProps}
                onProcesar={async () => {
                  setScreen('processing')
                  try {
                    const data = await api.procesar(pipeline, mes)
                    setPlan(data)
                    setScreen('summary')
                  } catch (err) {
                    if (err.locked) {
                      setLockedBy(err.locked_by)
                      setScreen('panel')
                    } else {
                      setErrorMsg(err.message)
                      setScreen('error')
                    }
                  }
                }}
              />
            )}
            {screen === 'processing' && <Loader titulo={`Procesando ${pact.full}`} sub={MESES.find(m => m.value === mes)?.label ?? mes} mode="processing" />}
            {screen === 'error'      && <ErrorScreen msg={errorMsg} onBack={() => { setErrorMsg(''); setScreen('panel') }} />}
            {screen === 'summary'    && (
              <Resumen
                pact={pact}
                mes={MESES.find(m => m.value === mes)?.label ?? mes}
                resumen={plan?.resumen}
                onConfirmar={async () => {
                  setScreen('writing')
                  try {
                    const data = await api.confirmar(pipeline, plan.token)
                    setReporte(data.reporte)
                    setPlan(null)
                    setScreen('report')
                  } catch (err) {
                    setErrorMsg(err.message)
                    setScreen('error')
                  }
                }}
                onRechazar={async () => {
                  await api.rechazar(pipeline, plan.token).catch(() => {})
                  setPlan(null)
                  setScreen('rejected')
                }}
              />
            )}
            {screen === 'writing'   && <Loader titulo="Escribiendo y subiendo a Drive" sub={MESES.find(m => m.value === mes)?.label ?? mes} mode="writing" />}
            {screen === 'report'    && <Reporte reporte={reporte} mes={MESES.find(m => m.value === mes)?.label ?? mes} onBack={() => setScreen('panel')} />}
            {screen === 'rejected'  && <Rechazado onBack={() => setScreen('panel')} />}
          </div>
        </main>
        <footer className="border-t border-slate-200 bg-white px-6 py-4 text-center lg:px-10">
          <p className="text-xs text-slate-500">
            <span className="font-semibold text-slate-700">Orión by K&amp;K</span> — La propiedad intelectual y el agente pertenecen a <span className="font-semibold text-slate-700">K&amp;K</span>. © 2026 K&amp;K · Uso interno.
          </p>
        </footer>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Crear `Sidebar.jsx`**

```jsx
import { LayoutDashboard, Clock, FileText, LogOut } from 'lucide-react'
import Brand from './Brand'
import { PIPELINES } from '../App'

function NavItem({ icon: Icon, active, children }) {
  return (
    <a className={`mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors cursor-pointer ${
      active ? 'bg-white/10 font-medium text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>
      <Icon size={17} className={active ? 'text-amber-400' : ''} /> {children}
    </a>
  )
}

export default function Sidebar({ pipeline, setPipeline, onLogout }) {
  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-slate-900 lg:flex">
      <div className="flex h-16 items-center border-b border-white/10 px-5"><Brand /></div>
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        <div>
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">General</p>
          <NavItem icon={LayoutDashboard} active>Panel</NavItem>
          <NavItem icon={Clock}>Historial</NavItem>
          <NavItem icon={FileText}>Bitácora</NavItem>
        </div>
        <div>
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Pipelines</p>
          {PIPELINES.map(p => {
            const Icon = p.icon
            const sel = pipeline === p.id
            const dis = p.estado !== 'activo'
            return (
              <button key={p.id} disabled={dis} onClick={() => !dis && setPipeline(p.id)}
                className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  sel ? 'bg-white/10 text-white' : dis ? 'cursor-not-allowed text-slate-600' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>
                <Icon size={17} className={sel ? 'text-amber-400' : ''} />
                <span className="flex-1 text-left">{p.nombre}</span>
                {p.estado === 'construccion' && <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-400">beta</span>}
                {p.estado === 'proximamente' && <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-500">pronto</span>}
              </button>
            )
          })}
        </div>
      </nav>
      <div className="border-t border-white/10 p-3">
        <button onClick={onLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white">
          <LogOut size={17} /> Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 3: Crear `Topbar.jsx`**

```jsx
import { ChevronRight, Calendar, Search, Bell, ShieldCheck } from 'lucide-react'

export default function Topbar({ usuario, pact, mes, MESES }) {
  const mesLabel = MESES.find(m => m.value === mes)?.label ?? mes
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 backdrop-blur lg:px-10">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400">Pipelines</span>
        <ChevronRight size={14} className="text-slate-300" />
        <span className="font-semibold text-slate-900">{pact?.full}</span>
        <span className="ml-2 hidden items-center gap-1.5 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 sm:inline-flex">
          <Calendar size={13} /> {mesLabel}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex"><Search size={17} /></button>
        <button className="relative hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex">
          <Bell size={17} /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-amber-500" />
        </button>
        <div className="hidden items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 md:flex">
          <ShieldCheck size={13} /><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Sesión segura · 8h
        </div>
        <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
            {(usuario || 'u').slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden leading-tight sm:block">
            <p className="text-sm font-medium text-slate-800">{usuario}</p>
            <p className="text-[11px] text-slate-400">K&amp;K · Finanzas</p>
          </div>
        </div>
      </div>
    </header>
  )
}
```

- [ ] **Step 4: Verificar en dev server**

Con `npm run dev` abierto, el shell debe renderizar sidebar navy + topbar. Las pantallas de contenido mostrarán `undefined` por ahora — es esperado.

- [ ] **Step 5: Commit**

```
git add frontend/src/App.jsx frontend/src/components/Sidebar.jsx frontend/src/components/Topbar.jsx
git commit -m "feat(frontend): App shell — máquina de estados, Sidebar, Topbar"
```

---

## Task 6: Pantalla Login

**Files:**
- Create: `frontend/src/components/Login.jsx`

**Interfaces:**
- `<Login onSuccess={(usuario: string) => void} />`
- Llama `api.login(usuario, password)`, luego `onSuccess(usuario)`.
- Error de credenciales → mensaje inline (sin modal).

- [ ] **Step 1: Crear `Login.jsx`**

```jsx
import { useState } from 'react'
import { Lock, LogIn, Building2 } from 'lucide-react'
import OrionSky from './OrionSky'
import api from '../api'

export default function Login({ onSuccess }) {
  const [usuario,  setUsuario]  = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.login(usuario.trim(), password)
      onSuccess(usuario.trim())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="font-ui relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-900 px-6">
      <OrionSky />
      <div className="relative w-full max-w-sm">
        <div className="mb-4 mt-6 flex flex-col items-center text-center">
          <h1 className="text-3xl font-bold tracking-tight text-white">Orión</h1>
          <p className="mt-1 text-sm font-medium tracking-wide text-amber-400">by K&amp;K</p>
        </div>
        <div className="rounded-2xl bg-white/40 p-7 shadow-2xl ring-1 ring-white/30 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-slate-900">Iniciar sesión</h2>
          <p className="mt-1 text-sm text-slate-700">Accede con tu usuario individual</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Usuario</label>
              <div className="relative">
                <Building2 size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={usuario} onChange={e => setUsuario(e.target.value)} placeholder="ana.lopez" required
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Contraseña</label>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="••••••••" required
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}
            <button type="submit" disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:ring-4 focus:ring-slate-900/20 disabled:opacity-60">
              <LogIn size={16} /> {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>
          <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-slate-400">
            <Lock size={12} /> Autenticación JWT · expira en 8h · sin registro público
          </p>
        </div>
        <p className="mt-6 text-center text-xs text-slate-500">© 2026 K&amp;K · Orión es propiedad intelectual de K&amp;K</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verificar flujo de login con backend corriendo**

```
# Terminal 1 — backend
cd C:\Users\luism\PROJECTS\K-K\proyectos\activos\agente-financiero-ptres
uv run uvicorn core.api:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

Navegar a `http://localhost:5173`. Ingresar usuario/contraseña de un usuario creado con `crear_usuario.py`. Verificar que redirige al panel (aunque el panel muestre algo temporal por ahora).

Intentar con contraseña incorrecta: debe aparecer mensaje de error en rojo.

- [ ] **Step 3: Commit**

```
git add frontend/src/components/Login.jsx
git commit -m "feat(frontend): pantalla Login con JWT"
```

---

## Task 7: Pantalla Panel

**Files:**
- Create: `frontend/src/components/Panel.jsx`

**Interfaces:**
- `<Panel pact mes setMes MESES lockedBy onProcesar />`
- Muestra KPIs estáticos (último cierre, provisiones activas, total provisionado — datos reales vendrán de un endpoint de historial futuro; por ahora valores fijos del prototipo).
- Si `lockedBy !== ''` → banner de bloqueo con nombre del usuario.
- `onProcesar` llama al handler en `App.jsx` (que a su vez llama `api.procesar`).

- [ ] **Step 1: Crear `Panel.jsx`**

```jsx
import { CheckCircle2, TrendingUp, Wallet, Calendar, ChevronDown, ChevronRight, Cpu, Lock } from 'lucide-react'
import Money from './Money'
import StatusPill from './StatusPill'

const KPIS = [
  { l: 'Último cierre',      v: 'Abril 2026', sub: '8 filas escritas',   icon: CheckCircle2, tone: 'text-emerald-600', num: false },
  { l: 'Provisiones activas', v: '23',          sub: 'arrastradas al mes', icon: TrendingUp,   tone: 'text-slate-900',  num: false },
  { l: 'Total provisionado',  v: 3_325_000,     sub: 'cierre anterior',    icon: Wallet,       tone: 'text-slate-900',  num: true  },
]

export default function Panel({ pact, mes, setMes, MESES, lockedBy, onProcesar }) {
  const Icon = pact.icon

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Panel de proceso</h1>
        <p className="text-sm text-slate-500">Elige el mes y procésalo. Verás un resumen para aprobar antes de escribir nada.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {KPIS.map(k => (
          <div key={k.l} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{k.l}</p>
              <k.icon size={16} className={k.tone} />
            </div>
            {k.num
              ? <p className="mt-2 font-num text-2xl font-bold tabular-nums text-slate-900"><Money value={k.v} /></p>
              : <p className="mt-2 text-2xl font-bold text-slate-900">{k.v}</p>
            }
            <p className="mt-0.5 text-xs text-slate-400">{k.sub}</p>
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="flex items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-5 py-3.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-amber-400"><Icon size={18} /></span>
          <div>
            <p className="text-sm font-semibold text-slate-900">{pact.full}</p>
            <p className="text-xs text-slate-500">{pact.desc}</p>
          </div>
          <StatusPill tone="active"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Disponible</StatusPill>
        </div>

        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="w-full max-w-xs">
            <label className="mb-1.5 block text-sm font-medium text-slate-700">Mes a procesar</label>
            <div className="relative">
              <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <select value={mes} onChange={e => setMes(e.target.value)}
                className="w-full appearance-none rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-9 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10">
                {MESES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
              </select>
              <ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
            </div>
          </div>
          <button onClick={onProcesar} disabled={!!lockedBy}
            className={`flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition focus:ring-4 ${
              lockedBy ? 'cursor-not-allowed bg-slate-300' : 'bg-slate-900 hover:bg-slate-800 focus:ring-slate-900/20'}`}>
            Procesar {pact.nombre} <ChevronRight size={16} />
          </button>
        </div>

        {lockedBy && (
          <div className="mx-5 mb-5 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3.5">
            <Lock size={18} className="mt-0.5 shrink-0 text-amber-600" />
            <div className="text-sm">
              <p className="font-semibold text-amber-900">Mes bloqueado — lo está procesando {lockedBy}.</p>
              <p className="text-amber-700">No puedes iniciar otro proceso hasta que confirme o rechace. Se le notificó que intentaste entrar.</p>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 border-t border-slate-100 px-5 py-3">
          <Cpu size={14} className="text-slate-400" />
          <p className="text-xs text-slate-500">La IA interpreta la estructura de los archivos; <span className="font-medium text-slate-700">el sistema calcula los montos</span> de forma determinista.</p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verificar en dev server**

Navegar a `http://localhost:5173`, hacer login, verificar que el Panel muestra los KPIs, el selector de mes y el botón "Procesar Summary". Cambiar mes y confirmar que el select funciona.

- [ ] **Step 3: Commit**

```
git add frontend/src/components/Panel.jsx
git commit -m "feat(frontend): pantalla Panel con selector de mes"
```

---

## Task 8: Pantallas Loader y ErrorScreen

**Files:**
- Create: `frontend/src/components/Loader.jsx`
- Create: `frontend/src/components/ErrorScreen.jsx`

**Interfaces:**
- `<Loader titulo sub mode="processing"|"writing" />` — el `mode` determina qué lista de pasos mostrar
- `<ErrorScreen msg onBack />` — muestra `msg` o mensaje genérico si está vacío

- [ ] **Step 1: Crear `Loader.jsx`**

```jsx
import { Loader2, Database, Sparkles, FileCheck, Calculator, FileSpreadsheet, CloudUpload, ShieldCheck } from 'lucide-react'
import Stepper from './Stepper'

const PASOS_PROCESO = [
  { txt: 'Localizando archivos en Google Drive',        icon: Database },
  { txt: 'Interpretando fuentes con IA', sub: 'Facturación · DS · Engineering · Consulting', icon: Sparkles },
  { txt: 'Reconciliando provisiones vs. facturas',      icon: FileCheck },
  { txt: 'Calculando montos', sub: 'motor determinista', icon: Calculator },
  { txt: 'Generando resumen para revisión',             icon: FileSpreadsheet },
]

const PASOS_ESCRITURA = [
  { txt: 'Duplicando hoja del mes anterior',                                    icon: FileSpreadsheet },
  { txt: 'Escribiendo Sección B', sub: 'sin tocar el tablero KPI (filas 1–11)', icon: Calculator },
  { txt: 'Subiendo archivo a Google Drive',                                     icon: CloudUpload },
]

export default function Loader({ titulo, sub, mode }) {
  const pasos = mode === 'writing' ? PASOS_ESCRITURA : PASOS_PROCESO
  const [paso, setPaso] = useState(0)

  useEffect(() => {
    setPaso(0)
    const t = setInterval(() => {
      setPaso(p => {
        if (p >= pasos.length - 1) { clearInterval(t); return p }
        return p + 1
      })
    }, 900)
    return () => clearInterval(t)
  }, [mode])

  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-amber-400">
            <Loader2 size={18} className="animate-spin" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-slate-900">{titulo}</h2>
            <p className="font-num text-xs text-slate-500">{sub}</p>
          </div>
        </div>
        <Stepper pasos={pasos} activo={paso} />
        {mode === 'processing' && (
          <p className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-400">
            <ShieldCheck size={14} /> Nada se escribe todavía. Al terminar verás un resumen para aprobar.
          </p>
        )}
      </div>
    </div>
  )
}

// Nota: necesita importar useState y useEffect de React
```

Agregar imports al inicio del archivo:

```jsx
import { useState, useEffect } from 'react'
import { Loader2, Database, Sparkles, FileCheck, Calculator, FileSpreadsheet, CloudUpload, ShieldCheck } from 'lucide-react'
import Stepper from './Stepper'
```

- [ ] **Step 2: Crear `ErrorScreen.jsx`**

```jsx
import { XCircle, ArrowLeft } from 'lucide-react'

export default function ErrorScreen({ msg, onBack }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-rose-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-600">
        <XCircle size={26} />
      </div>
      <h2 className="text-lg font-bold text-slate-900">Proceso detenido</h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">
        {msg || 'Ocurrió un error inesperado. No se modificó ningún archivo.'}
      </p>
      <button onClick={onBack} className="mt-6 inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  )
}
```

- [ ] **Step 3: Verificar en dev server**

Forzar `screen = 'processing'` en `App.jsx` temporalmente y verificar que el stepper anima correctamente. Luego `screen = 'error'` con un mensaje de prueba.

- [ ] **Step 4: Commit**

```
git add frontend/src/components/Loader.jsx frontend/src/components/ErrorScreen.jsx
git commit -m "feat(frontend): Loader animado y ErrorScreen"
```

---

## Task 9: Pantalla Resumen

**Files:**
- Create: `frontend/src/components/Resumen.jsx`

**Interfaces:**
- `<Resumen pact mes resumen onConfirmar onRechazar />`
- `resumen` shape del backend: `{ canceladas, activas, nuevas, alertas }`
- Cada activa tiene `monto_mxn_anterior` y `monto_mxn`
- Muestra totales calculados en el frontend por segmento (CC)

- [ ] **Step 1: Crear `Resumen.jsx`**

```jsx
import { ShieldCheck, AlertTriangle, Clock, CheckCircle2, XCircle } from 'lucide-react'
import Money from './Money'
import StatusPill from './StatusPill'
import Delta from './Delta'
import Tabla, { Row } from './Tabla'

function calcularTotales(resumen) {
  const mapa = {}
  const sumar = (items, signo = 1) => {
    items.forEach(r => {
      if (!mapa[r.cc]) mapa[r.cc] = { seg: String(r.cc), cc: r.cc, total: 0 }
      mapa[r.cc].total += signo * (r.monto_mxn ?? 0)
    })
  }
  sumar(resumen.activas)
  sumar(resumen.nuevas)
  return Object.values(mapa).sort((a, b) => a.cc - b.cc)
}

export default function Resumen({ pact, mes, resumen, onConfirmar, onRechazar }) {
  if (!resumen) return null
  const total = resumen.canceladas.length + resumen.activas.length + resumen.nuevas.length
  const totales = calcularTotales(resumen)

  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Resumen para revisión</h1>
            <StatusPill tone="review"><Clock size={12} /> Pendiente de aprobación</StatusPill>
          </div>
          <p className="text-sm text-slate-500">{pact.full} · <span className="font-num">{mes}</span> · {total} filas listas para escribir.</p>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3">
        <ShieldCheck size={18} className="shrink-0 text-amber-700" />
        <p className="text-sm font-medium text-amber-900">Nada se ha guardado todavía. Revisa los movimientos y aprueba para escribir en el Summary.</p>
      </div>

      {totales.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          {totales.map(t => (
            <div key={t.cc} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">CC {t.cc}</p>
              </div>
              <p className="mt-2 font-num text-2xl font-bold tabular-nums text-slate-900"><Money value={t.total} /></p>
            </div>
          ))}
        </div>
      )}

      {resumen.alertas.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-white p-4">
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800"><AlertTriangle size={16} /> Alertas · {resumen.alertas.length}</p>
          <ul className="space-y-1.5 text-sm text-slate-600">
            {resumen.alertas.map((a, i) => (
              <li key={i} className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-400" />{a}</li>
            ))}
          </ul>
        </div>
      )}

      <Tabla tone="cancel" titulo="Canceladas" sub="Ya se facturaron — cambian de estatus en su fila"
        head={['CC', 'Cliente', 'Proyecto', 'Monto MXN']} align={[false, false, false, true]}>
        {resumen.canceladas.map((r, i) => (
          <Row key={i} align={[false, false, false, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn} className="text-slate-500 line-through" />,
          ]} />
        ))}
      </Tabla>

      <Tabla tone="active" titulo="Activas" sub="Siguen como provisión — anterior vs. nuevo"
        head={['CC', 'Cliente', 'Proyecto', 'Antes', 'Ahora', 'Δ']} align={[false, false, false, true, true, true]}>
        {resumen.activas.map((r, i) => (
          <Row key={i} align={[false, false, false, true, true, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn_anterior} className="text-slate-400" />,
            <Money value={r.monto_mxn} className="font-medium text-slate-900" />,
            <Delta antes={r.monto_mxn_anterior} ahora={r.monto_mxn} />,
          ]} />
        ))}
      </Tabla>

      <Tabla tone="new" titulo="Nuevas" sub="Provisiones nuevas detectadas este mes"
        head={['CC', 'Cliente', 'Proyecto', 'Monto MXN']} align={[false, false, false, true]}>
        {resumen.nuevas.map((r, i) => (
          <Row key={i} align={[false, false, false, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn} className="font-medium text-slate-900" />,
          ]} />
        ))}
      </Tabla>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur lg:left-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-3.5 sm:flex-row sm:items-center sm:justify-between lg:px-10">
          <p className="text-xs text-slate-500">
            <span className="font-num font-semibold text-slate-800">{total} filas</span> se escribirán en la hoja <span className="font-num">{mes}</span>. Rechazar descarta el plan; ningún archivo se modifica.
          </p>
          <div className="flex gap-3">
            <button onClick={onRechazar} className="flex items-center gap-2 rounded-lg border border-rose-200 bg-white px-4 py-2 text-sm font-medium text-rose-600 transition hover:bg-rose-50 focus:ring-4 focus:ring-rose-500/15">
              <XCircle size={16} /> Rechazar
            </button>
            <button onClick={onConfirmar} className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus:ring-4 focus:ring-emerald-600/25">
              <CheckCircle2 size={16} /> Confirmar y escribir
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verificar con datos reales del backend**

Con backend corriendo y un usuario creado:
1. Login → Panel → Procesar Summary (cualquier mes)
2. Verificar que el resumen muestra las tablas con datos reales del backend
3. Verificar que las alertas se muestran (o la sección se oculta si `alertas.length === 0`)
4. Verificar que `Δ` muestra `—` cuando `antes === ahora`

- [ ] **Step 3: Commit**

```
git add frontend/src/components/Resumen.jsx
git commit -m "feat(frontend): pantalla Resumen con datos reales del backend"
```

---

## Task 10: Pantallas Reporte y Rechazado

**Files:**
- Create: `frontend/src/components/Reporte.jsx`
- Create: `frontend/src/components/Rechazado.jsx`

**Interfaces:**
- `<Reporte reporte mes onBack />` donde `reporte = { archivo, filas_escritas, canceladas, activas, nuevas }`
- `<Rechazado onBack />`

- [ ] **Step 1: Crear `Reporte.jsx`**

```jsx
import { CheckCircle2, AlertTriangle, ArrowLeft } from 'lucide-react'

export default function Reporte({ reporte, mes, onBack }) {
  if (!reporte) return null
  const items = [
    ['Canceladas', reporte.canceladas,   'text-rose-600'],
    ['Provisiones', reporte.activas,     'text-emerald-600'],
    ['Nuevas',     reporte.nuevas,       'text-blue-600'],
    ['Total',      reporte.filas_escritas, 'text-slate-900'],
  ]
  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div className="rounded-xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <CheckCircle2 size={26} />
        </div>
        <h2 className="text-lg font-bold text-slate-900">Hoja escrita correctamente</h2>
        <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">
          Hoja <span className="font-num font-medium text-slate-900">{mes.replace(' — ', '_')}</span> · subida a Google Drive.
        </p>
        <div className="mt-6 grid grid-cols-4 gap-2">
          {items.map(([l, n, c]) => (
            <div key={l} className="rounded-lg border border-slate-100 bg-slate-50 py-3">
              <p className={`font-num text-2xl font-bold tabular-nums ${c}`}>{n}</p>
              <p className="text-[11px] uppercase tracking-wide text-slate-400">{l}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <AlertTriangle size={17} className="mt-0.5 shrink-0 text-amber-600" />
        <div className="text-sm">
          <p className="font-semibold text-amber-900">Pendientes manuales</p>
          <p className="text-amber-800">Capturar tipos de cambio USD/EUR/CAD en el tablero KPI (filas 6–8).</p>
        </div>
      </div>
      <button onClick={onBack} className="mx-auto flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Crear `Rechazado.jsx`**

```jsx
import { XCircle, ArrowLeft } from 'lucide-react'

export default function Rechazado({ onBack }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        <XCircle size={26} />
      </div>
      <h2 className="text-lg font-bold text-slate-900">Plan descartado</h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">No se modificó ningún archivo. El mes queda libre para volver a procesarse.</p>
      <button onClick={onBack} className="mx-auto mt-6 flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  )
}
```

- [ ] **Step 3: Prueba del flujo completo**

Con backend corriendo:
1. Login → Panel → Procesar → (esperar animación) → Resumen
2. Revisar tablas con datos reales
3. Clic "Confirmar y escribir" → (esperar animación) → Reporte
4. Verificar que los counts del reporte coinciden con lo que se procesó
5. Repetir con "Rechazar" → verificar pantalla Rechazado
6. Intentar procesar el mismo mes dos veces en paralelo → verificar banner de bloqueo

- [ ] **Step 4: Suite backend final**

```
cd C:\Users\luism\PROJECTS\K-K\proyectos\activos\agente-financiero-ptres
uv run pytest -q
```

Todos los tests deben pasar.

- [ ] **Step 5: Commit final**

```
git add frontend/src/components/Reporte.jsx frontend/src/components/Rechazado.jsx
git commit -m "feat(frontend): Reporte y Rechazado — flujo completo e2e"
```

---

## Self-Review

**1. Spec coverage:**

| Req | Tarea |
|-----|-------|
| Alertas en resumen | Task 1 |
| monto_mxn_anterior en activas | Task 1 |
| counts en reporte (canceladas/activas/nuevas) | Task 1 |
| Flujo login → JWT | Tasks 3, 6 |
| Panel con selector de mes | Task 7 |
| Banner de bloqueo (409) | Task 5 (App.jsx), Task 7 (Panel) |
| Loader animado (procesar y escribir) | Task 8 |
| Error de archivo faltante | Task 8 |
| Resumen con datos reales | Task 9 |
| Confirmar → write → Drive | Tasks 5, 10 |
| Rechazar → descarta plan | Tasks 5, 10 |
| Design system navy+dorado, Inter+JetBrains | Tasks 2, 4 |
| Constelación Orión en login | Task 4 (OrionSky) |
| `ref` en canceladas | **Fuera de alcance** |
| Sin `node_modules/dist` en git | Task 2 (.gitignore) |

**2. Placeholders:** Ninguno. Todos los pasos tienen código completo.

**3. Type consistency:**
- `resumen.activas[i].monto_mxn_anterior` — definido en Task 1 (`calculate.py`), usado en Task 9 (`Resumen.jsx`). ✓
- `resumen.alertas` — definido en Task 1, usado en Task 9. ✓
- `reporte.canceladas`, `reporte.activas`, `reporte.nuevas` — definidos en Task 1 (`spec.py write()`), usados en Task 10 (`Reporte.jsx`). ✓
- `api.procesar(pipeline, mes)` → `{ token, resumen }` — definido en Task 3, consumido en Task 5 (`App.jsx`). ✓
- `MESES` — exportado de `App.jsx`, importado en `Panel.jsx` y `Topbar.jsx`. ✓
- `PIPELINES` — exportado de `App.jsx`, importado en `Sidebar.jsx`. ✓
