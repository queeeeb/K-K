import React from 'react'

const TONE_BAR = { cancel: 'bg-rose-500', active: 'bg-emerald-500', new: 'bg-blue-500' }

export function Row({ cells, align }) {
  return (
    <tr className="transition-colors hover:bg-slate-50/70">
      {cells.map((c, j) => (
        <td key={j} className={`px-4 py-2.5 ${align[j] ? 'text-right' : 'text-left'} ${j === 1 ? 'font-medium text-slate-800' : 'text-slate-600'}`}>
          {c}
        </td>
      ))}
    </tr>
  )
}

export default function Tabla({ tone, titulo, sub, head, align, children }) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="flex items-center gap-2.5 border-b border-slate-100 px-4 py-3">
        <span className={`h-2.5 w-2.5 rounded-full ${TONE_BAR[tone]}`} />
        <h3 className="text-sm font-semibold text-slate-900">{titulo}</h3>
        <span className="font-num text-xs text-slate-400">{React.Children.count(children)}</span>
        <span className="ml-auto hidden text-xs text-slate-400 sm:inline">{sub}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              {head.map((h, i) => (
                <th key={h} className={`px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400 ${align[i] ? 'text-right' : 'text-left'}`}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">{children}</tbody>
        </table>
      </div>
    </div>
  )
}
