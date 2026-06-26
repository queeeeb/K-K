const fmt = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })

export default function Money({ value, className = '' }) {
  return <span className={`font-num tabular-nums ${className}`}>{fmt.format(value)}</span>
}
