import { useState } from 'react'
import { FileSpreadsheet, TrendingUp, Wallet } from 'lucide-react'
import api from './api'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Login    from './components/Login'
import Panel    from './components/Panel'
import Loader   from './components/Loader'
import ErrorScreen from './components/ErrorScreen'
import Resumen  from './components/Resumen'
import Reporte  from './components/Reporte'
import Rechazado from './components/Rechazado'

export const PIPELINES = [
  { id: 'summary',  nombre: 'Summary',   full: 'Summary · Provisiones',      desc: 'Hoja mensual de provisiones',   icon: FileSpreadsheet, estado: 'activo' },
  { id: 'pl',       nombre: 'P&L',       full: 'P&L · Estado de resultados', desc: 'Estado de resultados mensual',  icon: TrendingUp,      estado: 'activo' },
  { id: 'cashflow', nombre: 'Cash Flow', full: 'Cash Flow · Cobranza',       desc: 'Estatus de cobranza / AR',      icon: Wallet,          estado: 'proximamente' },
]

const MESES = [
  { label: '2026 — Marzo', value: '2026-03' },
  { label: '2026 — Abril', value: '2026-04' },
  { label: '2026 — Mayo',  value: '2026-05' },
  { label: '2026 — Junio', value: '2026-06' },
]

export { MESES }

export default function App() {
  const [screen,     setScreen]     = useState(api.getToken() ? 'panel' : 'login')
  const [usuario,    setUsuario]    = useState('')
  const [pipeline,   setPipeline]   = useState('summary')
  const [mes,        setMes]        = useState('2026-05')
  const [plan,       setPlan]       = useState(null)
  const [reporte,    setReporte]    = useState(null)
  const [errorMsg,   setErrorMsg]   = useState('')
  const [lockedBy,   setLockedBy]   = useState('')

  const pact = PIPELINES.find(p => p.id === pipeline)

  function handleLogout() {
    api.clearToken()
    setUsuario('')
    setPlan(null)
    setReporte(null)
    setScreen('login')
  }

  const sharedProps = { usuario, pipeline, setPipeline, mes, setMes, plan, planToken: plan?.token, reporte, pact, MESES, lockedBy, errorMsg }

  if (screen === 'login') {
    return <Login onSuccess={(u) => { setUsuario(u); setScreen('panel') }} />
  }

  return (
    <div className="font-ui min-h-screen bg-slate-100 text-slate-900 antialiased flex">
      <Sidebar pipeline={pipeline} setPipeline={setPipeline} onLogout={handleLogout} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar usuario={usuario} pact={pact} mes={mes} MESES={MESES} />
        <main className="flex-1 overflow-y-auto px-6 py-6 lg:px-10">
          <div className="mx-auto max-w-6xl">
            {screen === 'panel' && (
              <Panel
                {...sharedProps}
                onProcesar={async () => {
                  setScreen('processing')
                  try {
                    const data = await api.procesar(pipeline, mes)
                    setPlan(data)
                    setScreen('summary')
                  } catch (err) {
                    if (err.locked) {
                      setLockedBy(err.locked_by)
                      setScreen('panel')
                    } else {
                      setErrorMsg(err.message)
                      setScreen('error')
                    }
                  }
                }}
              />
            )}
            {screen === 'processing' && <Loader titulo={`Procesando ${pact.full}`} sub={MESES.find(m => m.value === mes)?.label ?? mes} mode="processing" />}
            {screen === 'error'      && <ErrorScreen msg={errorMsg} onBack={() => { setErrorMsg(''); setScreen('panel') }} />}
            {screen === 'summary'    && (
              <Resumen
                pact={pact}
                mes={MESES.find(m => m.value === mes)?.label ?? mes}
                resumen={plan?.resumen}
                onConfirmar={async () => {
                  setScreen('writing')
                  try {
                    const data = await api.confirmar(pipeline, plan.token)
                    setReporte(data.reporte)
                    setPlan(null)
                    setScreen('report')
                  } catch (err) {
                    setErrorMsg(err.message)
                    setScreen('error')
                  }
                }}
                onRechazar={async () => {
                  await api.rechazar(pipeline, plan.token).catch(() => {})
                  setPlan(null)
                  setScreen('rejected')
                }}
              />
            )}
            {screen === 'writing'   && <Loader titulo="Escribiendo y subiendo a Drive" sub={MESES.find(m => m.value === mes)?.label ?? mes} mode="writing" />}
            {screen === 'report'    && <Reporte reporte={reporte} mes={MESES.find(m => m.value === mes)?.label ?? mes} onBack={() => setScreen('panel')} />}
            {screen === 'rejected'  && <Rechazado onBack={() => setScreen('panel')} />}
          </div>
        </main>
        <footer className="border-t border-slate-200 bg-white px-6 py-4 text-center lg:px-10">
          <p className="text-xs text-slate-500">
            <span className="font-semibold text-slate-700">Orión by K&amp;K</span> — La propiedad intelectual y el agente pertenecen a <span className="font-semibold text-slate-700">K&amp;K</span>. © 2026 K&amp;K · Uso interno.
          </p>
        </footer>
      </div>
    </div>
  )
}
