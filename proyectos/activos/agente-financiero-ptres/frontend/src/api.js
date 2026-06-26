const BASE = ''  // proxy de Vite redirige al backend

let _token = localStorage.getItem('orion_jwt') || null

function setToken(jwt) {
  _token = jwt
  if (jwt) localStorage.setItem('orion_jwt', jwt)
  else localStorage.removeItem('orion_jwt')
}

function clearToken() {
  setToken(null)
}

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
  return data
}

async function procesar(pipeline, mes) {
  return _fetch(`/procesar/${pipeline}`, {
    method: 'POST',
    body: JSON.stringify({ mes }),
  })
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

export default { login, procesar, confirmar, rechazar, setToken, clearToken, getToken }
