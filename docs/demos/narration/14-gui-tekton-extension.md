# Narration — Segment 14: Extending the GUI for more Tekton (M12.2)

**Target duration:** ~2–3 minutes. **Visual:** editor split backend route + frontend store.

## Script (edit for voice)

1. To add a new operator surface — for example TaskRun logs or Tekton Results read-only views — start in Flask.
2. Add a JSON route that wraps the Kubernetes client; return stable shapes the UI can table or chart.
3. Add pytest with the same mock style as existing route tests.
4. In Vue, add or extend a Pinia store using `useApi` and `teamUrl` for team-scoped reads.
5. Add a view and router entry, then a Playwright spec so regressions catch breaks.
6. The extension guide in the repo lists concrete files and ideas for deeper Tekton coverage.
