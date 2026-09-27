/**
 * Role-aware W3C baggage / x-dev-session for browser and Node.
 *
 * Invariant: the original override header (the session that selects a PR
 * container somewhere in the stack) is transferred unchanged hop-to-hop.
 * Call install() / adoptIncoming() — do not write your own header code.
 */

const ROLES = new Set(['originator', 'forwarder', 'terminal'])

export function firstNonBlank(...values) {
  for (const raw of values) {
    if (raw == null) continue
    const text = String(raw).trim()
    if (text) return text
  }
  return null
}

export function normalizeRole(role) {
  if (role == null || String(role).trim() === '') return 'forwarder'
  const text = String(role).trim().toLowerCase()
  return ROLES.has(text) ? text : null
}

export function incomingSession({
  role,
  header,
  cookie,
  query,
  sessionValue,
  enabled = true,
} = {}) {
  if (!enabled) return null
  const resolved = normalizeRole(role)
  if (!resolved) return null
  const incoming = firstNonBlank(header, cookie, query)
  if (resolved === 'originator') return firstNonBlank(incoming, sessionValue)
  return incoming
}

export function outgoingSession({ role, contextValue, sessionValue } = {}) {
  const resolved = normalizeRole(role)
  if (resolved === 'originator') return firstNonBlank(contextValue, sessionValue)
  if (resolved === 'forwarder') return firstNonBlank(contextValue)
  return null
}

export function parseBaggage(header) {
  const entries = {}
  if (!header || !String(header).trim()) return entries
  for (const member of String(header).split(',')) {
    const trimmed = member.trim()
    if (!trimmed) continue
    const eq = trimmed.indexOf('=')
    if (eq < 1) continue
    entries[trimmed.substring(0, eq).trim()] = trimmed.substring(eq + 1).trim()
  }
  return entries
}

export function mergeBaggage(existingHeader, key, value) {
  const entries = parseBaggage(existingHeader)
  entries[key] = value
  return serializeBaggage(entries)
}

export function serializeBaggage(entries) {
  return Object.entries(entries)
    .map(([k, v]) => `${k}=${v}`)
    .join(',')
}

export function createBaggageConfig(overrides = {}) {
  return {
    headerName: overrides.headerName || 'x-dev-session',
    baggageKey: overrides.baggageKey || 'dev-session',
    sessionValue: overrides.sessionValue || '',
    role: normalizeRole(overrides.role ?? 'forwarder'),
    enabled: overrides.enabled ?? false,
  }
}

export function defaultConfig() {
  const env = (typeof import.meta !== 'undefined' && import.meta.env) || {}
  // Default off. Production Docker images may still set VITE_BAGGAGE_ENABLED=true
  // so intercepts keep the original override on browser fetch.
  return createBaggageConfig({
    headerName: env.VITE_BAGGAGE_HEADER_NAME,
    baggageKey: env.VITE_BAGGAGE_KEY,
    sessionValue: env.VITE_DEV_SESSION,
    role: env.VITE_BAGGAGE_ROLE,
    enabled: env.VITE_BAGGAGE_ENABLED === 'true',
  })
}

let adopted = { header: '', cookie: '', query: '' }

export function adoptIncoming(incoming = {}, config) {
  const cfg = config || defaultConfig()
  const headers = incoming.headers || {}
  const headerFromMap =
    incoming.header ||
    headers[cfg.headerName] ||
    headers[String(cfg.headerName).toLowerCase()] ||
    ''
  adopted = {
    header: headerFromMap || '',
    cookie: incoming.cookie || '',
    query: incoming.query || incoming.search || '',
  }
  return { ...adopted }
}

export function resetAdoptedIncoming() {
  adopted = { header: '', cookie: '', query: '' }
}

function readCookie(cookieHeader, name) {
  if (!cookieHeader) return ''
  const parts = String(cookieHeader).split(';')
  for (const part of parts) {
    const trimmed = part.trim()
    if (!trimmed) continue
    const eq = trimmed.indexOf('=')
    if (eq < 1) continue
    if (trimmed.slice(0, eq).trim() === name) return trimmed.slice(eq + 1).trim()
  }
  return ''
}

function browserSources(headerName) {
  let cookie = ''
  let query = ''
  try {
    if (typeof document !== 'undefined' && document.cookie) {
      cookie = readCookie(document.cookie, headerName)
    }
    if (typeof location !== 'undefined' && location.search) {
      query = new URLSearchParams(location.search).get(headerName) || ''
    }
  } catch {
    // non-browser
  }
  return { cookie, query }
}

export function resolveOutgoing(config) {
  const cfg = config || defaultConfig()
  const browser = browserSources(cfg.headerName)
  const context = incomingSession({
    role: cfg.role,
    header: adopted.header,
    cookie: firstNonBlank(adopted.cookie, browser.cookie),
    query: firstNonBlank(adopted.query, browser.query),
    sessionValue: cfg.sessionValue,
    enabled: cfg.enabled,
  })
  return outgoingSession({
    role: cfg.role,
    contextValue: context,
    sessionValue: cfg.sessionValue,
  })
}

function applyHeaders(headersInit, config, value) {
  const headers = new Headers(headersInit || {})
  headers.set(config.headerName, value)
  const existing = headers.get('baggage') || ''
  headers.set('baggage', mergeBaggage(existing, config.baggageKey, value))
  return headers
}

export function createBaggageFetch(config, baseFetch = globalThis.fetch) {
  const resolvedConfig = config || defaultConfig()

  return function baggageFetch(url, options = {}) {
    if (!resolvedConfig.enabled) {
      return baseFetch(url, options)
    }
    const value = resolveOutgoing(resolvedConfig)
    if (!value) return baseFetch(url, options)
    const headers = applyHeaders(options.headers, resolvedConfig, value)
    return baseFetch(url, { ...options, headers })
  }
}

export function createAxiosInterceptor(config) {
  const resolvedConfig = config || defaultConfig()

  return function baggageInterceptor(axiosConfig) {
    if (!resolvedConfig.enabled) return axiosConfig
    const value = resolveOutgoing(resolvedConfig)
    if (!value) return axiosConfig
    axiosConfig.headers = axiosConfig.headers || {}
    axiosConfig.headers[resolvedConfig.headerName] = value
    const existing = axiosConfig.headers.baggage || axiosConfig.headers['baggage'] || ''
    axiosConfig.headers.baggage = mergeBaggage(
      existing,
      resolvedConfig.baggageKey,
      value,
    )
    return axiosConfig
  }
}

export function install(config) {
  const resolved = config || defaultConfig()
  const original = globalThis.fetch
  const wrapped = createBaggageFetch(resolved, original)
  globalThis.fetch = wrapped
  return function uninstall() {
    if (globalThis.fetch === wrapped) globalThis.fetch = original
  }
}
