# Cloudflare Tunnel for Tekton EventListener

Expose the Tekton EventListener at **https://tekton-el.menkelabs.com** so GitHub webhooks can reach your local cluster.

---

## Steps (run in order)

### Step 1. Tunnel config (already done)

`~/.cloudflared/config.yml` has been updated with:

- **tekton-el.menkelabs.com** → `http://localhost:8080` (EventListener)
- **login.menkelabs.com** → `http://localhost:8090` (unchanged)

Tunnel ID: `6e3bb35c-d779-44fa-a6d2-b913459b52a3` (menkelabs-sso-tunnel-config).

**Config location:** `$HOME/.cloudflared/config.yml` (e.g. `/home/ubuntu/.cloudflared/config.yml`).

---

### Step 2. DNS in Cloudflare

Add a **CNAME** so the hostname points at your tunnel: **tekton-el** → `6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com`.

**Option A — API script (recommended):**

1. Create a Cloudflare API token with **Zone → DNS → Edit** and **Zone → Zone → Read** (or use an account-level token that can list zones).
2. Add to `.env`: `CLOUDFLARE_API_TOKEN=your_token` and `CLOUDFLARE_ZONE_ID=your_zone_id` (Zone ID is per-domain: Dashboard → menkelabs.com → Overview → Zone ID on the right; not the Account ID).
3. Run:
   ```bash
   cd /home/ubuntu/github/jmjava/tekton-dag
   set -a && source .env && set +a
   ./scripts/cloudflare-add-tunnel-cname.sh
   ```
   If the token cannot list zones (e.g. zone-scoped token), get your Zone ID from Dashboard → menkelabs.com → Overview → Zone ID, then:
   ```bash
   ./scripts/cloudflare-add-tunnel-cname.sh --zone-id YOUR_ZONE_ID
   ```
   Options: `--zone menkelabs.com`, `--zone-id` (skip lookup), `--name tekton-el`, `--target 6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com`.

**Option B — Manual:**

| Type  | Name       | Target                                                         |
|-------|------------|----------------------------------------------------------------|
| CNAME | tekton-el  | `6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com`       |

- **Cloudflare Dashboard:** DNS → Add record → CNAME **tekton-el** → target `6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com`.
- **Zero Trust:** Access → Tunnels → tunnel `menkelabs-sso-tunnel-config` → Public Hostname → Add **tekton-el.menkelabs.com** → Service **http://localhost:8080**.

---

### Step 3. Run the tunnel

Start the tunnel that uses the config above (so **tekton-el.menkelabs.com** and **login.menkelabs.com** are active):

```bash
cloudflared tunnel run menkelabs-sso-tunnel-config
```

Background:

```bash
cloudflared tunnel run menkelabs-sso-tunnel-config &
```

**Verified:** Tunnel started successfully; connections registered (ewr11, ewr12, ewr14).

---

### Step 4. Expose EventListener on localhost:8080

Port-forward the EventListener so the tunnel can reach it:

```bash
kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines
```

Background:

```bash
kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines &
```

**Verified:** Port-forward started; forwarding 127.0.0.1:8080 → 8080.

---

### Step 5. Configure GitHub webhooks

With the tunnel and port-forward running, and DNS in place:

```bash
cd /home/ubuntu/github/jmjava/tekton-dag
set -a && source .env && set +a
./scripts/configure-github-webhooks.sh --stack stack-one.yaml
```

Requires in `.env`:

- `GITHUB_TOKEN` (or `GH_TOKEN`) with `admin:repo_hook` or `repo` scope
- `EVENT_LISTENER_URL=https://tekton-el.menkelabs.com`

**Verified run (2026-02-28):**

- Webhook URL used: `https://tekton-el.menkelabs.com`
- Created webhooks for: **jmjava/tekton-dag-vue-fe**, **jmjava/tekton-dag-spring-boot**, **jmjava/tekton-dag-spring-boot-gradle**
- Cluster secret `github-webhook-secret` in namespace `tekton-pipelines` updated

---

## One-shot: run all steps (after DNS is set)

```bash
# 1. Start tunnel (background)
cloudflared tunnel run menkelabs-sso-tunnel-config &

# 2. Start port-forward (background)
kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines &

# 3. Wait for listeners
sleep 5

# 4. Configure webhooks
cd /home/ubuntu/github/jmjava/tekton-dag
set -a && source .env && set +a
./scripts/configure-github-webhooks.sh --stack stack-one.yaml
```

---

## Summary

| Step | Action | Status |
|------|--------|--------|
| 1 | Tunnel config: tekton-el.menkelabs.com → localhost:8080 in `~/.cloudflared/config.yml` | Done |
| 2 | DNS: CNAME **tekton-el** → `6e3bb35c-d779-44fa-a6d2-b913459b52a3.cfargotunnel.com` | Manual in Cloudflare |
| 3 | Run `cloudflared tunnel run menkelabs-sso-tunnel-config` | Run (or run in background) |
| 4 | Run `kubectl port-forward svc/el-stack-event-listener 8080:8080 -n tekton-pipelines` | Run (or run in background) |
| 5 | Run `./scripts/configure-github-webhooks.sh` with `.env` sourced | Run once; webhooks created |

After this, merging a PR in any of the three sample app repos sends a webhook to **https://tekton-el.menkelabs.com**, and the Tekton `pr-merged` trigger runs the merge pipeline.
