import { CheckCircle2, AlertTriangle, ArrowLeft, Download } from 'lucide-react'
import api from '../api'

export default function Reporte({ reporte, mes, onBack }) {
  if (!reporte) return null

  const esPL = reporte.archivo?.startsWith('PL_')

  const items = esPL ? [] : [
    ['Canceladas', reporte.canceladas,    'text-rose-600'],
    ['Provisiones', reporte.activas,      'text-emerald-600'],
    ['Nuevas',      reporte.nuevas,       'text-blue-600'],
    ['Total',       reporte.filas_escritas, 'text-slate-900'],
  ]

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <div className="rounded-xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <CheckCircle2 size={26} />
        </div>
        <h2 className="text-lg font-bold text-slate-900">
          {esPL ? 'P&L generado correctamente' : 'Hoja escrita correctamente'}
        </h2>
        <p className="mx-auto mt-1.5 max-w-md text-sm text-slate-600">
          <span className="font-num font-medium text-slate-900">{mes}</span>
        </p>

        {!esPL && (
          <div className="mt-6 grid grid-cols-4 gap-2">
            {items.map(([l, n, c]) => (
              <div key={l} className="rounded-lg border border-slate-100 bg-slate-50 py-3">
                <p className={`font-num text-2xl font-bold tabular-nums ${c}`}>{n}</p>
                <p className="text-[11px] uppercase tracking-wide text-slate-400">{l}</p>
              </div>
            ))}
          </div>
        )}

        {reporte.archivo && (
          <button
            onClick={() => api.descargar(reporte.archivo)}
            className="mt-6 flex items-center gap-2 mx-auto rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700"
          >
            <Download size={16} /> Descargar Excel
          </button>
        )}
      </div>

      {!esPL && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle size={17} className="mt-0.5 shrink-0 text-amber-600" />
          <div className="text-sm">
            <p className="font-semibold text-amber-900">Pendientes manuales</p>
            <p className="text-amber-800">Capturar tipos de cambio USD/EUR/CAD en el tablero KPI (filas 6–8).</p>
          </div>
        </div>
      )}

      <button onClick={onBack} className="mx-auto flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50">
        <ArrowLeft size={16} /> Volver al panel
      </button>
    </div>
  )
}
