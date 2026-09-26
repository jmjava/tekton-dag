import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  adoptIncoming,
  createAxiosInterceptor,
  createBaggageConfig,
  createBaggageFetch,
  incomingSession,
  install,
  mergeBaggage,
  outgoingSession,
  parseBaggage,
  resetAdoptedIncoming,
  serializeBaggage,
} from '../src/index.js'

const vectors = JSON.parse(
  readFileSync(
    join(dirname(fileURLToPath(import.meta.url)), '../../baggage-contract/vectors.json'),
    'utf8',
  ),
)

afterEach(() => {
  resetAdoptedIncoming()
})

describe('W3C Baggage codec vectors', () => {
  for (const case_ of vectors.codec) {
    it(case_.name, () => {
      if (case_.name === 'parse-empty') {
        for (const raw of case_.parse) expect(parseBaggage(raw)).toEqual({})
      } else if (case_.name.startsWith('parse-')) {
        expect(parseBaggage(case_.header)).toEqual(case_.expected)
      } else if (case_.name.startsWith('merge-')) {
        const result = mergeBaggage(case_.existing, case_.key, case_.value)
        if (case_.equals) expect(result).toBe(case_.equals)
        for (const part of case_.contains || []) expect(result).toContain(part)
        for (const part of case_.excludes || []) expect(result).not.toContain(part)
      } else if (case_.name === 'round-trip') {
        expect(serializeBaggage(parseBaggage(case_.header))).toBe(case_.header)
      }
    })
  }
})

describe('role vectors preserve original override', () => {
  for (const case_ of vectors.resolveIncoming) {
    it(case_.name, () => {
      expect(
        incomingSession({
          role: case_.role,
          header: case_.header,
          cookie: case_.cookie,
          query: case_.query,
          sessionValue: case_.sessionValue,
          enabled: case_.enabled ?? true,
        }),
      ).toBe(case_.expected ?? null)
    })
  }
  for (const case_ of vectors.resolveOutgoing) {
    it(case_.name, () => {
      expect(
        outgoingSession({
          role: case_.role,
          contextValue: case_.context,
          sessionValue: case_.sessionValue,
        }),
      ).toBe(case_.expected ?? null)
    })
  }
})

describe('createBaggageFetch', () => {
  it('originator mints when nothing incoming', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'originator',
      sessionValue: 'my-session',
    })
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test')
    const headers = new Headers(mockFetch.mock.calls[0][1].headers)
    expect(headers.get('x-dev-session')).toBe('my-session')
    expect(headers.get('baggage')).toContain('dev-session=my-session')
  })

  it('originator transfers the original incoming override', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'originator',
      sessionValue: 'minted',
    })
    adoptIncoming({ header: 'pr-42' }, config)
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test')
    const headers = new Headers(mockFetch.mock.calls[0][1].headers)
    expect(headers.get('x-dev-session')).toBe('pr-42')
  })

  it('forwarder copies adopted incoming and does not mint', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'forwarder',
      sessionValue: 'must-not-mint',
    })
    adoptIncoming({ header: 'pr-42' }, config)
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test')
    expect(new Headers(mockFetch.mock.calls[0][1].headers).get('x-dev-session')).toBe('pr-42')
  })

  it('forwarder without incoming sends nothing', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'forwarder',
      sessionValue: 'must-not-mint',
    })
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test')
    expect(new Headers(mockFetch.mock.calls[0][1]?.headers || {}).get('x-dev-session')).toBeNull()
  })

  it('terminal never sets headers', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'terminal',
      sessionValue: 'should-not',
    })
    adoptIncoming({ header: 'pr-42' }, config)
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test')
    const headers = new Headers(mockFetch.mock.calls[0][1]?.headers || {})
    expect(headers.get('x-dev-session')).toBeNull()
  })

  it('disabled config passes through', async () => {
    const config = createBaggageConfig({
      enabled: false,
      role: 'originator',
      sessionValue: 'ignored',
    })
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test', { headers: { Accept: 'text/plain' } })
    expect(new Headers(mockFetch.mock.calls[0][1].headers).get('x-dev-session')).toBeNull()
  })

  it('merges with existing baggage header', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'originator',
      sessionValue: 'sess',
    })
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    await createBaggageFetch(config, mockFetch)('http://api/test', {
      headers: { baggage: 'traceId=abc' },
    })
    const baggage = new Headers(mockFetch.mock.calls[0][1].headers).get('baggage')
    expect(baggage).toContain('traceId=abc')
    expect(baggage).toContain('dev-session=sess')
  })

  it('install patches global fetch and copies the original header', async () => {
    const config = createBaggageConfig({
      enabled: true,
      role: 'forwarder',
    })
    adoptIncoming({ header: 'pr-7' }, config)
    const mockFetch = vi.fn().mockResolvedValue(new Response('ok'))
    const original = globalThis.fetch
    globalThis.fetch = mockFetch
    const uninstall = install(config)
    await fetch('http://api/test')
    expect(new Headers(mockFetch.mock.calls[0][1].headers).get('x-dev-session')).toBe('pr-7')
    uninstall()
    globalThis.fetch = original
  })
})

describe('createAxiosInterceptor', () => {
  it('originator adds minted headers', () => {
    const interceptor = createAxiosInterceptor(
      createBaggageConfig({ enabled: true, role: 'originator', sessionValue: 'ax-session' }),
    )
    const axConfig = interceptor({ headers: {} })
    expect(axConfig.headers['x-dev-session']).toBe('ax-session')
    expect(axConfig.headers.baggage).toContain('dev-session=ax-session')
  })

  it('terminal leaves axios config unchanged', () => {
    const interceptor = createAxiosInterceptor(
      createBaggageConfig({ enabled: true, role: 'terminal' }),
    )
    const axConfig = interceptor({ headers: {} })
    expect(axConfig.headers['x-dev-session']).toBeUndefined()
  })
})
