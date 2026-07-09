const BASE = ''  // proxy de Vite redirige al backend

let _token = localStorage.getItem('orion_jwt') || null
let _usuario = localStorage.getItem('orion_user') || ''

function setToken(jwt) {
  _token = jwt
  if (jwt) localStorage.setItem('orion_jwt', jwt)
  else localStorage.removeItem('orion_jwt')
}

function clearToken() {
  setToken(null)
  _usuario = ''
  localStorage.removeItem('orion_user')
}

function getUsuario() { return _usuario }

async function _fetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  const res = await fetch(BASE + path, { ...options, headers })
  if (res.status === 409) {
    const body = await res.json()
    const err = new Error('Mes bloqueado')
    err.locked = true
    err.locked_by = body.detail?.replace('Locked by ', '') ?? 'otro usuario'
    throw err
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Error ${res.status}`)
  }
  return res.json()
}

async function login(usuario, password) {
  const data = await _fetch('/login', {
    method: 'POST',
    body: JSON.stringify({ usuario, password }),
  })
  setToken(data.access_token)
  _usuario = usuario
  localStorage.setItem('orion_user', usuario)
  return data
}

async function procesar(pipeline, mes, archivos = {}, tc = {}) {
  const fd = new FormData()
  fd.append('mes', mes)
  for (const [slot, file] of Object.entries(archivos)) {
    if (file) fd.append(slot, file)
  }
  const campoTc = { USD: 'tc_usd', EUR: 'tc_eur', CAD: 'tc_cad' }
  for (const [moneda, campo] of Object.entries(campoTc)) {
    if (tc[moneda] != null && tc[moneda] !== '') fd.append(campo, tc[moneda])
  }
  const headers = {}
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  const res = await fetch(`${BASE}/procesar/${pipeline}`, { method: 'POST', headers, body: fd })
  if (res.status === 409) {
    const b = await res.json()
    const err = new Error('Mes bloqueado'); err.locked = true
    err.locked_by = b.detail?.replace('Locked by ', '') ?? 'otro usuario'
    throw err
  }
  if (!res.ok) {
    const b = await res.json().catch(() => ({}))
    throw new Error(b.detail || `Error ${res.status}`)
  }
  return res.json()
}

async function confirmar(pipeline, token) {
  return _fetch(`/confirmar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

async function rechazar(pipeline, token) {
  return _fetch(`/rechazar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ token }),
  })
}

function getToken() { return _token }

async function pendientes() {
  return _fetch('/pendientes')
}

async function recuperar(pipeline, mes) {
  return _fetch(`/recuperar/${pipeline}?mes=${mes}`)
}

async function bitacora(pipeline) {
  const qs = pipeline ? `?pipeline=${pipeline}` : ''
  return _fetch(`/bitacora${qs}`)
}

async function nombrar(pipeline, token, nombres) {
  return _fetch(`/nombrar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ token, nombres }),
  })
}

async function descargar(archivo) {
  const res = await fetch(`/descargar/${archivo}`, {
    cache: 'no-store',
    headers: { Authorization: `Bearer ${_token}` },
  })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = archivo
  a.click()
  URL.revokeObjectURL(url)
}

export default { login, procesar, confirmar, rechazar, recuperar, pendientes, bitacora, descargar, nombrar, setToken, clearToken, getToken, getUsuario }
