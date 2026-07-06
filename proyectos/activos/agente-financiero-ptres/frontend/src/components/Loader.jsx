import { useState, useEffect } from 'react'
import { Loader2, FileUp, Sparkles, FileCheck, Calculator, FileSpreadsheet, ShieldCheck } from 'lucide-react'
import Stepper from './Stepper'

const PASOS_PROCESO = [
  { txt: 'Leyendo archivos subidos',        icon: FileUp },
  { txt: 'Interpretando fuentes con IA', sub: 'Facturación · DS · Engineering · Consulting', icon: Sparkles },
  { txt: 'Reconciliando provisiones vs. facturas',      icon: FileCheck },
  { txt: 'Calculando montos', sub: 'motor determinista', icon: Calculator },
  { txt: 'Generando resumen para revisión',             icon: FileSpreadsheet },
]

const PASOS_ESCRITURA = [
  { txt: 'Duplicando hoja del mes anterior',                                    icon: FileSpreadsheet },
  { txt: 'Escribiendo Sección B', sub: 'sin tocar el tablero KPI (filas 1–11)', icon: Calculator },
  { txt: 'Generando archivo para descarga',                                     icon: FileCheck },
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
