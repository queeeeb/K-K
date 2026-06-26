import { useState } from 'react'
import { Lock, LogIn, Building2 } from 'lucide-react'
import OrionSky from './OrionSky'
import api from '../api'

export default function Login({ onSuccess }) {
  const [usuario,  setUsuario]  = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.login(usuario.trim(), password)
      onSuccess(usuario.trim())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="font-ui relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-900 px-6">
      <OrionSky />
      <div className="relative w-full max-w-sm">
        <div className="mb-4 mt-6 flex flex-col items-center text-center">
          <h1 className="text-3xl font-bold tracking-tight text-white">Orión</h1>
          <p className="mt-1 text-sm font-medium tracking-wide text-amber-400">by K&amp;K</p>
        </div>
        <div className="rounded-2xl bg-white/40 p-7 shadow-2xl ring-1 ring-white/30 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-slate-900">Iniciar sesión</h2>
          <p className="mt-1 text-sm text-slate-700">Accede con tu usuario individual</p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Usuario</label>
              <div className="relative">
                <Building2 size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={usuario} onChange={e => setUsuario(e.target.value)} placeholder="ana.lopez" required
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Contraseña</label>
              <div className="relative">
                <Lock size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="••••••••" required
                  className="w-full rounded-lg border border-slate-300 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-slate-900 focus:ring-4 focus:ring-slate-900/10" />
              </div>
            </div>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}
            <button type="submit" disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:ring-4 focus:ring-slate-900/20 disabled:opacity-60">
              <LogIn size={16} /> {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>
          <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-slate-400">
            <Lock size={12} /> Autenticación JWT · expira en 8h · sin registro público
          </p>
        </div>
        <p className="mt-6 text-center text-xs text-slate-500">© 2026 K&amp;K · Orión es propiedad intelectual de K&amp;K</p>
      </div>
    </div>
  )
}
