// Adaptado para el runtime de Design Components (sin imports ESM):
// - React proviene del global UMD ya cargado.
// - Los iconos usan el paquete vanilla "lucide" (UMD) dibujados con el MISMO React.
const { useState, useEffect, useRef } = React;

const _camel = (k) => k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
function makeIcon(name) {
  return function LucideIcon(props) {
    props = props || {};
    const size = props.size || 24;
    const svgAttrs = {
      xmlns: "http://www.w3.org/2000/svg", width: size, height: size,
      viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
      strokeWidth: 2, strokeLinecap: "round", strokeLinejoin: "round",
      className: props.className, style: props.style,
    };
    const node = window.lucide && window.lucide.icons && window.lucide.icons[name];
    if (!node) return React.createElement("svg", svgAttrs);
    const parts = node[2] || [];
    const children = parts.map((part, i) => {
      const tag = part[0];
      const attrs = { key: i };
      const raw = part[1] || {};
      for (const k in raw) attrs[_camel(k)] = raw[k];
      return React.createElement(tag, attrs);
    });
    return React.createElement("svg", svgAttrs, children);
  };
}

const LogIn = makeIcon("LogIn");
const LogOut = makeIcon("LogOut");
const FileSpreadsheet = makeIcon("FileSpreadsheet");
const TrendingUp = makeIcon("TrendingUp");
const Wallet = makeIcon("Wallet");
const ChevronRight = makeIcon("ChevronRight");
const ChevronDown = makeIcon("ChevronDown");
const Lock = makeIcon("Lock");
const ShieldCheck = makeIcon("ShieldCheck");
const Cpu = makeIcon("Cpu");
const AlertTriangle = makeIcon("AlertTriangle");
const CheckCircle2 = makeIcon("CheckCircle2");
const XCircle = makeIcon("XCircle");
const Loader2 = makeIcon("Loader2");
const ArrowLeft = makeIcon("ArrowLeft");
const Calendar = makeIcon("Calendar");
const Database = makeIcon("Database");
const Sparkles = makeIcon("Sparkles");
const Calculator = makeIcon("Calculator");
const FileCheck = makeIcon("FileCheck");
const CloudUpload = makeIcon("CloudUpload");
const LayoutDashboard = makeIcon("LayoutDashboard");
const Search = makeIcon("Search");
const Bell = makeIcon("Bell");
const Building2 = makeIcon("Building2");
const Check = makeIcon("Check");
const ArrowUpRight = makeIcon("ArrowUpRight");
const ArrowDownRight = makeIcon("ArrowDownRight");
const Clock = makeIcon("Clock");
const FileText = makeIcon("FileText");

if (!window.lucide && !window.__lucideLoading) {
  window.__lucideLoading = true;
  const s = document.createElement("script");
  s.src = "https://unpkg.com/lucide@0.471.0/dist/umd/lucide.js";
  s.onload = () => window.dispatchEvent(new Event("lucide-ready"));
  document.head.appendChild(s);
}

/* =========================================================================
   Agente Financiero P3 — Plataforma interna de automatización (prototipo)
   Design system (UI/UX Pro Max): Financial Dashboard / Banking — Data-Dense.
   Identidad: navy #0F172A + dorado #A16207. Inter + mono tabular para montos.
   Datos 100% ficticios.
   ========================================================================= */

