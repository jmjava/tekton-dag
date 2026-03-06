# M4 §2.5: EventListener per namespace (webhook routing)

When using multiple namespaces (e.g. `tekton-test` and `tekton-pipelines`), each namespace has its own EventListener. GitHub (or your CI) must send webhook events to the correct URL for the environment.

## Per-namespace EventListener

- **Production** (`tekton-pipelines`): EventListener `stack-event-listener`, Service `el-stack-event-listener`. Webhook URL is the one used for real PR/merge events.
- **Test** (`tekton-test`): After running `bootstrap-namespace.sh tekton-test`, the same triggers YAML is applied in that namespace, so you get a separate EventListener and Service there.

Pipeline and trigger YAML do not hardcode namespace; they are applied with `kubectl apply -f pipeline/ -n <namespace>`, so the EventListener and its TriggerTemplates live in that namespace. PipelineRuns created by the EventListener are created in the same namespace as the EventListener.

## Webhook URL routing

1. **Same cluster, different namespaces**  
   Each namespace has a distinct Kubernetes Service (e.g. `el-stack-event-listener.tekton-pipelines.svc.cluster.local` vs `el-stack-event-listener.tekton-test.svc.cluster.local`). From outside the cluster you need different entry points:
   - **LoadBalancer / NodePort**: each Service gets its own external IP or port. Configure two webhook URLs in GitHub (e.g. one for production, one for test).
   - **Ingress**: define separate Ingress hosts or paths (e.g. `tekton-el.mydomain.com` → `tekton-pipelines`, `tekton-el-test.mydomain.com` → `tekton-test`).
   - **Cloudflare Tunnel** (or similar): run one tunnel per namespace, or one tunnel with different subdomains pointing to different Services. Example: `tekton-el.menkelabs.com` → prod, `tekton-el-test.menkelabs.com` → test. See `docs/CLOUDFLARE-TUNNEL-EVENTLISTENER.md` for tunnel setup.

2. **Local (Kind)**  
   Use `kubectl port-forward` to the EventListener Service in the desired namespace:
   ```bash
   kubectl port-forward -n tekton-test svc/el-stack-event-listener 8080:8080
   ```
   Then send webhooks to `http://localhost:8080` (or use a tool like ngrok to expose it). For production namespace, forward the same service in `tekton-pipelines`.

3. **GitHub webhook configuration**  
   - **Single environment**: one webhook URL pointing at production EventListener.  
   - **Multi-environment**: one webhook URL per environment (e.g. prod vs test), each targeting the corresponding EventListener’s public URL. Use GitHub’s “Which events?” and repository filters so test repos or branches can target the test URL.

## Summary

- Each namespace has its own EventListener and Service; no shared URL.
- Route webhooks by URL (different host/path or port) to the namespace you want.
- PipelineRuns created by triggers run in the same namespace as the EventListener.
