import { useState } from 'react'
import { FileSpreadsheet, TrendingUp, ChevronDown, ClipboardList } from 'lucide-react'

const PIPELINE_META = {
  summary: { label: 'Summary', Icon: FileSpreadsheet },
  pl:      { label: 'P&L',     Icon: TrendingUp },
}

const TYPE_PILL = {
  nueva:    { label: 'Nueva',      cls: 'bg-blue-50 text-blue-700 ring-blue-200' },
  activa:   { label: 'Modificada', cls: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  cancelada:{ label: 'Cancelada',  cls: 'bg-rose-50 text-rose-700 ring-rose-200' },
}

function inferType(e) {
  if (e.valor_anterior === null || e.valor_anterior === undefined) return 'nueva'
  if (String(e.valor_nuevo).trim().toLowerCase() === 'cancelar') return 'cancelada'
  return 'activa'
}

function formatNum(v) {
  if (v === null || v === undefined) return null
  const n = parseFloat(String(v).replace(/,/g, ''))
  return isNaN(n) ? String(v) : n.toLocaleString('es-MX')
}

function formatMes(m) {
  const [y, mo] = m.split('_')
  const mp = { Jan:'Enero',Feb:'Febrero',Mar:'Marzo',Apr:'Abril',May:'Mayo',Jun:'Junio',Jul:'Julio',Aug:'Agosto',Sep:'Septiembre',Oct:'Octubre',Nov:'Noviembre',Dec:'Diciembre' }
  return (mp[mo] || mo) + ' ' + y
}

function formatFecha(iso) {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('es-MX', { day:'2-digit', month:'short', year:'numeric' }) +
           ' · ' + d.toLocaleTimeString('es-MX', { hour:'2-digit', minute:'2-digit', hour12:false })
  } catch { return iso }
}

function Pill({ type }) {
  const { label, cls } = TYPE_PILL[type] || TYPE_PILL.activa
  return <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${cls}`}>{label}</span>
}

function GroupTable({ entries, pipeline }) {
  const colLabel = pipeline === 'summary' ? 'Proyecto' : 'Empresa / Gasto'
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50/50">
            {[colLabel, 'Tipo', 'Anterior', 'Nuevo'].map((h, i) => (
              <th key={h} className={`px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 ${i >= 2 ? 'text-right' : 'text-left'}`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {entries.map((e, i) => {
            const type = inferType(e)
            const isCancelar = String(e.valor_nuevo).trim().toLowerCase() === 'cancelar'
            return (
              <tr key={i} className="transition-colors hover:bg-slate-50/70">
                <td className="px-4 py-2.5 font-mono text-sm text-slate-700">{e.fila}</td>
                <td className="px-4 py-2.5"><Pill type={type} /></td>
                <td className="px-4 py-2.5 text-right font-mono tabular-nums text-sm">
                  {e.valor_anterior !== null && e.valor_anterior !== undefined
                    ? <span className="text-slate-400 line-through">{formatNum(e.valor_anterior)}</span>
                    : <span className="text-slate-200">—</span>}
                </td>
                <td className={`px-4 py-2.5 text-right font-mono tabular-nums text-sm font-medium ${isCancelar ? 'text-rose-600' : type === 'nueva' ? 'text-blue-700' : 'text-slate-900'}`}>
                  {isCancelar ? 'Cancelar' : formatNum(e.valor_nuevo)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function Group({ group }) {
  const [open, setOpen] = useState(true)
  const meta = PIPELINE_META[group.pipeline] || { label: group.pipeline, Icon: FileSpreadsheet }
  const Icon = meta.Icon

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <button type="button" onClick={() => setOpen(v => !v)}
        className="flex w-full items-center gap-3 border-b border-slate-100 bg-slate-50/60 px-5 py-3.5 text-left transition-colors hover:bg-slate-50">
        <Icon size={16} className="shrink-0 text-slate-400" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-900">{meta.label}</span>
            <span className="text-xs text-slate-300">·</span>
            <span className="text-sm text-slate-600">{formatMes(group.mes)}</span>
          </div>
          <div className="mt-0.5 flex items-center gap-2">
            <span className="text-xs text-slate-400">{group.usuario}</span>
            <span className="text-xs text-slate-200">·</span>
            <span className="text-xs text-slate-400">{formatFecha(group.latestDate)}</span>
          </div>
        </div>
        <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 ring-1 ring-slate-200 whitespace-nowrap">
          {group.entries.length} cambios
        </span>
        <ChevronDown size={16} className="shrink-0 text-slate-400 transition-transform duration-150" style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }} />
      </button>
      {open && <GroupTable entries={group.entries} pipeline={group.pipeline} />}
    </div>
  )
}

export default function Bitacora({ entradas }) {
  const [activeFilter, setActiveFilter] = useState('all')

  const data = entradas || []
  const filtered = activeFilter === 'all' ? data : data.filter(e => e.pipeline === activeFilter)

  const groupMap = new Map()
  filtered.forEach(entry => {
    const key = `${entry.pipeline}|${entry.mes}`
    if (!groupMap.has(key)) {
      groupMap.set(key, { key, pipeline: entry.pipeline, mes: entry.mes, usuario: entry.usuario, latestDate: entry.created_at, entries: [] })
    }
    const g = groupMap.get(key)
    if (entry.created_at > g.latestDate) { g.latestDate = entry.created_at; g.usuario = entry.usuario }
    g.entries.push(entry)
  })

  const groups = Array.from(groupMap.values()).sort((a, b) => b.latestDate > a.latestDate ? 1 : -1)

  const tabCls = (active) => active
    ? 'px-3 py-1.5 rounded-md text-sm font-medium bg-slate-900 text-white transition-colors'
    : 'px-3 py-1.5 rounded-md text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors'

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Bitácora</h1>
          <p className="mt-0.5 text-sm text-slate-500">Historial de cambios confirmados por proceso</p>
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          <button type="button" onClick={() => setActiveFilter('all')} className={tabCls(activeFilter === 'all')}>Todos</button>
          <button type="button" onClick={() => setActiveFilter('summary')} className={tabCls(activeFilter === 'summary')}>Summary</button>
          <button type="button" onClick={() => setActiveFilter('pl')} className={tabCls(activeFilter === 'pl')}>P&amp;L</button>
        </div>
      </div>

      {groups.length > 0
        ? <div className="flex flex-col gap-3">{groups.map(g => <Group key={g.key} group={g} />)}</div>
        : (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-slate-200 bg-white py-20">
            <ClipboardList size={36} className="text-slate-300" />
            <p className="mt-1 text-sm font-semibold text-slate-900">Sin registros todavía</p>
            <p className="text-xs text-slate-400">Aquí aparecerán los procesos confirmados.</p>
          </div>
        )
      }
    </div>
  )
}
