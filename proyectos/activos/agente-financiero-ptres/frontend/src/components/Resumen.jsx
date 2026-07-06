import { useState } from 'react'
import { ShieldCheck, AlertTriangle, Clock, CheckCircle2, XCircle, Tag } from 'lucide-react'
import Money from './Money'
import StatusPill from './StatusPill'
import Delta from './Delta'
import Tabla, { Row } from './Tabla'

function calcularTotales(resumen) {
  const mapa = {}
  const sumar = (items) => {
    items.forEach(r => {
      if (!mapa[r.cc]) mapa[r.cc] = { seg: String(r.cc), cc: r.cc, total: 0 }
      mapa[r.cc].total += (r.monto_mxn ?? 0)
    })
  }
  sumar(resumen.activas)
  sumar(resumen.nuevas)
  return Object.values(mapa).sort((a, b) => a.cc - b.cc)
}

export default function Resumen({ pact, mes, resumen, onConfirmar, onRechazar, onNombrar }) {
  const [nombres, setNombres] = useState({})
  const [ocultarNombrar, setOcultarNombrar] = useState(false)
  const [guardando, setGuardando] = useState(false)

  if (!resumen) return null
  const total = resumen.canceladas.length + resumen.activas.length + resumen.nuevas.length
  const totales = calcularTotales(resumen)
  const sinNombre = resumen.nuevas.filter(r => r.codigo_nuevo)
  const hayNombres = Object.values(nombres).some(n => n.trim() !== '')

  async function guardarYContinuar() {
    const listos = Object.fromEntries(
      Object.entries(nombres).filter(([, v]) => v.trim() !== '')
    )
    if (Object.keys(listos).length === 0) { setOcultarNombrar(true); return }
    setGuardando(true)
    try {
      await onNombrar(listos)
      setNombres({})
      setOcultarNombrar(true)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="space-y-6 pb-24">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">Resumen para revisión</h1>
            <StatusPill tone="review"><Clock size={12} /> Pendiente de aprobación</StatusPill>
          </div>
          <p className="text-sm text-slate-500">{pact.full} · <span className="font-num">{mes}</span> · {total} filas listas para escribir.</p>
        </div>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/70 px-4 py-3">
        <ShieldCheck size={18} className="shrink-0 text-amber-700" />
        <p className="text-sm font-medium text-amber-900">Nada se ha guardado todavía. Revisa los movimientos y aprueba para escribir en el Summary.</p>
      </div>

      {totales.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-3">
          {totales.map(t => (
            <div key={t.cc} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">CC {t.cc}</p>
              </div>
              <p className="mt-2 font-num text-2xl font-bold tabular-nums text-slate-900"><Money value={t.total} /></p>
            </div>
          ))}
        </div>
      )}

      {sinNombre.length > 0 && !ocultarNombrar && (
        <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-4">
          <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-900">
            <Tag size={16} /> Códigos nuevos sin nombre de cliente · {sinNombre.length}
          </p>
          <div className="space-y-2.5">
            {sinNombre.map((r, i) => (
              <div key={i} className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <StatusPill tone="cc">{r.cc}</StatusPill>
                <span className="font-num text-sm text-slate-600 sm:w-56">{r.proyecto}</span>
                <input
                  type="text"
                  placeholder="Nombre del cliente"
                  value={nombres[r.proyecto] ?? ''}
                  onChange={e => setNombres(n => ({ ...n, [r.proyecto]: e.target.value }))}
                  className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-400 focus:outline-none focus:ring-4 focus:ring-blue-500/15"
                />
              </div>
            ))}
          </div>
          <div className="mt-3 flex justify-end gap-3">
            <button onClick={() => setOcultarNombrar(true)} className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100">
              Continuar sin nombrar
            </button>
            <button onClick={guardarYContinuar} disabled={!hayNombres || guardando}
              className="rounded-lg bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50">
              {guardando ? 'Guardando…' : 'Guardar y continuar'}
            </button>
          </div>
        </div>
      )}

      {resumen.alertas.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-white p-4">
          <p className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-800"><AlertTriangle size={16} /> Alertas · {resumen.alertas.length}</p>
          <ul className="space-y-1.5 text-sm text-slate-600">
            {resumen.alertas.map((a, i) => (
              <li key={i} className="flex gap-2"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-400" />{a}</li>
            ))}
          </ul>
        </div>
      )}

      <Tabla tone="cancel" titulo="Canceladas" sub="Ya se facturaron — cambian de estatus en su fila"
        head={['CC', 'Cliente', 'Proyecto', 'Monto MXN']} align={[false, false, false, true]}>
        {resumen.canceladas.map((r, i) => (
          <Row key={i} align={[false, false, false, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn} className="text-slate-500 line-through" />,
          ]} />
        ))}
      </Tabla>

      <Tabla tone="active" titulo="Activas" sub="Siguen como provisión — anterior vs. nuevo"
        head={['CC', 'Cliente', 'Proyecto', 'Antes', 'Ahora', 'Δ']} align={[false, false, false, true, true, true]}>
        {resumen.activas.map((r, i) => (
          <Row key={i} align={[false, false, false, true, true, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn_anterior} className="text-slate-400" />,
            <Money value={r.monto_mxn} className="font-medium text-slate-900" />,
            <Delta antes={r.monto_mxn_anterior} ahora={r.monto_mxn} />,
          ]} />
        ))}
      </Tabla>

      <Tabla tone="new" titulo="Nuevas" sub="Provisiones nuevas detectadas este mes"
        head={['CC', 'Cliente', 'Proyecto', 'Monto MXN']} align={[false, false, false, true]}>
        {resumen.nuevas.map((r, i) => (
          <Row key={i} align={[false, false, false, true]} cells={[
            <StatusPill tone="cc">{r.cc}</StatusPill>,
            r.codigo_nuevo ? <StatusPill tone="review">Sin nombre</StatusPill> : r.cliente,
            r.proyecto,
            <Money value={r.monto_mxn} className="font-medium text-slate-900" />,
          ]} />
        ))}
      </Tabla>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 backdrop-blur lg:left-64">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-3.5 sm:flex-row sm:items-center sm:justify-between lg:px-10">
          <p className="text-xs text-slate-500">
            <span className="font-num font-semibold text-slate-800">{total} filas</span> se escribirán en la hoja <span className="font-num">{mes}</span>. Rechazar descarta el plan; ningún archivo se modifica.
          </p>
          <div className="flex gap-3">
            <button onClick={onRechazar} className="flex items-center gap-2 rounded-lg border border-rose-200 bg-white px-4 py-2 text-sm font-medium text-rose-600 transition hover:bg-rose-50 focus:ring-4 focus:ring-rose-500/15">
              <XCircle size={16} /> Rechazar
            </button>
            <button onClick={onConfirmar} className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus:ring-4 focus:ring-emerald-600/25">
              <CheckCircle2 size={16} /> Confirmar y escribir
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
