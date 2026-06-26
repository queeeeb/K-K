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
