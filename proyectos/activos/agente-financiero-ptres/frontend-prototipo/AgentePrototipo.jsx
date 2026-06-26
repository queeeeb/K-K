import React, { useState, useEffect, useRef } from "react";
import {
  LogIn, LogOut, FileSpreadsheet, TrendingUp, Wallet, ChevronRight,
  Lock, ShieldCheck, Cpu, AlertTriangle, CheckCircle2, XCircle,
  Loader2, ArrowLeft, Calendar, Database, Sparkles, Calculator,
  FileCheck, CloudUpload, Info, ChevronDown,
} from "lucide-react";

/* =========================================================================
   Agente Financiero P3 — Prototipo de interfaz (datos 100% ficticios)
   Plataforma interna que automatiza entregables financieros mensuales.
   Flujo: login → panel → procesar → resumen (revisión) → confirmar/rechazar.
   ========================================================================= */

// ---------- Datos ficticios ----------
const PIPELINES = [
  { id: "summary", nombre: "Summary (Provisiones)", desc: "Hoja mensual de provisiones", icon: FileSpreadsheet, estado: "activo" },
  { id: "pl", nombre: "P&L (Estado de resultados)", desc: "Estado de resultados mensual", icon: TrendingUp, estado: "construccion" },
  { id: "cashflow", nombre: "Cash Flow (Cobranza)", desc: "Estatus de cobranza / AR", icon: Wallet, estado: "proximamente" },
];

const MESES = [
  "2026 — Marzo", "2026 — Abril", "2026 — Mayo", "2026 — Junio",
];

const mxn = (n) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(n);

const RESUMEN = {
  mes: "2026 — Mayo",
  totales: [
    { seg: "CONSULTING", facturacion: 1_840_000, canceladas: 420_000, total: 1_420_000 },
    { seg: "DS", facturacion: 960_000, canceladas: 180_000, total: 780_000 },
    { seg: "ENGINEERING", facturacion: 1_220_000, canceladas: 95_000, total: 1_125_000 },
  ],
  canceladas: [
    { cc: 3000, cliente: "Acme Corp", proyecto: "Aurora", monto: 240_000, ref: "C-2026-00109" },
    { cc: 3000, cliente: "Globex", proyecto: "Helios", monto: 180_000, ref: "C-2026-00114" },
    { cc: 7000, cliente: "Initech", proyecto: "Nimbus", monto: 180_000, ref: "C-2026-00121" },
  ],
  activas: [
    { cc: 3000, cliente: "Umbrella", proyecto: "Vega", antes: 320_000, ahora: 320_000 },
    { cc: 2000, cliente: "Stark Ind.", proyecto: "Orion", antes: 410_000, ahora: 455_000 },
    { cc: 7000, cliente: "Soylent", proyecto: "Lyra", antes: 150_000, ahora: 132_000 },
  ],
  nuevas: [
    { cc: 3000, cliente: "Wayne Ent.", proyecto: "Polaris", monto: 280_000 },
    { cc: 2000, cliente: "Cyberdyne", proyecto: "Atlas", monto: 215_000 },
  ],
  alertas: [
    "Proyecto sin código en fuente DS — fila 24 (revisar manualmente).",
    "Moneda sin tipo de cambio en Engineering: proyecto 'Atlas' (EUR).",
  ],
};

const PASOS_PROCESO = [
  { txt: "Localizando archivos en Google Drive", icon: Database },
  { txt: "Interpretando fuentes con IA (Facturación, DS, Engineering, Consulting)", icon: Sparkles },
  { txt: "Reconciliando provisiones vs. facturas", icon: FileCheck },
  { txt: "Calculando montos (motor determinista)", icon: Calculator },
  { txt: "Generando resumen para revisión", icon: FileSpreadsheet },
];

const PASOS_ESCRITURA = [
  { txt: "Duplicando hoja del mes anterior", icon: FileSpreadsheet },
  { txt: "Escribiendo Sección B (sin tocar el tablero KPI)", icon: Calculator },
  { txt: "Subiendo archivo a Google Drive", icon: CloudUpload },
];

// ---------- UI helpers ----------
function Badge({ tone = "gray", children }) {
  const tones = {
    gray: "bg-slate-100 text-slate-600 ring-slate-200",
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    red: "bg-rose-50 text-rose-700 ring-rose-200",
    amber: "bg-amber-50 text-amber-700 ring-amber-200",
    blue: "bg-sky-50 text-sky-700 ring-sky-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${tones[tone]}`}>
      {children}
    </span>
  );
}

