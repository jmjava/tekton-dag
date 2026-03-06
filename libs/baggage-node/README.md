# @tekton-dag/baggage

Role-aware W3C baggage / `x-dev-session` middleware for browser and Node.js applications.

## Installation

```bash
npm install @tekton-dag/baggage
# or from local path:
npm install /path/to/tekton-dag/libs/baggage-node
```

## Configuration

```javascript
import { createBaggageConfig } from '@tekton-dag/baggage'

const config = createBaggageConfig({
  enabled: true,
  role: 'originator',       // 'originator' | 'forwarder' | 'terminal'
  headerName: 'x-dev-session',
  baggageKey: 'dev-session',
  sessionValue: 'my-session',
})
```

## Usage

### fetch wrapper
```javascript
import { createBaggageFetch, createBaggageConfig } from '@tekton-dag/baggage'

const config = createBaggageConfig({ enabled: true, role: 'originator', sessionValue: 'sess-1' })
const baggageFetch = createBaggageFetch(config)
await baggageFetch('http://api/endpoint')
```

### Axios interceptor
```javascript
import { createAxiosInterceptor, createBaggageConfig } from '@tekton-dag/baggage'
import axios from 'axios'

const config = createBaggageConfig({ enabled: true, role: 'originator', sessionValue: 'sess-1' })
axios.interceptors.request.use(createAxiosInterceptor(config))
```

## Production safety

- **Build-time**: list in `devDependencies`. Production `npm ci --omit=dev` excludes it.
- **Runtime**: `enabled: false` by default. Vite tree-shakes unused branches in production builds.

## Testing

```bash
npm install
npm test
```
