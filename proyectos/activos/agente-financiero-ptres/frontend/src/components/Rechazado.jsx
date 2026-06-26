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
