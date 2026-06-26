import { ChevronRight, Calendar, Search, Bell, ShieldCheck } from 'lucide-react'

export default function Topbar({ usuario, pact, mes, MESES }) {
  const mesLabel = MESES.find(m => m.value === mes)?.label ?? mes
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-6 backdrop-blur lg:px-10">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-slate-400">Pipelines</span>
        <ChevronRight size={14} className="text-slate-300" />
        <span className="font-semibold text-slate-900">{pact?.full}</span>
        <span className="ml-2 hidden items-center gap-1.5 rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600 sm:inline-flex">
          <Calendar size={13} /> {mesLabel}
        </span>
      </div>
      <div className="flex items-center gap-3">
        <button className="hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex"><Search size={17} /></button>
        <button className="relative hidden h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 sm:flex">
          <Bell size={17} /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-amber-500" />
        </button>
        <div className="hidden items-center gap-1.5 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 md:flex">
          <ShieldCheck size={13} /><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Sesión segura · 8h
        </div>
        <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
            {(usuario || 'u').slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden leading-tight sm:block">
            <p className="text-sm font-medium text-slate-800">{usuario}</p>
            <p className="text-[11px] text-slate-400">K&amp;K · Finanzas</p>
          </div>
        </div>
      </div>
    </header>
  )
}
