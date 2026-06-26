import { LayoutDashboard, Clock, FileText, LogOut } from 'lucide-react'
import Brand from './Brand'
import { PIPELINES } from '../App'

function NavItem({ icon: Icon, active, children }) {
  return (
    <a className={`mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors cursor-pointer ${
      active ? 'bg-white/10 font-medium text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>
      <Icon size={17} className={active ? 'text-amber-400' : ''} /> {children}
    </a>
  )
}

export default function Sidebar({ pipeline, setPipeline, onLogout }) {
  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-slate-900 lg:flex">
      <div className="flex h-16 items-center border-b border-white/10 px-5"><Brand /></div>
      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        <div>
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">General</p>
          <NavItem icon={LayoutDashboard} active>Panel</NavItem>
          <NavItem icon={Clock}>Historial</NavItem>
          <NavItem icon={FileText}>Bitácora</NavItem>
        </div>
        <div>
          <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Pipelines</p>
          {PIPELINES.map(p => {
            const Icon = p.icon
            const sel = pipeline === p.id
            const dis = p.estado !== 'activo'
            return (
              <button key={p.id} disabled={dis} onClick={() => !dis && setPipeline(p.id)}
                className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  sel ? 'bg-white/10 text-white' : dis ? 'cursor-not-allowed text-slate-600' : 'text-slate-300 hover:bg-white/5 hover:text-white'}`}>
                <Icon size={17} className={sel ? 'text-amber-400' : ''} />
                <span className="flex-1 text-left">{p.nombre}</span>
                {p.estado === 'construccion' && <span className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-medium text-amber-400">beta</span>}
                {p.estado === 'proximamente' && <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-500">pronto</span>}
              </button>
            )
          })}
        </div>
      </nav>
      <div className="border-t border-white/10 p-3">
        <button onClick={onLogout} className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-white/5 hover:text-white">
          <LogOut size={17} /> Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
