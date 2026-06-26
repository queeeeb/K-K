import { ArrowUpRight, ArrowDownRight } from 'lucide-react'

const fmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })

export default function Delta({ antes, ahora }) {
  const d = ahora - antes
  if (d === 0) return <span className="font-num text-slate-400">—</span>
  const up = d > 0
  return (
    <span className={`inline-flex items-center gap-0.5 font-num font-medium ${up ? 'text-emerald-600' : 'text-rose-600'}`}>
      {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
      {up ? '+' : '−'}{fmt.format(Math.abs(d))}
    </span>
  )
}
