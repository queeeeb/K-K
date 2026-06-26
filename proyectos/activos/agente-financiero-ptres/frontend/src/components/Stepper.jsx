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
