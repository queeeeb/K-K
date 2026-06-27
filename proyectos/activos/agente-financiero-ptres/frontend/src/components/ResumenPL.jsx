import { ShieldCheck, Clock, CheckCircle2, XCircle, TrendingUp, TrendingDown } from 'lucide-react'
import Money from './Money'
import StatusPill from './StatusPill'

const FILAS = [
  { key: 'incomes',          label: 'Ingresos',              tone: 'text-emerald-600' },
  { key: 'expenses',         label: 'Gastos operativos',     tone: 'text-rose-600' },
  { key: 'operating_profit', label: 'Utilidad operativa',    tone: 'text-slate-900', bold: true, divider: true },
  { key: 'other_incomes',    label: 'Otros ingresos',        tone: 'text-emerald-600' },
  { key: 'other_expenses',   label: 'Otros gastos',          tone: 'text-rose-600' },
  { key: 'accrued_taxes',    label: 'Impuestos acumulados',  tone: 'text-rose-600' },
  { key: 'net_profit',       label: 'Utilidad neta',         tone: 'text-slate-900', bold: true, divider: true },
]

export default function ResumenPL({ pact, mes, resumen, onConfirmar, onRechazar }) {
  if (!resumen) return null

  const netPositive = resumen.net_profit >= 0

  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Resumen para revisión</h1>
            <StatusPill tone="review"><Clock size={12} /> Pendiente de aprobación</StatusPill>
          </div>
          <p className="text-sm text-slate-500">{pact.full} · <span className="font-num">{mes}</span></p>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3">
        <ShieldCheck size={18} className="shrink-0 text-amber-700" />
        <p className="text-sm font-medium text-amber-900">Nada se ha guardado todavía. Revisa los totales y aprueba para escribir el P&L.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Ingresos totales</p>
          <p className="mt-2 font-num text-2xl font-bold tabular-nums text-emerald-600">
            <Money value={resumen.incomes} />
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Utilidad neta</p>
            {netPositive
              ? <TrendingUp size={16} className="text-emerald-600" />
              : <TrendingDown size={16} className="text-rose-600" />}
          </div>
          <p className={`mt-2 font-num text-2xl font-bold tabular-nums ${netPositive ? 'text-slate-900' : 'text-rose-600'}`}>
            <Money value={resumen.net_profit} />
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-100 bg-slate-50/60 px-5 py-3.5">
          <h3 className="text-sm font-semibold text-slate-900">Estado de resultados</h3>
        </div>
        <table className="w-full text-sm">
          <tbody>
            {FILAS.map(({ key, label, tone, bold, divider }) => (
              <tr key={key} className={`transition-colors hover:bg-slate-50/70 ${divider ? 'border-t border-slate-200' : 'border-t border-slate-50'}`}>
                <td className={`px-5 py-3 ${bold ? 'font-semibold text-slate-900' : 'text-slate-600'}`}>{label}</td>
                <td className={`px-5 py-3 text-right font-num tabular-nums ${bold ? 'font-bold' : 'font-medium'} ${tone}`}>
                  <Money value={resumen[key]} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur lg:left-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-3.5 sm:flex-row sm:items-center sm:justify-between lg:px-10">
          <p className="text-xs text-slate-500">
            Rechazar descarta el plan; ningún archivo se modifica.
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
