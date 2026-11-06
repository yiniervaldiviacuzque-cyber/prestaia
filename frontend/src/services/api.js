const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '')
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export function getSession() {
  try {
    return JSON.parse(localStorage.getItem('prestaia_session') || 'null')
  } catch {
    return null
  }
}

export function saveSession(session) {
  localStorage.setItem('prestaia_session', JSON.stringify(session))
}

export function clearSession() {
  localStorage.removeItem('prestaia_session')
}

export async function signOut() {
  const session = getSession()

  if (session?.access_token && SUPABASE_URL && SUPABASE_ANON_KEY) {
    await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        apikey: SUPABASE_ANON_KEY,
      },
    }).catch(() => {})
  }

  clearSession()
}

export async function signIn(email, password) {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error('Configura las variables de Supabase para iniciar sesión.')
  }

  let response
  try {
    response = await fetch(
      `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          apikey: SUPABASE_ANON_KEY,
        },
        body: JSON.stringify({ email, password }),
      }
    )
  } catch {
    throw new Error('No se pudo conectar con Supabase Auth. Revisa tu conexión e inténtalo nuevamente.')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.msg || data.message || data.error_description || 'No se pudo iniciar sesión.')
  }

  saveSession(data)
  return data
}

let refreshPromise = null

async function refreshSession() {
  const session = getSession()

  if (!session?.refresh_token || !SUPABASE_URL || !SUPABASE_ANON_KEY) {
    clearSession()
    return null
  }

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await fetch(
          `${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              apikey: SUPABASE_ANON_KEY,
            },
            body: JSON.stringify({
              refresh_token: session.refresh_token,
            }),
          }
        )

        const data = await response.json().catch(() => ({}))

        if (!response.ok || !data.access_token) {
          clearSession()
          return null
        }

        saveSession(data)
        return data
      } catch {
        return null
      } finally {
        refreshPromise = null
      }
    })()
  }

  return refreshPromise
}

async function sendRequest(path, options = {}, token = getSession()?.access_token) {
  const headers = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...options.headers,
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  try {
    return await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    })
  } catch {
    throw new Error('No se pudo conectar con PRESTAIA API. Verifica que el backend esté iniciado.')
  }
}

export async function api(path, options = {}) {
  let session = getSession()
  let response = await sendRequest(path, options, session?.access_token)

  if (response.status === 401) {
    session = await refreshSession()

    if (session?.access_token) {
      response = await sendRequest(path, options, session.access_token)
    } else {
      clearSession()
      throw new Error('Tu sesión expiró. Inicia sesión nuevamente.')
    }
  }

  if (response.status === 204) return null

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = data.detail ?? data.message ?? data.msg
    let message

    if (Array.isArray(detail)) {
      message = detail.map(item => {
        const location = Array.isArray(item?.loc)
          ? item.loc.filter(part => part !== "body").join(".")
          : ""
        const description = item?.msg || item?.message || JSON.stringify(item)
        return location ? `${location}: ${description}` : description
      }).join(" | ")
    } else if (detail && typeof detail === "object") {
      message = detail.message || detail.msg || JSON.stringify(detail)
    } else {
      message = detail ? String(detail) : `Error de servicio (${response.status})`
    }

    throw new Error(message)
  }

  return data
}

export async function download(path, filename) {
  let session = getSession()
  let response = await sendRequest(path, {}, session?.access_token)

  if (response.status === 401) {
    session = await refreshSession()

    if (session?.access_token) {
      response = await sendRequest(path, {}, session.access_token)
    } else {
      clearSession()
      throw new Error('Tu sesión expiró. Inicia sesión nuevamente.')
    }
  }

  if (!response.ok) {
    throw new Error('No se pudo descargar el reporte.')
  }

  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