// ---------- Tipografía (Inter UI + JetBrains Mono para cifras) ----------
const FontFace = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
    .font-ui   { font-family: 'Inter', ui-sans-serif, system-ui, sans-serif; }
    .font-num  { font-family: 'JetBrains Mono', ui-monospace, monospace; font-feature-settings: 'tnum' 1; }
  `}</style>
);

// ---------- Datos ficticios ----------
const PIPELINES = [
  { id: "summary",  nombre: "Summary",  full: "Summary · Provisiones",     desc: "Hoja mensual de provisiones", icon: FileSpreadsheet, estado: "activo" },
  { id: "pl",       nombre: "P&L",      full: "P&L · Estado de resultados", desc: "Estado de resultados mensual", icon: TrendingUp,      estado: "construccion" },
  { id: "cashflow", nombre: "Cash Flow",full: "Cash Flow · Cobranza",       desc: "Estatus de cobranza / AR",     icon: Wallet,          estado: "proximamente" },
];

const MESES = ["2026 — Marzo", "2026 — Abril", "2026 — Mayo", "2026 — Junio"];

const mxn = (n) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(n);

const RESUMEN = {
  mes: "2026 — Mayo",
  totales: [
    { seg: "CONSULTING",  cc: 3000, facturacion: 1_840_000, canceladas: 420_000, total: 1_420_000 },
    { seg: "DS",          cc: 7000, facturacion: 960_000,   canceladas: 180_000, total: 780_000 },
    { seg: "ENGINEERING", cc: 2000, facturacion: 1_220_000, canceladas: 95_000,  total: 1_125_000 },
  ],
  canceladas: [
    { cc: 3000, cliente: "Acme Corp",  proyecto: "Aurora", monto: 240_000, ref: "C-2026-00109" },
    { cc: 3000, cliente: "Globex",     proyecto: "Helios", monto: 180_000, ref: "C-2026-00114" },
    { cc: 7000, cliente: "Initech",    proyecto: "Nimbus", monto: 180_000, ref: "C-2026-00121" },
  ],
  activas: [
    { cc: 3000, cliente: "Umbrella",   proyecto: "Vega",  antes: 320_000, ahora: 320_000 },
    { cc: 2000, cliente: "Stark Ind.", proyecto: "Orion", antes: 410_000, ahora: 455_000 },
    { cc: 7000, cliente: "Soylent",    proyecto: "Lyra",  antes: 150_000, ahora: 132_000 },
  ],
  nuevas: [
    { cc: 3000, cliente: "Wayne Ent.", proyecto: "Polaris", monto: 280_000 },
    { cc: 2000, cliente: "Cyberdyne",  proyecto: "Atlas",   monto: 215_000 },
  ],
  alertas: [
    "Proyecto sin código en fuente DS — fila 24 (revisar manualmente).",
    "Moneda sin tipo de cambio en Engineering: proyecto 'Atlas' (EUR).",
  ],
};

const PASOS_PROCESO = [
  { txt: "Localizando archivos en Google Drive", icon: Database },
  { txt: "Interpretando fuentes con IA", sub: "Facturación · DS · Engineering · Consulting", icon: Sparkles },
  { txt: "Reconciliando provisiones vs. facturas", icon: FileCheck },
  { txt: "Calculando montos", sub: "motor determinista", icon: Calculator },
  { txt: "Generando resumen para revisión", icon: FileSpreadsheet },
];
const PASOS_ESCRITURA = [
  { txt: "Duplicando hoja del mes anterior", icon: FileSpreadsheet },
  { txt: "Escribiendo Sección B", sub: "sin tocar el tablero KPI (filas 1–11)", icon: Calculator },
  { txt: "Subiendo archivo a Google Drive", icon: CloudUpload },
];

// ---------- Átomos ----------
const Money = ({ value, className = "" }) => (
  <span className={`font-num tabular-nums ${className}`}>{mxn(value)}</span>
);

function StatusPill({ tone, children }) {
  const tones = {
    cancel: "bg-rose-50 text-rose-700 ring-rose-200",
    active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    new:    "bg-blue-50 text-blue-700 ring-blue-200",
    review: "bg-amber-50 text-amber-800 ring-amber-200",
    cc:     "bg-slate-100 text-slate-600 ring-slate-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${tones[tone]}`}>
      {children}
    </span>
  );
}