function Stepper({ pasos, activo }) {
  return (
    <ul className="space-y-3">
      {pasos.map((p, i) => {
        const Icon = p.icon;
        const done = i < activo;
        const current = i === activo;
        return (
          <li key={i} className="flex items-center gap-3">
            <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ring-1 ${
              done ? "bg-emerald-500 text-white ring-emerald-500"
              : current ? "bg-indigo-50 text-indigo-600 ring-indigo-200"
              : "bg-slate-50 text-slate-300 ring-slate-200"}`}>
              {done ? <CheckCircle2 size={18} /> : current ? <Loader2 size={18} className="animate-spin" /> : <Icon size={16} />}
            </span>
            <span className={`text-sm ${done ? "text-slate-500" : current ? "text-slate-900 font-medium" : "text-slate-400"}`}>
              {p.txt}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

// ---------- App ----------
export default function AgentePrototipo() {
  const [screen, setScreen] = useState("login");        // login | panel | processing | summary | writing | report | rejected
  const [usuario, setUsuario] = useState("");
  const [pipeline, setPipeline] = useState("summary");
  const [mes, setMes] = useState("2026 — Mayo");
  const [escenario, setEscenario] = useState("ok");      // ok | locked | error
  const [paso, setPaso] = useState(0);

  // Avance animado de los steppers
  const timer = useRef(null);
  useEffect(() => {
    if (screen !== "processing" && screen !== "writing") return;
    const pasos = screen === "processing" ? PASOS_PROCESO : PASOS_ESCRITURA;
    setPaso(0);
    timer.current = setInterval(() => {
      setPaso((p) => {
        // En escenario de error, detenerse en el paso 1 (archivos)
        if (screen === "processing" && escenario === "error" && p >= 1) {
          clearInterval(timer.current);
          setTimeout(() => setScreen("error"), 500);
          return p;
        }
        if (p >= pasos.length - 1) {
          clearInterval(timer.current);
          setTimeout(() => setScreen(screen === "processing" ? "summary" : "report"), 650);
          return p;
        }
        return p + 1;
      });
    }, 850);
    return () => clearInterval(timer.current);
  }, [screen, escenario]);

  const pipelineActual = PIPELINES.find((p) => p.id === pipeline);

  function iniciarProceso() {
    if (escenario === "locked") return; // bloqueado, no procede
    setScreen("processing");
  }

  // ----- Barra de demo (saltar entre estados sin backend) -----
  const DemoBar = () => (
    <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2">
      <div className="flex items-center gap-1 rounded-full border border-slate-200 bg-white/90 px-2 py-1.5 shadow-lg backdrop-blur">
        <span className="px-2 text-[11px] font-semibold uppercase tracking-wide text-slate-400">Demo</span>
        {[
          ["login", "Login"],
          ["panel", "Panel"],
          ["summary", "Resumen"],
          ["error", "Error"],
          ["report", "Reporte"],
          ["rejected", "Rechazo"],
        ].map(([s, label]) => (
          <button
            key={s}
            onClick={() => { setEscenario("ok"); setScreen(s); }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${
              screen === s ? "bg-indigo-600 text-white" : "text-slate-500 hover:bg-slate-100"}`}>
            {label}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 [font-feature-settings:'tnum']">
      {screen === "login" && <Login onEnter={(u) => { setUsuario(u || "ana.lopez"); setScreen("panel"); }} />}

      {screen !== "login" && (
        <Shell usuario={usuario} onLogout={() => { setUsuario(""); setScreen("login"); }}>
          {screen === "panel" && (
            <Panel
              pipeline={pipeline} setPipeline={setPipeline}
              mes={mes} setMes={setMes}
              escenario={escenario} setEscenario={setEscenario}
              onProcesar={iniciarProceso}
              pipelineActual={pipelineActual}
            />
          )}
          {screen === "processing" && (
            <CenterCard titulo={`Procesando ${pipelineActual.nombre}`} sub={mes}>
              <Stepper pasos={PASOS_PROCESO} activo={paso} />
              <p className="mt-6 flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck size={14} /> Nada se ha escrito todavía. Al terminar verás un resumen para aprobar.
              </p>
            </CenterCard>
          )}
          {screen === "error" && (
            <ErrorScreen onBack={() => setScreen("panel")} />
          )}
          {screen === "summary" && (
            <Resumen
              onConfirmar={() => setScreen("writing")}
              onRechazar={() => setScreen("rejected")}
              pipelineNombre={pipelineActual.nombre}
            />
          )}
          {screen === "writing" && (
            <CenterCard titulo="Escribiendo y subiendo" sub={RESUMEN.mes}>
              <Stepper pasos={PASOS_ESCRITURA} activo={paso} />
            </CenterCard>
          )}
          {screen === "report" && <Reporte onBack={() => setScreen("panel")} />}
          {screen === "rejected" && <Rechazado onBack={() => setScreen("panel")} />}
        </Shell>
      )}

      <DemoBar />
    </div>
  );
}

// ---------- Login ----------
function Login({ onEnter }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
            <FileSpreadsheet size={22} />
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Agente Financiero P3</h1>
          <p className="mt-1 text-sm text-slate-500">Plataforma interna de automatización</p>
        </div>
        <form
          onSubmit={(e) => { e.preventDefault(); onEnter(u.trim()); }}
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="block text-sm font-medium text-slate-700">Usuario</label>
          <input value={u} onChange={(e) => setU(e.target.value)} placeholder="ana.lopez"
            className="mt-1 mb-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
          <label className="block text-sm font-medium text-slate-700">Contraseña</label>
          <input value={p} onChange={(e) => setP(e.target.value)} type="password" placeholder="••••••••"
            className="mt-1 mb-6 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100" />
          <button type="submit"
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700">
            <LogIn size={16} /> Iniciar sesión
          </button>
          <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-slate-400">
            <Lock size={12} /> Sesión segura (JWT, expira en 8 h). Sin registro público.
          </p>
        </form>
      </div>
    </div>
  );
}

// ---------- Shell (layout con header) ----------
function Shell({ usuario, onLogout, children }) {
  return (
    <div className="mx-auto max-w-5xl px-4 pb-28 pt-6">
      <header className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <FileSpreadsheet size={18} />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">Agente Financiero P3</p>
            <p className="text-xs text-slate-400">Plataforma de automatización mensual</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden items-center gap-1.5 text-xs text-slate-400 sm:flex">
            <Lock size={12} /> sesión expira en ~8 h
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold text-slate-600">
              {(usuario || "u").slice(0, 2).toUpperCase()}
            </div>
            <span className="hidden text-slate-600 sm:inline">{usuario || "usuario"}</span>
          </div>
          <button onClick={onLogout} className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-500 hover:bg-slate-100">
            <LogOut size={15} /> Salir
          </button>
        </div>
      </header>
      {children}
    </div>
  );
}

// ---------- Panel principal ----------
function Panel({ pipeline, setPipeline, mes, setMes, escenario, setEscenario, onProcesar, pipelineActual }) {
  const bloqueado = escenario === "locked";
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Elige un pipeline y un mes</h2>
        <p className="text-sm text-slate-500">El agente lee las fuentes, las interpreta y prepara un resumen para tu aprobación.</p>
      </div>

      {/* Pipelines */}
      <div className="mb-8 grid gap-4 sm:grid-cols-3">
        {PIPELINES.map((p) => {
          const Icon = p.icon;
          const activo = p.estado === "activo";
          const sel = pipeline === p.id;
          return (
            <button
              key={p.id}
              disabled={!activo}
              onClick={() => activo && setPipeline(p.id)}
              className={`relative rounded-xl border p-4 text-left transition ${
                sel ? "border-indigo-500 bg-indigo-50/40 ring-2 ring-indigo-100"
                : activo ? "border-slate-200 bg-white hover:border-slate-300"
                : "cursor-not-allowed border-slate-200 bg-slate-50 opacity-70"}`}>
              <div className="mb-2 flex items-center justify-between">
                <Icon size={20} className={sel ? "text-indigo-600" : "text-slate-400"} />
                {p.estado === "construccion" && <Badge tone="amber">En construcción</Badge>}
                {p.estado === "proximamente" && <Badge tone="gray">Próximamente</Badge>}
                {p.estado === "activo" && <Badge tone="green">Disponible</Badge>}
              </div>
              <p className="text-sm font-semibold text-slate-800">{p.nombre}</p>
              <p className="mt-0.5 text-xs text-slate-500">{p.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Selección de mes + acción */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-xs flex-1">
            <label className="mb-1 block text-sm font-medium text-slate-700">Mes a procesar</label>
            <div className="relative">
              <Calendar size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <select value={mes} onChange={(e) => setMes(e.target.value)}
                className="w-full appearance-none rounded-lg border border-slate-300 py-2 pl-9 pr-9 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100">
                {MESES.map((m) => <option key={m}>{m}</option>)}
              </select>
              <ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
            </div>
          </div>
          <button
            onClick={onProcesar}
            disabled={bloqueado}
            className={`flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium text-white transition ${
              bloqueado ? "cursor-not-allowed bg-slate-300" : "bg-indigo-600 hover:bg-indigo-700"}`}>
            Procesar {pipelineActual.nombre.split(" ")[0]} <ChevronRight size={16} />
          </button>
        </div>

        {bloqueado && (
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <Lock size={18} className="mt-0.5 shrink-0 text-amber-600" />
            <div className="text-sm text-amber-800">
              <p className="font-semibold">Este mes lo está procesando Ana López.</p>
              <p className="text-amber-700">No puedes iniciar otro proceso para {mes} hasta que confirme o rechace. Se le avisó que intentaste entrar.</p>
            </div>
          </div>
        )}

        {/* Nota IA/código */}
        <p className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-400">
          <Cpu size={14} /> La IA interpreta la estructura de los archivos; <span className="font-medium text-slate-500">el sistema calcula los montos</span> de forma determinista.
        </p>
      </div>

      {/* Conmutador de escenario (solo demo) */}
      <div className="mt-4 flex items-center gap-2 text-xs text-slate-400">
        <Info size={13} /> Escenario de demo:
        {[["ok", "Normal"], ["locked", "Mes bloqueado"], ["error", "Archivo faltante"]].map(([v, l]) => (
          <button key={v} onClick={() => setEscenario(v)}
            className={`rounded-full px-2.5 py-1 ${escenario === v ? "bg-slate-800 text-white" : "bg-slate-100 hover:bg-slate-200 text-slate-600"}`}>
            {l}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---------- Tarjeta centrada (loaders) ----------
function CenterCard({ titulo, sub, children }) {
  return (
    <div className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <h2 className="text-lg font-semibold">{titulo}</h2>
      <p className="mb-6 text-sm text-slate-500">{sub}</p>
      {children}
    </div>
  );
}

// ---------- Error: archivo faltante ----------
function ErrorScreen({ onBack }) {
  return (
    <div className="mx-auto max-w-lg rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-600">
        <XCircle size={26} />
      </div>
      <h2 className="text-lg font-semibold text-slate-900">Proceso detenido</h2>
      <p className="mt-1 text-sm text-slate-600">
        Falta un archivo en Google Drive: <span className="font-medium">Provisiones_Engineering</span>.
        No se interpretó ni modificó nada.
      </p>
      <button onClick={onBack}
        className="mt-6 inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  );
}

// ---------- Resumen (Paso 7 — revisión) ----------
function Resumen({ onConfirmar, onRechazar, pipelineNombre }) {
  const totalFilas = RESUMEN.canceladas.length + RESUMEN.activas.length + RESUMEN.nuevas.length;
  return (
    <div>
      {/* Aviso de no-escritura */}
      <div className="mb-6 flex items-center gap-3 rounded-xl border border-sky-200 bg-sky-50 p-4">
        <ShieldCheck size={20} className="shrink-0 text-sky-600" />
        <div>
          <p className="text-sm font-semibold text-sky-900">Nada se ha guardado. Revisa y aprueba.</p>
          <p className="text-xs text-sky-700">{pipelineNombre} · {RESUMEN.mes} · {totalFilas} filas listas para escribir.</p>
        </div>
      </div>

      {/* Totales por segmento */}
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        {RESUMEN.totales.map((t) => (
          <div key={t.seg} className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t.seg}</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{mxn(t.total)}</p>
            <div className="mt-3 space-y-1 text-xs text-slate-500">
              <div className="flex justify-between"><span>Facturación</span><span className="font-medium text-slate-700">{mxn(t.facturacion)}</span></div>
              <div className="flex justify-between"><span>Canceladas</span><span className="font-medium text-rose-600">−{mxn(t.canceladas)}</span></div>
            </div>
          </div>
        ))}
      </div>

      {/* Alertas */}
      {RESUMEN.alertas.length > 0 && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800">
            <AlertTriangle size={16} /> Alertas ({RESUMEN.alertas.length})
          </p>
          <ul className="space-y-1 text-sm text-amber-800">
            {RESUMEN.alertas.map((a, i) => <li key={i} className="flex gap-2"><span className="text-amber-400">•</span>{a}</li>)}
          </ul>
        </div>
      )}

      {/* Tablas por estado */}
      <Tabla titulo="Canceladas" tone="red" sub="Provisiones que se cancelan porque ya se facturaron"
        cols={["CC", "Cliente", "Proyecto", "Monto MXN", "Referencia"]}
        rows={RESUMEN.canceladas.map((r) => [r.cc, r.cliente, r.proyecto, mxn(r.monto), r.ref])} />

      <Tabla titulo="Activas" tone="green" sub="Siguen como provisión — se muestra monto anterior vs. nuevo"
        cols={["CC", "Cliente", "Proyecto", "Antes", "Ahora", "Δ"]}
        rows={RESUMEN.activas.map((r) => {
          const delta = r.ahora - r.antes;
          return [
            r.cc, r.cliente, r.proyecto, mxn(r.antes), mxn(r.ahora),
            <span key="d" className={delta === 0 ? "text-slate-400" : delta > 0 ? "text-emerald-600" : "text-rose-600"}>
              {delta === 0 ? "—" : `${delta > 0 ? "+" : "−"}${mxn(Math.abs(delta))}`}
            </span>,
          ];
        })} />

      <Tabla titulo="Nuevas" tone="blue" sub="Provisiones nuevas detectadas este mes"
        cols={["CC", "Cliente", "Proyecto", "Monto MXN"]}
        rows={RESUMEN.nuevas.map((r) => [r.cc, r.cliente, r.proyecto, mxn(r.monto)])} />

      {/* Acciones */}
      <div className="sticky bottom-20 mt-6 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white/95 p-4 shadow-sm backdrop-blur sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-slate-500">
          <span className="font-medium text-slate-700">{totalFilas} filas</span> se escribirán en la hoja {RESUMEN.mes}. La decisión final es tuya.
        </p>
        <div className="flex gap-3">
          <button onClick={onRechazar}
            className="flex items-center gap-2 rounded-lg border border-rose-200 px-4 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50">
            <XCircle size={16} /> Rechazar
          </button>
          <button onClick={onConfirmar}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-700">
            <CheckCircle2 size={16} /> Confirmar y escribir
          </button>
        </div>
      </div>
      <p className="mt-2 text-center text-xs text-slate-400">Rechazar descarta el plan; ningún archivo se modifica.</p>
    </div>
  );
}

function Tabla({ titulo, sub, tone, cols, rows }) {
  const dot = { red: "bg-rose-500", green: "bg-emerald-500", blue: "bg-sky-500" }[tone];
  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <span className={`h-2 w-2 rounded-full ${dot}`} />
        <h3 className="text-sm font-semibold text-slate-800">{titulo}</h3>
        <span className="text-xs text-slate-400">· {rows.length}</span>
        <span className="ml-auto hidden text-xs text-slate-400 sm:inline">{sub}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
              {cols.map((c) => <th key={c} className="px-4 py-2 font-medium">{c}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-t border-slate-50 hover:bg-slate-50/60">
                {r.map((cell, j) => (
                  <td key={j} className={`px-4 py-2.5 ${j === 0 ? "text-slate-400" : "text-slate-700"} ${j >= 3 ? "tabular-nums" : ""}`}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------- Reporte final ----------
function Reporte({ onBack }) {
  const filas = { canceladas: 3, provisiones: 3, nuevas: 2, total: 8 };
  return (
    <div className="mx-auto max-w-lg">
      <div className="rounded-2xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <CheckCircle2 size={26} />
        </div>
        <h2 className="text-lg font-semibold">Hoja escrita correctamente</h2>
        <p className="mt-1 text-sm text-slate-600">
          <span className="font-medium">2026_Mayo</span> en <span className="font-medium">2026_Summary_provision.xlsm</span> · subido a Google Drive.
        </p>

        <div className="mt-6 grid grid-cols-4 gap-2 text-center">
          {[["Canceladas", filas.canceladas], ["Provisiones", filas.provisiones], ["Nuevas", filas.nuevas], ["Total", filas.total]].map(([l, n]) => (
            <div key={l} className="rounded-lg bg-slate-50 py-3">
              <p className="text-xl font-semibold text-slate-900">{n}</p>
              <p className="text-[11px] uppercase tracking-wide text-slate-400">{l}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-left">
        <p className="mb-1 flex items-center gap-2 text-sm font-semibold text-amber-800"><AlertTriangle size={15} /> Pendientes manuales</p>
        <p className="text-sm text-amber-800">Capturar tipos de cambio USD/EUR/CAD en el tablero KPI (filas 6–8).</p>
      </div>

      <button onClick={onBack}
        className="mx-auto mt-6 flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  );
}

// ---------- Rechazado ----------
function Rechazado({ onBack }) {
  return (
    <div className="mx-auto max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
        <XCircle size={26} />
      </div>
      <h2 className="text-lg font-semibold">Plan descartado</h2>
      <p className="mt-1 text-sm text-slate-600">No se modificó ningún archivo. El mes queda libre para volver a procesarse.</p>
      <button onClick={onBack}
        className="mx-auto mt-6 flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  );
}
