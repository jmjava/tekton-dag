# Milestone 5: MetalBear mirrord PoC results

Evaluation of [mirrord](https://github.com/metalbear-co/mirrord) as an alternative to Telepresence for header-based traffic interception in the PR pipeline. See [milestones/milestone-5.md](../milestones/milestone-5.md) for full scope.

---

## 1. Installation

### mirrord CLI

```bash
# Automated (detects OS/arch, downloads the right binary):
./scripts/install-mirrord.sh

# Or manually (Linux x86_64, adjust tag):
TAG=$(curl -sS https://api.github.com/repos/metalbear-co/mirrord/releases/latest | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
curl -fsSL "https://github.com/metalbear-co/mirrord/releases/download/${TAG}/mirrord_linux_x86_64" -o mirrord
chmod +x mirrord && sudo mv mirrord /usr/local/bin/
```

**Note:** The release asset is a plain binary (`mirrord_linux_x86_64`), not a `.tar.gz`. A prior bad install can leave a **file** at `/tmp/mirrord`; this blocks mirrord from creating its working directory. Fix: `rm /tmp/mirrord`.

**Verified version:** `mirrord 3.193.0`

### Prerequisites

- Kind (or other Kubernetes) cluster with stack deployed in `staging`
- `kubectl` configured for the cluster
- mirrord binary in PATH (or local path)

---

## 2. PoC: Header-based intercept — PROVEN ✓

### 2.1 Config (`docs/mirrord-poc/mirrord.json`)

```json
{
  "target": {
    "path": "deployment/release-lifecycle-demo",
    "namespace": "staging"
  },
  "agent": {
    "namespace": "staging"
  },
  "feature": {
    "network": {
      "incoming": {
        "mode": "steal",
        "http_filter": {
          "header_filter": "x-dev-session: pr-test"
        }
      },
      "outgoing": true
    },
    "fs": "local"
  }
}
```

**Key config notes:**
- `target.namespace` = where the deployment lives (separate from `agent.namespace`)
- `feature.network.incoming.http_filter.header_filter` = the header predicate (regex supported)
- Do NOT set `"feature.env": "inherit"` — mirrord expects an env object; the string `"inherit"` causes a parse error

### 2.2 How to run

```bash
# Terminal 1 — local "PR" server (port 8080 to match container-port)
./mirrord exec -f docs/mirrord-poc/mirrord.json -- python3 docs/mirrord-poc/local_server.py

# Terminal 2 — port-forward to reach service from host
kubectl port-forward svc/release-lifecycle-demo 18080:80 -n staging

# Terminal 3 — validate
curl http://127.0.0.1:18080/                                  # → original
curl -H "x-dev-session: pr-test" http://127.0.0.1:18080/     # → local
```

### 2.3 Validation results

Tested against stack-one (`release-lifecycle-demo` deployment in `staging`):

| Step | Action | Expected | Actual | Pass |
|------|--------|----------|--------|------|
| 1 | `curl http://127.0.0.1:18080/` (no header, 5 rounds) | `tekton-dag-spring-boot` (original pod) | `tekton-dag-spring-boot` (5/5) | ✓ |
| 2 | `curl -H "x-dev-session: pr-test" http://127.0.0.1:18080/` (5 rounds) | `LOCAL-PR-RESPONSE` (local process) | `LOCAL-PR-RESPONSE` (5/5) | ✓ |

**Result: Header-based intercept works identically to Telepresence's `--http-match` flag. Original traffic is completely unaffected.**

---

## 3. In-pipeline feasibility

### 3.1 What mirrord spawns in the cluster

When `mirrord exec` runs, it automatically spawns a `mirrord-agent` **Job+Pod** in the target namespace. No Operator needed.

**Agent pod security context (observed):**

```yaml
securityContext:
  capabilities:
    add:
    - SYS_ADMIN
    - SYS_PTRACE
    - NET_ADMIN
  privileged: false
  hostPID: true
```

The agent mounts `/host/run` and `/host/var` from the node.

### 3.2 In-cluster execution (Tekton task) — feasibility

The `mirrord exec` pattern is designed for **local-process-to-cluster** use: it injects a shared library (`LD_PRELOAD`) into the local process and manages the agent remotely. For a Tekton task (fully in-cluster), the pattern changes:

| Aspect | Assessment |
|--------|------------|
| `mirrord exec` from a Tekton task pod | **Requires elevated privileges** (`SYS_ADMIN`, `hostPID`) on the task pod to inject the layer — not the agent pod. This is more invasive than Telepresence's current sidecar pattern. |
| mirrord Operator | Enables a cleaner in-cluster workflow via `MirrordWorkloadSession` CRD; does not require LD_PRELOAD injection on the task pod. Requires Operator install. |
| No Operator, no LD_PRELOAD | Not currently possible — `mirrord exec` fundamentally relies on library injection. |
| Agent auto-cleanup | **Advantage over Telepresence**: agent pod self-terminates on TTL (1s default) after the session ends; no explicit cleanup step needed. |

**Verdict:** Without the Operator, running `mirrord exec` from inside a Tekton task is impractical — it requires the task pod itself to have elevated Linux capabilities for library injection. The Telepresence sidecar approach is simpler for in-cluster use today.

---

## 4. Feature comparison

| Requirement | Telepresence | mirrord | Notes |
|-------------|--------------|---------|--------|
| Header-based intercept | `--http-match` | `feature.network.incoming.http_filter.header_filter` | **Parity — both work.** |
| Original traffic unaffected | ✓ (by design) | ✓ (confirmed in PoC) | **Parity.** |
| No persistent cluster component | Requires Traffic Manager (Helm chart) | Agent pod per session; auto-terminates on TTL | **mirrord advantage.** |
| In-cluster execution (Tekton task) | ✓ (sidecar pattern) | Requires Operator or elevated task pod | See §6 for recommended path. |
| **Multiple concurrent intercepts without overlap** | ✓ (Traffic Manager + per-intercept `--http-match`) | ✓ (per-session agent + `header_filter` per PR) | **Prerequisite for lower env; both support. mirrord: no shared component, natural isolation.** |
| Cleanup reliability | Requires explicit cleanup Tekton task | Agent exits automatically on session end | **mirrord advantage.** |
| OSS license | Apache 2.0 | MIT (core) + commercial (Teams/Operator) | Both acceptable. |
| Migration effort | — (current) | Medium — rearchitect intercept task | n/a |

---

## 5. MetalBear / mirrord Operator — security risks and mitigations

### 5.1 Security risks (agent and Operator)

The mirrord **agent** (and, when used, the **Operator**) require elevated privileges to intercept traffic at the pod/node level. Documented risks and how they can be mitigated are below.

| Risk | Description | Severity |
|------|-------------|----------|
| **Elevated Linux capabilities (agent pod)** | The agent runs with `SYS_ADMIN`, `SYS_PTRACE`, `NET_ADMIN` and `hostPID: true`. It can join network namespaces, modify routing, and access process/namespace state on the node. A compromised agent could be used to inspect or redirect traffic, or escalate on the node. | **High** if the cluster or namespace also runs production workloads. |
| **Host path mounts (agent)** | The agent mounts `/host/run` and `/host/var` from the node. This gives the agent visibility into node-level state (e.g. container runtimes, logs). A compromised agent could read or tamper with that data. | **Medium–High** depending on what else shares the node. |
| **Operator scope** | With the Operator, only the Operator needs cluster-wide or namespace-wide permissions to create agent Jobs; users get RBAC to create `MirrordWorkloadSession` resources. Centralizing privilege in the Operator reduces the blast radius of a single compromised user but means the Operator is a high-value target. | **Medium** — compromise of the Operator could allow creation of agents across namespaces. |
| **No production boundary** | If the same cluster (or same nodes) is used for production and for PR/intercept workloads, a compromised agent could affect production traffic or data. | **High** when production and dev share a cluster. |

These are inherent to any tool that does in-cluster traffic interception (including Telepresence’s Traffic Manager and sidecars, which also require elevated capabilities). The goal is to **contain the blast radius** so that intercept tooling never runs in or alongside production.

### 5.2 Mitigations — do not run in production

**Primary mitigation: use mirrord (and the Operator, if adopted) only in non-production environments.** That materially reduces risk and can make the trade-off acceptable for cost savings.

| Mitigation | What to do | Effect |
|------------|------------|--------|
| **No production** | Run the PR pipeline (and thus mirrord agent/Operator) only in **dev**, **test**, or **CI** namespaces or clusters. Never install the Operator or run intercepts in a cluster (or namespace) that runs production workloads. | Eliminates risk to production traffic and data. |
| **Dedicated dev/test cluster** | Use a separate Kubernetes cluster for PR pipelines and intercepts (e.g. Kind, or a dedicated dev cluster). Production runs in a different cluster with no mirrord/Telepresence. | Strong isolation; no shared nodes or control plane with production. **This project uses this model: production is a different cluster.** |
| **Namespace isolation** | If dev and prod share a cluster, restrict the Operator and agent Jobs to specific namespaces (e.g. `tekton-pipelines`, `staging`, `ci`). Use RBAC and network policies so agent pods cannot reach production namespaces. | Reduces blast radius; production namespaces are not in the same trust boundary as intercept tooling. |
| **Network policies** | Apply NetworkPolicies so that agent pods (and Tekton task pods using mirrord) can only talk to intended targets (e.g. staging apps) and cannot reach production Services. | Limits lateral movement and accidental production impact. |
| **RBAC** | Grant only the minimum RBAC needed for the Operator and for users (e.g. create `MirrordWorkloadSession` only in dev/test namespaces). Do not grant cluster-admin or broad write access. | Limits who can create intercept sessions and where. |
| **Pod security** | Use Pod Security Standards (e.g. restricted or baseline) on production namespaces; allow elevated capabilities only in dev/test namespaces where mirrord runs. | Ensures production stays locked down; dev/test accepts the known risk of intercept tooling. |

**Conclusion:** If mirrord (with or without the Operator) is used **only for dev/test/CI** and **never in production**, the main security risks are confined to non-production. That is an acceptable way to gain the licensing and operational benefits of mirrord while keeping production out of scope.

**This project’s architecture:** Production runs on a **separate cluster**. The PR pipeline (Tekton, intercepts, mirrord or Telepresence) runs only in the dev/test cluster. There is no shared control plane or nodes with production, so intercept tooling never runs in or alongside production. This satisfies the “dedicated dev/test cluster” mitigation by design.

### 5.3 Licensing and cost — Telepresence vs mirrord

| Aspect | Telepresence | mirrord |
|--------|--------------|---------|
| **OSS / free tier** | Community edition (Apache 2.0); some features require commercial license. | Core CLI + agent: **MIT**, free. No license cost for basic intercept. |
| **Commercial / Teams** | Telepresence Cloud / Teams licensing for team use, SSO, and advanced features. | mirrord for Teams (and Operator) may have commercial tiers; check MetalBear pricing. |
| **In-cluster (CI/pipeline)** | Often requires or is simplified by commercial licensing for multi-user or pipeline use. | With OSS agent-only (no Operator): free but task pod needs elevated caps. With Operator: possible commercial cost; compare to Telepresence. |

**Cost win:** Avoiding or reducing **Telepresence licensing** is a significant benefit. If the pipeline runs only in **non-production** (dev/test/CI), adopting mirrord with the mitigations above allows:

- **No Telepresence license** (or reduced seats) for that environment.
- **Same functional behavior** (header-based intercept, original traffic unchanged) as proven in the PoC.
- **Acceptable risk** when intercept tooling and Operator are confined to non-production and isolated from production (separate cluster or strict namespace + network policy).

Document the decision (e.g. “mirrord in dev/test/CI only, production unchanged”) in your runbooks and architecture docs so that future changes (e.g. running intercepts in prod) are explicitly re-evaluated for risk and licensing. For this project, production is a different cluster, so intercept tooling (mirrord or Telepresence) is already scoped to the non-production cluster only.

---

## 6. Traffic mirroring (bonus)

mirrord supports a **mirror mode** (`"mode": "mirror"` instead of `"steal"`) that duplicates traffic to the local process without stealing it from the original pod. This enables shadow testing. Not evaluated in this PoC; a follow-up could run a PR process in mirror mode alongside the original.

---

## 6. Recommendation: go with mirrord (lower environment)

**Recommendation: Use MetalBear mirrord for intercepts in the lower (dev/test) environment.**

### Rationale

| Prerequisite / goal | mirrord | Telepresence |
|--------------------|---------|--------------|
| **Multiple concurrent intercepts without overlap** | ✓ Each session gets its own agent Job; traffic is isolated by `header_filter` (e.g. `x-dev-session: pr-123` vs `pr-456`). No shared Traffic Manager; no overlap between PRs. | Depends on Traffic Manager and correct `--http-match` per intercept; possible contention or config drift. |
| **Cost (lower env only)** | **Free** — OSS (MIT). No license required for CLI + agent. | Often requires or benefits from commercial licensing for team/pipeline use. |
| **Production safety** | Production is a **different cluster**; intercept tooling never runs there. Risks confined to lower env. | Same. |
| **Header-based intercept parity** | ✓ Proven in PoC. | ✓ Current baseline. |

Given that (1) **multiple competing intercepts without overlap** in the lower environment is a prerequisite, (2) **mirrord cost is free**, and (3) **production is a different cluster**, mirrord is the better fit: it meets the concurrency requirement natively (per-session agents + header isolation), avoids Telepresence licensing cost, and keeps all intercept risk in the non-production cluster.

### In-cluster pipeline (Tekton)

For running intercepts from Tekton task pods (fully in-cluster), either:

- **Option A — mirrord Operator:** Install the mirrord Operator in the lower-environment cluster and use `MirrordWorkloadSession` (or equivalent) so task pods do not need `LD_PRELOAD` / elevated caps. Then the pipeline uses mirrord instead of Telepresence for deploy-intercept.
- **Option B — mirrord exec from task pod:** Task pod runs `mirrord exec` with elevated capabilities (`SYS_ADMIN`, `hostPID`). More invasive but no Operator install; document and restrict to dev/test namespace only.

Next step: prototype a `deploy-intercept-mirrord` task (Option A or B) and run the PR pipeline with mirrord; once validated, remove or make optional the Telepresence path to save licensing cost.

### Errors encountered during PoC

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid type: string "inherit", expected struct EnvFileConfig` | `"feature": {"env": "inherit"}` in config | Remove the `env` field entirely |
| `Failed to extract mirrord-layer to /tmp/mirrord/...: Not a directory` | Previous install left a **file** at `/tmp/mirrord` | `rm /tmp/mirrord` |
| `deployments.apps "release-lifecycle-demo" not found` | `"target": "deployment/..."` string form uses default namespace | Use object form: `"target": {"path": "deployment/...", "namespace": "staging"}` |

---

## 7. References

- [mirrord GitHub](https://github.com/metalbear-co/mirrord)
- [mirrord config options](https://metalbear.com/mirrord/docs/config/options)
- [Milestone 5](../milestones/milestone-5.md)
- Working config: [docs/mirrord-poc/mirrord.json](mirrord-poc/mirrord.json)
- Local server used for PoC: [docs/mirrord-poc/local_server.py](mirrord-poc/local_server.py)