function Delta({ antes, ahora }) {
  const d = ahora - antes;
  if (d === 0) return <span className="font-num text-slate-400">—</span>;
  const up = d > 0;
  return (
    <span className={`inline-flex items-center gap-0.5 font-num font-medium ${up ? "text-emerald-600" : "text-rose-600"}`}>
      {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
      {up ? "+" : "−"}{mxn(Math.abs(d)).replace("$", "$")}
    </span>
  );
}

function Stepper({ pasos, activo }) {
  return (
    <ul className="space-y-1">
      {pasos.map((p, i) => {
        const Icon = p.icon;
        const done = i < activo, current = i === activo;
        return (
          <li key={i} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors ${current ? "bg-slate-50" : ""}`}>
            <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ring-1 transition-colors ${
              done ? "bg-emerald-600 text-white ring-emerald-600"
              : current ? "bg-amber-50 text-amber-700 ring-amber-200"
              : "bg-white text-slate-300 ring-slate-200"}`}>
              {done ? <Check size={16} /> : current ? <Loader2 size={16} className="animate-spin" /> : <Icon size={15} />}
            </span>
            <div className="min-w-0">
              <p className={`text-sm leading-tight ${done ? "text-slate-400" : current ? "font-semibold text-slate-900" : "text-slate-400"}`}>{p.txt}</p>
              {p.sub && <p className="text-xs text-slate-400">{p.sub}</p>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

// =========================================================================
function AgentePrototipo() {
  const [screen, setScreen] = useState("login"); // login|panel|processing|error|summary|writing|report|rejected
  const [usuario, setUsuario] = useState("");
  const [pipeline, setPipeline] = useState("summary");
  const [mes, setMes] = useState("2026 — Mayo");
  const [escenario, setEscenario] = useState("ok"); // ok|locked|error
  const [paso, setPaso] = useState(0);
  const timer = useRef(null);

  useEffect(() => {
    if (screen !== "processing" && screen !== "writing") return;
    const pasos = screen === "processing" ? PASOS_PROCESO : PASOS_ESCRITURA;
    setPaso(0);
    timer.current = setInterval(() => {
      setPaso((p) => {
        if (screen === "processing" && escenario === "error" && p >= 1) {
          clearInterval(timer.current);
          setTimeout(() => setScreen("error"), 450);
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

  const pact = PIPELINES.find((p) => p.id === pipeline);

  return (
    <div className="font-ui min-h-screen bg-slate-100 text-slate-900 antialiased">
      <FontFace />
      {screen === "login"
        ? <Login onEnter={(u) => { setUsuario(u || "ana.lopez"); setScreen("panel"); }} />
        : (
          <div className="flex min-h-screen">
            <Sidebar pipeline={pipeline} setPipeline={setPipeline} onLogout={() => { setUsuario(""); setScreen("login"); }} />
            <div className="flex min-w-0 flex-1 flex-col">
              <Topbar usuario={usuario} pact={pact} mes={mes} />
              <main className="flex-1 overflow-y-auto px-6 py-6 lg:px-10">
                <div className="mx-auto max-w-6xl">
                  {screen === "panel" && (
                    <Panel pact={pact} mes={mes} setMes={setMes} escenario={escenario} setEscenario={setEscenario}
                           onProcesar={() => escenario !== "locked" && setScreen("processing")} />
                  )}
                  {screen === "processing" && <Loader titulo={`Procesando ${pact.full}`} sub={mes} pasos={PASOS_PROCESO} paso={paso} nota />}
                  {screen === "error" && <ErrorScreen onBack={() => setScreen("panel")} />}
                  {screen === "summary" && <Resumen pact={pact} onConfirmar={() => setScreen("writing")} onRechazar={() => setScreen("rejected")} />}
                  {screen === "writing" && <Loader titulo="Escribiendo y subiendo a Drive" sub={RESUMEN.mes} pasos={PASOS_ESCRITURA} paso={paso} />}
                  {screen === "report" && <Reporte onBack={() => setScreen("panel")} />}
                  {screen === "rejected" && <Rechazado onBack={() => setScreen("panel")} />}
                </div>
              </main>
              <footer className="border-t border-slate-200 bg-white px-6 py-4 text-center lg:px-10">
                <p className="text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">Orión by K&amp;K</span> — La propiedad intelectual y el agente pertenecen a <span className="font-semibold text-slate-700">K&amp;K</span>. © 2026 K&amp;K · Uso interno.
                </p>
              </footer>
            </div>
          </div>
        )}
      <DemoBar screen={screen} go={(s) => { setEscenario("ok"); setScreen(s); }} />
    </div>
  );
}

// ---------- Marca ----------
const Brand = ({ dark = true }) => (
  <div className="flex items-center gap-2.5">
    <div className={`flex h-9 w-9 items-center justify-center rounded-lg font-num text-[11px] font-bold tracking-tight ${dark ? "bg-amber-500 text-slate-900" : "bg-slate-900 text-amber-400"}`}>K&amp;K</div>
    <div className="leading-tight">
      <p className={`text-lg font-bold leading-none ${dark ? "text-white" : "text-slate-900"}`}>Orión</p>
      <p className={`text-[11px] ${dark ? "text-slate-400" : "text-slate-500"}`}>by K&amp;K</p>
    </div>
  </div>
);

// ---------- Sidebar (navy shell) ----------
function Sidebar({ pipeline, setPipeline, onLogout }) {
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
          {PIPELINES.map((p) => {
            const Icon = p.icon, sel = pipeline === p.id, dis = p.estado !== "activo";
            return (
              <button key={p.id} disabled={dis} onClick={() => !dis && setPipeline(p.id)}
                className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  sel ? "bg-white/10 text-white" : dis ? "cursor-not-allowed text-slate-600" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}>
                <Icon size={17} className={sel ? "text-amber-400" : ""} />
                <span className="flex-1 text-left">{p.nombre}</span>
                {p.estado === "construccion" && <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-400">beta</span>}
                {p.estado === "proximamente" && <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-500">pronto</span>}
              </button>
            );
          })}
        </div>
      </nav>
      <div className="border-t border-white/10 p-3">
        <button onClick={onLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white">
          <LogOut size={17} /> Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
const NavItem = ({ icon: Icon, active, children }) => (
  <a className={`mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
    active ? "bg-white/10 font-medium text-white" : "text-slate-300 hover:bg-white/5 hover:text-white"}`}>
    <Icon size={17} className={active ? "text-amber-400" : ""} /> {children}
  </a>
);

// ---------- Topbar ----------
function Topbar({ usuario, pact, mes }) {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 backdrop-blur lg:px-10">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400">Pipelines</span>
        <ChevronRight size={14} className="text-slate-300" />
        <span className="font-semibold text-slate-900">{pact?.full}</span>
        <span className="ml-2 hidden items-center gap-1.5 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 sm:inline-flex">
          <Calendar size={13} /> {mes}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex"><Search size={17} /></button>
        <button className="relative hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex">
          <Bell size={17} /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-amber-500" />
        </button>
        <div className="hidden items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 md:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Sesión segura · 8h
        </div>
        <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">{(usuario || "u").slice(0, 2).toUpperCase()}</div>
          <div className="hidden leading-tight sm:block">
            <p className="text-sm font-medium text-slate-800">{usuario}</p>
            <p className="text-[11px] text-slate-400">K&amp;K · Finanzas</p>
          </div>
        </div>
      </div>
    </header>
  );
}

// ---------- Fondo: constelación de Orión con profundidad y brillo ----------
const ORION = [
  { x: 500, y: 70,  r: 3.0, c: "#fff4dd", g: 9  },  // Meissa (cabeza)
  { x: 360, y: 235, r: 6.0, c: "#ffb27a", g: 22 },  // Betelgeuse (gigante rojiza)
  { x: 650, y: 195, r: 4.4, c: "#eaf2ff", g: 15 },  // Bellatrix
  { x: 430, y: 360, r: 3.4, c: "#ffe9c2", g: 11 },  // Cinturón
  { x: 505, y: 388, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 580, y: 412, r: 3.4, c: "#ffe9c2", g: 11 },
  { x: 320, y: 560, r: 6.0, c: "#cfe2ff", g: 22 },  // Rigel (supergigante azul)
  { x: 690, y: 540, r: 4.4, c: "#dbe7ff", g: 15 },  // Saiph
  { x: 780, y: 120, r: 2.6, c: "#ffe9c2", g: 8  },  // brazo / garrote
  { x: 850, y: 55,  r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 235, y: 205, r: 2.6, c: "#ffe9c2", g: 8  },  // escudo
  { x: 215, y: 100, r: 2.6, c: "#ffe9c2", g: 8  },
  { x: 240, y: 345, r: 2.6, c: "#ffe9c2", g: 8  },
];

const _seed = (() => { let s = 1723; return () => (s = (s * 9301 + 49297) % 233280) / 233280; })();
const FAR  = Array.from({ length: 70 }, () => ({ x: _seed() * 1000, y: _seed() * 620, r: _seed() * 0.8 + 0.3, o: _seed() * 0.35 + 0.1,  d: _seed() * 6 }));
const NEAR = Array.from({ length: 30 }, () => ({ x: _seed() * 1000, y: _seed() * 620, r: _seed() * 1.2 + 0.7, o: _seed() * 0.5 + 0.45, d: _seed() * 5 }));

const OrionSky = () => (
  <div className="absolute inset-0 overflow-hidden">
    <style>{`
      @keyframes orionTwinkle { 0%,100%{opacity:.15} 50%{opacity:.7} }
      @keyframes orionPulse   { 0%,100%{opacity:.55} 50%{opacity:1} }
      @keyframes nebDrift     { 0%,100%{opacity:.55} 50%{opacity:.95} }
    `}</style>
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid slice" fill="none" aria-hidden="true">
      <defs>
        <radialGradient id="spaceGlow" cx="46%" cy="40%" r="75%">
          <stop offset="0%"  stopColor="#1d3050" />
          <stop offset="42%" stopColor="#101f36" />
          <stop offset="100%" stopColor="#060c18" />
        </radialGradient>
        <radialGradient id="nebA" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="nebB" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#3b6fd4" stopOpacity="0.26" />
          <stop offset="100%" stopColor="#3b6fd4" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffd79b" stopOpacity="0.0" />
          <stop offset="50%" stopColor="#ffce8a" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#ffd79b" stopOpacity="0.0" />
        </linearGradient>
        <filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" /></filter>
        <filter id="glow" x="-400%" y="-400%" width="900%" height="900%">
          <feGaussianBlur stdDeviation="6" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <rect width="1000" height="620" fill="url(#spaceGlow)" />

      {/* nebulosas para dar profundidad */}
      <g style={{ animation: "nebDrift 9s ease-in-out infinite" }}>
        <ellipse cx="430" cy="380" rx="340" ry="250" fill="url(#nebA)" />
      </g>
      <g style={{ animation: "nebDrift 11s ease-in-out 1.5s infinite" }}>
        <ellipse cx="700" cy="170" rx="280" ry="210" fill="url(#nebB)" />
        <ellipse cx="240" cy="520" rx="240" ry="190" fill="url(#nebB)" />
      </g>

      {/* capa lejana: estrellas difusas y tenues (profundidad) */}
      <g fill="#9fb4d6" filter="url(#soft)">
        {FAR.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
            style={{ animation: `orionTwinkle ${4 + s.d}s ease-in-out ${s.d}s infinite` }} />
        ))}
      </g>

      {/* capa cercana: estrellas nítidas con parpadeo */}
      <g fill="#ffffff">
        {NEAR.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} opacity={s.o}
            style={{ animation: `orionTwinkle ${3 + s.d}s ease-in-out ${s.d}s infinite` }} />
        ))}
      </g>

      {/* líneas de la constelación: halo difuso + trazo nítido */}
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

      {/* halos de las estrellas de Orión (brillo) */}
      <g filter="url(#soft)">
        {ORION.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.g} fill={s.c} opacity="0.16"
            style={{ animation: `orionPulse ${5 + (i % 4)}s ease-in-out ${i * 0.4}s infinite` }} />
        ))}
      </g>

      {/* núcleos brillantes de Orión */}
      <g filter="url(#glow)">
        {ORION.map((s, i) => (
          <circle key={i} cx={s.x} cy={s.y} r={s.r} fill={s.c}
            style={{ animation: `orionPulse ${4 + (i % 3)}s ease-in-out ${i * 0.3}s infinite` }} />
        ))}
      </g>
    </svg>
  </div>
);

// ---------- Login ----------
function Login({ onEnter }) {
  const [u, setU] = useState(""); const [p, setP] = useState("");
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
          <p className="mt-1 text-sm text-slate-900">Accede con tu usuario individual</p>
          <form onSubmit={(e) => { e.preventDefault(); onEnter(u.trim()); }} className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Usuario</label>
              <div className="relative">
                <Building2 size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={u} onChange={(e) => setU(e.target.value)} placeholder="ana.lopez"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Contraseña</label>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={p} onChange={(e) => setP(e.target.value)} type="password" placeholder="••••••••"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            <button type="submit" className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:ring-4 focus:ring-slate-900/20">
              <LogIn size={16} /> Entrar
            </button>
          </form>
          <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-slate-400">
            <Lock size={12} /> Autenticación JWT · expira en 8 h · sin registro público
          </p>
        </div>
        <p className="mt-6 text-center text-xs text-slate-500">© 2026 K&amp;K · Orión es propiedad intelectual de K&amp;K</p>
      </div>
    </div>
  );
}

// ---------- Panel ----------
function Panel({ pact, mes, setMes, escenario, setEscenario, onProcesar }) {
  const bloqueado = escenario === "locked";
  const Icon = pact.icon;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Panel de proceso</h1>
        <p className="text-sm text-slate-500">Elige el mes y procésalo. Verás un resumen para aprobar antes de escribir nada.</p>
      </div>

      {/* KPIs del último cierre */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { l: "Último cierre", v: "Abril 2026", sub: "8 filas escritas", icon: CheckCircle2, tone: "text-emerald-600" },
          { l: "Provisiones activas", v: "23", sub: "arrastradas al mes", icon: TrendingUp, tone: "text-slate-900" },
          { l: "Total provisionado", v: mxn(3_325_000), sub: "cierre anterior", icon: Wallet, tone: "text-slate-900", num: true },
        ].map((k) => (
          <div key={k.l} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{k.l}</p>
              <k.icon size={16} className={k.tone} />
            </div>
            <p className={`mt-2 text-2xl font-bold text-slate-900 ${k.num ? "font-num tabular-nums" : ""}`}>{k.v}</p>
            <p className="mt-0.5 text-xs text-slate-400">{k.sub}</p>
          </div>
        ))}
      </div>

      {/* Tarjeta de ejecución */}
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
              <select value={mes} onChange={(e) => setMes(e.target.value)}
                className="w-full appearance-none rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-9 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10">
                {MESES.map((m) => <option key={m}>{m}</option>)}
              </select>
              <ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
            </div>
          </div>
          <button onClick={onProcesar} disabled={bloqueado}
            className={`flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition focus:ring-4 ${
              bloqueado ? "cursor-not-allowed bg-slate-300" : "bg-slate-900 hover:bg-slate-800 focus:ring-slate-900/20"}`}>
            Procesar {pact.nombre} <ChevronRight size={16} />
          </button>
        </div>

        {bloqueado && (
          <div className="mx-5 mb-5 flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3.5">
            <Lock size={18} className="mt-0.5 shrink-0 text-amber-600" />
            <div className="text-sm">
              <p className="font-semibold text-amber-900">Mes bloqueado — lo está procesando Ana López.</p>
              <p className="text-amber-700">No puedes iniciar otro proceso para {mes} hasta que confirme o rechace. Se le notificó que intentaste entrar.</p>
            </div>
          </div>
        )}

        <div className="flex items-center gap-2 border-t border-slate-100 px-5 py-3">
          <Cpu size={14} className="text-slate-400" />
          <p className="text-xs text-slate-500">La IA interpreta la estructura de los archivos; <span className="font-medium text-slate-700">el sistema calcula los montos</span> de forma determinista.</p>
        </div>
      </div>

      {/* Escenario demo */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <span className="font-medium">Escenario de demo:</span>
        {[["ok", "Normal"], ["locked", "Mes bloqueado"], ["error", "Archivo faltante"]].map(([v, l]) => (
          <button key={v} onClick={() => setEscenario(v)}
            className={`rounded-md px-2.5 py-1 font-medium transition ${escenario === v ? "bg-slate-900 text-white" : "bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50"}`}>{l}</button>
        ))}
      </div>
    </div>
  );
}

// ---------- Loader ----------
function Loader({ titulo, sub, pasos, paso, nota }) {
  return (
    <div className="mx-auto max-w-xl">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900 text-amber-400"><Loader2 size={18} className="animate-spin" /></span>
          <div><h2 className="text-base font-semibold text-slate-900">{titulo}</h2><p className="font-num text-xs text-slate-500">{sub}</p></div>
        </div>
        <Stepper pasos={pasos} activo={paso} />
        {nota && <p className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-4 text-xs text-slate-400"><ShieldCheck size={14} /> Nada se escribe todavía. Al terminar verás un resumen para aprobar.</p>}
      </div>
    </div>
  );
}

// ---------- Error ----------
function ErrorScreen({ onBack }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-rose-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-600"><XCircle size={26} /></div>
      <h2 className="text-lg font-bold text-slate-900">Proceso detenido</h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">Falta un archivo en Google Drive: <span className="font-num font-medium text-slate-900">Provisiones_Engineering</span>. No se interpretó ni modificó nada.</p>
      <button onClick={onBack} className="mt-6 inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"><ArrowLeft size={16} /> Volver al panel</button>
    </div>
  );
}

// ---------- Resumen (Paso 7) ----------
function Resumen({ pact, onConfirmar, onRechazar }) {
  const total = RESUMEN.canceladas.length + RESUMEN.activas.length + RESUMEN.nuevas.length;
  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Resumen para revisión</h1>
            <StatusPill tone="review"><Clock size={12} /> Pendiente de aprobación</StatusPill>
          </div>
          <p className="text-sm text-slate-500">{pact.full} · <span className="font-num">{RESUMEN.mes}</span> · {total} filas listas para escribir.</p>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3">
        <ShieldCheck size={18} className="shrink-0 text-amber-700" />
        <p className="text-sm font-medium text-amber-900">Nada se ha guardado todavía. Revisa los movimientos y aprueba para escribir en el Summary.</p>
      </div>

      {/* Totales por segmento */}
      <div className="grid gap-4 sm:grid-cols-3">
        {RESUMEN.totales.map((t) => (
          <div key={t.seg} className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{t.seg}</p>
              <StatusPill tone="cc">CC {t.cc}</StatusPill>
            </div>
            <p className="mt-2 font-num text-2xl font-bold tabular-nums text-slate-900">{mxn(t.total)}</p>
            <div className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-xs">
              <div className="flex justify-between text-slate-500"><span>Facturación</span><Money value={t.facturacion} className="text-slate-700" /></div>
              <div className="flex justify-between text-slate-500"><span>Canceladas</span><span className="font-num tabular-nums text-rose-600">−{mxn(t.canceladas)}</span></div>
            </div>
          </div>
        ))}
      </div>

      {/* Alertas */}
      {RESUMEN.alertas.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-white p-4">
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800"><AlertTriangle size={16} /> Alertas · {RESUMEN.alertas.length}</p>
          <ul className="space-y-1.5 text-sm text-slate-600">
            {RESUMEN.alertas.map((a, i) => <li key={i} className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-400" />{a}</li>)}
          </ul>
        </div>
      )}

      {/* Tablas */}
      <Tabla tone="cancel" titulo="Canceladas" sub="Ya se facturaron — cambian de estatus en su fila"
        head={["CC", "Cliente", "Proyecto", "Monto MXN", "Referencia"]} align={[0,0,0,1,1]}>
        {RESUMEN.canceladas.map((r, i) => (
          <Row key={i} cells={[<StatusPill tone="cc">{r.cc}</StatusPill>, r.cliente, r.proyecto, <Money value={r.monto} className="text-slate-500 line-through" />, <span className="font-num text-xs text-slate-500">{r.ref}</span>]} align={[0,0,0,1,1]} />
        ))}
      </Tabla>

      <Tabla tone="active" titulo="Activas" sub="Siguen como provisión — anterior vs. nuevo"
        head={["CC", "Cliente", "Proyecto", "Antes", "Ahora", "Δ"]} align={[0,0,0,1,1,1]}>
        {RESUMEN.activas.map((r, i) => (
          <Row key={i} cells={[<StatusPill tone="cc">{r.cc}</StatusPill>, r.cliente, r.proyecto, <Money value={r.antes} className="text-slate-400" />, <Money value={r.ahora} className="font-medium text-slate-900" />, <Delta antes={r.antes} ahora={r.ahora} />]} align={[0,0,0,1,1,1]} />
        ))}
      </Tabla>

      <Tabla tone="new" titulo="Nuevas" sub="Provisiones nuevas detectadas este mes"
        head={["CC", "Cliente", "Proyecto", "Monto MXN"]} align={[0,0,0,1]}>
        {RESUMEN.nuevas.map((r, i) => (
          <Row key={i} cells={[<StatusPill tone="cc">{r.cc}</StatusPill>, r.cliente, r.proyecto, <Money value={r.monto} className="font-medium text-slate-900" />]} align={[0,0,0,1]} />
        ))}
      </Tabla>

      {/* Barra de acción fija */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur lg:left-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-3.5 sm:flex-row sm:items-center sm:justify-between lg:px-10">
          <p className="text-xs text-slate-500"><span className="font-num font-semibold text-slate-800">{total} filas</span> se escribirán en la hoja <span className="font-num">{RESUMEN.mes}</span>. Rechazar descarta el plan; ningún archivo se modifica.</p>
          <div className="flex gap-3">
            <button onClick={onRechazar} className="flex items-center gap-2 rounded-lg border border-rose-200 bg-white px-4 py-2 text-sm font-medium text-rose-600 transition hover:bg-rose-50 focus:ring-4 focus:ring-rose-500/15"><XCircle size={16} /> Rechazar</button>
            <button onClick={onConfirmar} className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus:ring-4 focus:ring-emerald-600/25"><CheckCircle2 size={16} /> Confirmar y escribir</button>
          </div>
        </div>
      </div>
    </div>
  );
}

const TONE_BAR = { cancel: "bg-rose-500", active: "bg-emerald-500", new: "bg-blue-500" };
function Tabla({ tone, titulo, sub, head, align, children }) {
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
              {head.map((h, i) => <th key={h} className={`px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 ${align[i] ? "text-right" : "text-left"}`}>{h}</th>)}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">{children}</tbody>
        </table>
      </div>
    </div>
  );
}
const Row = ({ cells, align }) => (
  <tr className="transition-colors hover:bg-slate-50/70">
    {cells.map((c, j) => <td key={j} className={`px-4 py-2.5 ${align[j] ? "text-right" : "text-left"} ${j === 1 ? "font-medium text-slate-800" : "text-slate-600"}`}>{c}</td>)}
  </tr>
);

// ---------- Reporte ----------
function Reporte({ onBack }) {
  const f = { canceladas: 3, provisiones: 3, nuevas: 2, total: 8 };
  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div className="rounded-xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600"><CheckCircle2 size={26} /></div>
        <h2 className="text-lg font-bold text-slate-900">Hoja escrita correctamente</h2>
        <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">Hoja <span className="font-num font-medium text-slate-900">2026_Mayo</span> en <span className="font-num font-medium text-slate-900">2026_Summary_provision.xlsm</span> · subida a Google Drive.</p>
        <div className="mt-6 grid grid-cols-4 gap-2">
          {[["Canceladas", f.canceladas, "text-rose-600"], ["Provisiones", f.provisiones, "text-emerald-600"], ["Nuevas", f.nuevas, "text-blue-600"], ["Total", f.total, "text-slate-900"]].map(([l, n, c]) => (
            <div key={l} className="rounded-lg border border-slate-100 bg-slate-50 py-3">
              <p className={`font-num text-2xl font-bold tabular-nums ${c}`}>{n}</p>
              <p className="text-[11px] uppercase tracking-wide text-slate-400">{l}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
        <AlertTriangle size={17} className="mt-0.5 shrink-0 text-amber-600" />
        <div className="text-sm"><p className="font-semibold text-amber-900">Pendientes manuales</p><p className="text-amber-800">Capturar tipos de cambio USD/EUR/CAD en el tablero KPI (filas 6–8).</p></div>
      </div>
      <button onClick={onBack} className="mx-auto flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"><ArrowLeft size={16} /> Volver al panel</button>
    </div>
  );
}

// ---------- Rechazado ----------
function Rechazado({ onBack }) {
  return (
    <div className="mx-auto max-w-xl rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500"><XCircle size={26} /></div>
      <h2 className="text-lg font-bold text-slate-900">Plan descartado</h2>
      <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">No se modificó ningún archivo. El mes queda libre para volver a procesarse.</p>
      <button onClick={onBack} className="mx-auto mt-6 flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"><ArrowLeft size={16} /> Volver al panel</button>
    </div>
  );
}

// ---------- Barra de demo ----------
function DemoBar({ screen, go }) {
  return (
    <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2">
      <div className="flex items-center gap-1 rounded-full border border-slate-700 bg-slate-900/95 px-2 py-1.5 shadow-xl backdrop-blur">
        <span className="px-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Demo</span>
        {[["login","Login"],["panel","Panel"],["summary","Resumen"],["error","Error"],["report","Reporte"],["rejected","Rechazo"]].map(([s, l]) => (
          <button key={s} onClick={() => go(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition ${screen === s ? "bg-amber-500 text-slate-900" : "text-slate-300 hover:bg-white/10"}`}>{l}</button>
        ))}
      </div>
    </div>
  );
}


window.AgentePrototipo = AgentePrototipo;
