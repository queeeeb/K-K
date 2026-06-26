export default function Brand({ dark = true }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className={`flex h-9 w-9 items-center justify-center rounded-lg font-num text-[11px] font-bold tracking-tight ${dark ? "bg-amber-500 text-slate-900" : "bg-slate-900 text-amber-400"}`}>
        K&amp;K
      </div>
      <div className="leading-tight">
        <p className={`text-lg font-bold leading-none ${dark ? "text-white" : "text-slate-900"}`}>Orión</p>
        <p className={`text-[11px] ${dark ? "text-slate-400" : "text-slate-500"}`}>by K&amp;K</p>
      </div>
    </div>
  )
}
