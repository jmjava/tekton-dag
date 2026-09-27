# @tekton-dag/baggage

Transfers the **original override header** hop-to-hop. Call `install()` / `adoptIncoming()`. Spec: [docs/BAGGAGE-CONTRACT.md](../../docs/BAGGAGE-CONTRACT.md).

## Usage

```javascript
import { adoptIncoming, createBaggageConfig, install } from '@tekton-dag/baggage'

const config = createBaggageConfig({
  enabled: true,
  role: 'originator', // or forwarder / terminal from the stack
  headerName: 'x-dev-session',
})

// Server: keep the inbound PR header
adoptIncoming({ headers: req.headers }, config)

// Browser + Node: patch fetch so every call copies that value
const uninstall = install(config)
```

Originator mint (`sessionValue` / `VITE_DEV_SESSION`) is used only when no header, cookie, or query arrived.

```bash
./scripts/emit-baggage-env.sh --stack stacks/stack-one.yaml --app demo-fe --format vite
npm test
```
