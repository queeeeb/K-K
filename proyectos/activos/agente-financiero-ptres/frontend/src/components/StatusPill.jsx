const TONES = {
  cancel: 'bg-rose-50 text-rose-700 ring-rose-200',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  new:    'bg-blue-50 text-blue-700 ring-blue-200',
  review: 'bg-amber-50 text-amber-800 ring-amber-200',
  cc:     'bg-slate-100 text-slate-600 ring-slate-200',
}

export default function StatusPill({ tone, children }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ${TONES[tone]}`}>
      {children}
    </span>
  )
}
