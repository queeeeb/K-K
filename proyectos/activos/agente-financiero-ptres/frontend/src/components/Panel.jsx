import { CheckCircle2, TrendingUp, Wallet, Calendar, ChevronDown, ChevronRight, Cpu, Lock, Clock, XCircle } from 'lucide-react'
import Money from './Money'
import StatusPill from './StatusPill'
import { slotsDe } from '../uploadSpec'

const KPIS = [
  { l: 'Último cierre',      v: 'Abril 2026', sub: '8 filas escritas',   icon: CheckCircle2, tone: 'text-emerald-600', num: false },
  { l: 'Provisiones activas', v: '23',          sub: 'arrastradas al mes', icon: TrendingUp,   tone: 'text-slate-900',  num: false },
  { l: 'Total provisionado',  v: 3_325_000,     sub: 'cierre anterior',    icon: Wallet,       tone: 'text-slate-900',  num: true  },
]

const PIPELINE_LABEL = { summary: 'Summary · Provisiones', pl: 'P&L · Estado de resultados' }
const MES_LABEL = (mes) => mes.replace('-', ' — ').replace(/(\d{4}) — (\d{2})/, (_, y, m) => {
  const mp = ['','Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
  return `${y} — ${mp[parseInt(m)] || m}`
})

function BannerPendientes({ items, onRetomar, onCancelar }) {
  if (!items || items.length === 0) return null
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 space-y-3">
      <p className="flex items-center gap-2 text-sm font-semibold text-blue-900">
        <Clock size={15} /> Esperando aprobación
      </p>
      {items.map((item) => (
        <div key={`${item.pipeline}|${item.mes}`} className="flex items-center justify-between gap-4 rounded-lg border border-blue-100 bg-white px-4 py-3">
          <div>
            <p className="text-sm font-medium text-slate-900">{PIPELINE_LABEL[item.pipeline] ?? item.pipeline}</p>
            <p className="text-xs text-slate-500">{MES_LABEL(item.mes)}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => onCancelar(item)} className="flex items-center gap-1.5 rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 transition-colors">
              <XCircle size={13} /> Cancelar
            </button>
            <button onClick={() => onRetomar(item)} className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors">
              <ChevronRight size={13} /> Retomar
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Panel({ pact, mes, setMes, MESES, lockedBy, pendientesItems, onProcesar, onRetomar, onCancelarPendiente, archivos = {}, setArchivo, tc = {}, setTcMoneda }) {
  const Icon = pact.icon
  const slots = slotsDe(pact.id)
  const faltan = Object.keys(slots).filter(s => !archivos[s])
  const completo = faltan.length === 0

  return (
    <div className="space-y-6">
      <BannerPendientes items={pendientesItems} onRetomar={onRetomar} onCancelar={onCancelarPendiente} />
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
          <button onClick={onProcesar} disabled={!!lockedBy || !completo}
            className={`flex items-center justify-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition focus:ring-4 ${
              (lockedBy || !completo) ? 'cursor-not-allowed bg-slate-300' : 'bg-slate-900 hover:bg-slate-800 focus:ring-slate-900/20'}`}>
            Procesar {pact.nombre} <ChevronRight size={16} />
          </button>
        </div>

        {Object.keys(slots).length > 0 && (
          <div className="border-t border-slate-100 px-5 py-4">
            <p className="mb-2 text-sm font-medium text-slate-700">Archivos del mes</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(slots).map(([slot, etiqueta]) => (
                <label key={slot} className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50">
                  <input type="file" accept=".xlsx,.xlsm" className="hidden"
                    onChange={e => setArchivo(slot, e.target.files[0])} />
                  <span className={`h-2 w-2 shrink-0 rounded-full ${archivos[slot] ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                  <span className="min-w-0 flex-1 truncate text-slate-600">{archivos[slot]?.name ?? etiqueta}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {pact.id === 'summary' && (
          <div className="border-t border-slate-100 px-5 py-4">
            <p className="mb-1 text-sm font-medium text-slate-700">Tipo de cambio del mes</p>
            <p className="mb-2.5 text-xs text-slate-500">Se usa para convertir las provisiones nuevas en moneda extranjera. Si lo dejas vacío, se toma el del tablero del mes anterior.</p>
            <div className="grid gap-2 sm:grid-cols-3">
              {['USD', 'EUR', 'CAD'].map(moneda => (
                <label key={moneda} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                  <span className="w-9 shrink-0 font-semibold text-slate-600">{moneda}</span>
                  <input type="number" step="0.0001" min="0" inputMode="decimal"
                    placeholder="—"
                    value={tc[moneda] ?? ''}
                    onChange={e => setTcMoneda(moneda, e.target.value)}
                    className="min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-2 py-1 text-right font-num tabular-nums text-slate-900 outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
                </label>
              ))}
            </div>
          </div>
        )}

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
