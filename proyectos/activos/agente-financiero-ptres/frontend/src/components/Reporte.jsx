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
