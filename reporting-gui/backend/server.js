#!/usr/bin/env node
/**
 * Tekton DAG Reporting API
 * Serves PipelineRuns, TaskRuns, trigger, repos. Uses kubectl for cluster access (MVP).
 * Env: PORT, KUBECONFIG (optional; kubectl uses default), REPO_ROOT (path to tekton-dag repo for generate-run.sh).
 */
import express from 'express';
import cors from 'cors';
import { spawn } from 'child_process';
import { readFileSync, existsSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const NAMESPACE = process.env.TEKTON_NAMESPACE || 'tekton-pipelines';
// Resolve REPO_ROOT: env, or walk up from backend dir until we find a 'stacks' folder
function resolveRepoRoot() {
  if (process.env.REPO_ROOT) return process.env.REPO_ROOT;
  let dir = join(__dirname, '..', '..');
  for (let i = 0; i < 5; i++) {
    if (existsSync(join(dir, 'stacks'))) return dir;
    dir = join(dir, '..');
  }
  return join(__dirname, '..', '..');
}
const REPO_ROOT = resolveRepoRoot();
const STACKS_DIR = join(REPO_ROOT, 'stacks');
const SCRIPTS_DIR = join(REPO_ROOT, 'scripts');
const GIT_SSH_SECRET_NAME = process.env.GIT_SSH_SECRET_NAME || 'git-ssh-key';
const CACHE_PVC = process.env.CACHE_PVC || 'build-cache';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const GITHUB_API = 'https://api.github.com';

function kubectl(args, input = null) {
  return new Promise((resolve, reject) => {
    const proc = spawn('kubectl', args, {
      stdio: input ? ['pipe', 'pipe', 'pipe'] : ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d; });
    proc.stderr.on('data', (d) => { stderr += d; });
    if (input) proc.stdin.write(input, () => proc.stdin.end());
    proc.on('close', (code) => {
      if (code !== 0) return reject(new Error(stderr || `kubectl exited ${code}`));
      try {
        resolve(JSON.parse(stdout || '{}'));
      } catch {
        resolve(stdout);
      }
    });
  });
}

function runScript(args, stdin = null) {
  return new Promise((resolve, reject) => {
    const proc = spawn(args[0], args.slice(1), {
      cwd: REPO_ROOT,
      stdio: stdin ? ['pipe', 'pipe', 'pipe'] : ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => { stdout += d; });
    proc.stderr.on('data', (d) => { stderr += d; });
    if (stdin) proc.stdin.write(stdin, () => proc.stdin.end());
    proc.on('close', (code) => {
      if (code !== 0) return reject(new Error(stderr || `Script exited ${code}`));
      resolve(stdout);
    });
  });
}

// GET /api/pipelineruns?limit=50&namespace=tekton-pipelines
app.get('/api/pipelineruns', async (req, res) => {
  try {
    const limit = Math.min(parseInt(req.query.limit, 10) || 50, 100);
    const namespace = req.query.namespace || NAMESPACE;
    const data = await kubectl([
      'get', 'pipelineruns', '-n', namespace,
      '-o', 'json',
      '--sort-by=.metadata.creationTimestamp',
    ]);
    const items = (data.items || []).slice(-limit).reverse();
    const paramsList = (pr) => pr.spec?.params || [];
    const param = (pr, name) => paramsList(pr).find((p) => p.name === name)?.value ?? null;
    const out = items.map((pr) => {
      const cond = (pr.status?.conditions || [])[0];
      const start = pr.status?.startTime;
      const end = pr.status?.completionTime;
      let duration = null;
      if (start && end) {
        duration = Math.round((new Date(end) - new Date(start)) / 1000);
      }
      const results = pr.status?.results || pr.status?.pipelineResults || [];
      const testSummary = results.find((r) => r.name === 'test-summary')?.value;
      return {
        name: pr.metadata?.name,
        namespace: pr.metadata?.namespace,
        pipeline: pr.spec?.pipelineRef?.name || '-',
        status: cond?.reason || 'Unknown',
        message: cond?.message,
        startTime: start,
        completionTime: end,
        durationSeconds: duration,
        testSummary: testSummary || null,
        prNumber: param(pr, 'pr-number') || null,
        changedApp: param(pr, 'changed-app') || null,
      };
    });
    res.json({ items: out });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/pipelineruns/:name?namespace=tekton-pipelines
app.get('/api/pipelineruns/:name', async (req, res) => {
  try {
    const namespace = req.query.namespace || NAMESPACE;
    const data = await kubectl(['get', 'pipelinerun', req.params.name, '-n', namespace, '-o', 'json']);
    const cond = (data.status?.conditions || [])[0];
    const start = data.status?.startTime;
    const end = data.status?.completionTime;
    const results = data.status?.results || data.status?.pipelineResults || [];
    const testSummary = results.find((r) => r.name === 'test-summary')?.value;
    res.json({
      name: data.metadata?.name,
      namespace: data.metadata?.namespace,
      pipeline: data.spec?.pipelineRef?.name,
      status: cond?.reason,
      message: cond?.message,
      startTime: start,
      completionTime: end,
      testSummary: testSummary || null,
      spec: data.spec,
      statusFull: data.status,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/taskruns?pipelineRun=name&namespace=tekton-pipelines
app.get('/api/taskruns', async (req, res) => {
  try {
    const namespace = req.query.namespace || NAMESPACE;
    const pipelineRun = req.query.pipelineRun;
    let args = ['get', 'taskruns', '-n', namespace, '-o', 'json'];
    if (pipelineRun) {
      args = ['get', 'taskruns', '-n', namespace, '-l', `tekton.dev/pipelineRun=${pipelineRun}`, '-o', 'json'];
    }
    const data = await kubectl(args);
    const items = (data.items || []).map((tr) => {
      const cond = (tr.status?.conditions || [])[0];
      return {
        name: tr.metadata?.name,
        pipelineRun: tr.metadata?.labels?.['tekton.dev/pipelineRun'],
        task: tr.spec?.taskRef?.name,
        status: cond?.reason,
        message: cond?.message,
        startTime: tr.status?.startTime,
        completionTime: tr.status?.completionTime,
        statusFull: tr.status,
      };
    });
    res.json({ items });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Build list of repos from stacks: platform + app repos from stack YAMLs
function getReposList() {
  const repoSet = new Map();
  repoSet.set('jmjava/tekton-dag', { id: 'jmjava/tekton-dag', owner: 'jmjava', repo: 'tekton-dag', apps: ['platform'], stacks: [] });
  if (!existsSync(STACKS_DIR)) return Array.from(repoSet.values());
  for (const f of readdirSync(STACKS_DIR)) {
    if (!f.endsWith('.yaml') || f === 'registry.yaml' || f === 'versions.yaml') continue;
    const path = join(STACKS_DIR, f);
    const content = readFileSync(path, 'utf8');
    // Match "- name: <app>" with 2 or more spaces before the dash (YAML list item)
    const appBlocks = content.split(/\n\s{2,}-\s+name:\s*/).slice(1);
    for (const block of appBlocks) {
      const nameMatch = block.match(/^\s*(\S+)/);
      const repoMatch = block.match(/repo:\s*(\S+)/);
      const appName = nameMatch ? nameMatch[1].trim() : '';
      const repo = repoMatch ? repoMatch[1].trim() : '';
      if (!repo || !appName) continue;
      const [owner, repoName] = repo.split('/');
      if (!owner || !repoName) continue;
      const id = `${owner}/${repoName}`;
      if (!repoSet.has(id)) repoSet.set(id, { id, owner, repo: repoName, apps: [], stacks: [] });
      const r = repoSet.get(id);
      r.apps.push(appName);
      if (!r.stacks.includes(f)) r.stacks.push(f);
    }
  }
  return Array.from(repoSet.values());
}

// GET /api/repos — list repos (platform + from stacks) with app and stack mapping
app.get('/api/repos', (_req, res) => {
  try {
    const repos = getReposList();
    res.json({ items: repos });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

async function githubFetch(path) {
  const headers = { Accept: 'application/vnd.github.v3+json' };
  if (GITHUB_TOKEN) headers.Authorization = `Bearer ${GITHUB_TOKEN}`;
  const r = await fetch(`${GITHUB_API}${path}`, { headers });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

// GET /api/repos/:owner/:repo/branches
app.get('/api/repos/:owner/:repo/branches', async (req, res) => {
  try {
    const { owner, repo } = req.params;
    const data = await githubFetch(`/repos/${owner}/${repo}/branches?per_page=30`);
    res.json({ items: data.map((b) => ({ name: b.name, sha: b.commit?.sha })) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/repos/:owner/:repo/tags
app.get('/api/repos/:owner/:repo/tags', async (req, res) => {
  try {
    const { owner, repo } = req.params;
    const data = await githubFetch(`/repos/${owner}/${repo}/tags?per_page=30`);
    res.json({ items: data.map((t) => ({ name: t.name, sha: t.commit?.sha })) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/repos/:owner/:repo/commits
app.get('/api/repos/:owner/:repo/commits', async (req, res) => {
  try {
    const { owner, repo } = req.params;
    const data = await githubFetch(`/repos/${owner}/${repo}/commits?per_page=20`);
    res.json({ items: data.map((c) => ({ sha: c.sha, message: c.commit?.message?.split('\n')[0], date: c.commit?.author?.date, url: c.html_url })) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/repos/:owner/:repo/prs?state=open|closed|all
app.get('/api/repos/:owner/:repo/prs', async (req, res) => {
  try {
    const { owner, repo } = req.params;
    const state = req.query.state === 'closed' || req.query.state === 'all' ? req.query.state : 'open';
    const data = await githubFetch(`/repos/${owner}/${repo}/pulls?state=${state}&per_page=30&sort=updated`);
    res.json({ items: data.map((p) => ({ number: p.number, title: p.title, state: p.state, url: p.html_url })) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/prs?state=open|closed|all — open PRs across all repos (from stacks)
app.get('/api/prs', async (req, res) => {
  try {
    const state = req.query.state === 'closed' || req.query.state === 'all' ? req.query.state : 'open';
    const repos = getReposList();
    const limitRepos = Math.min(parseInt(req.query.repos, 10) || 50, 50);
    const perRepo = Math.min(parseInt(req.query.per_page, 10) || 15, 30);
    const aggregated = [];
    const reposQueried = [];
    const reposSkipped = [];
    for (let i = 0; i < Math.min(repos.length, limitRepos); i++) {
      const r = repos[i];
      reposQueried.push(r.id);
      try {
        const data = await githubFetch(`/repos/${r.owner}/${r.repo}/pulls?state=${state}&per_page=${perRepo}&sort=updated`);
        for (const p of data) {
          aggregated.push({
            repoId: r.id,
            owner: r.owner,
            repo: r.repo,
            apps: r.apps || [],
            pr: { number: p.number, title: p.title, state: p.state, url: p.html_url },
          });
        }
      } catch (e) {
        reposSkipped.push({ id: r.id, error: e.message || String(e) });
        console.warn(`[api/prs] Skip ${r.id}: ${e.message || e}`);
        continue;
      }
    }
    res.json({ items: aggregated, reposQueried, reposSkipped });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/stacks — list stack files and apps (from registry) for trigger form
app.get('/api/stacks', (_req, res) => {
  try {
    const stacks = [];
    if (existsSync(STACKS_DIR)) {
      for (const f of readdirSync(STACKS_DIR)) {
        if (f.endsWith('.yaml') && f !== 'registry.yaml' && f !== 'versions.yaml') {
          stacks.push(f);
        }
      }
    }
    const apps = [];
    const regPath = join(STACKS_DIR, 'registry.yaml');
    if (existsSync(regPath)) {
      const content = readFileSync(regPath, 'utf8');
      const lines = content.split('\n');
      for (let i = 0; i < lines.length; i++) {
        const m = lines[i].match(/^\s{2}([\w-]+):\s*$/);
        if (m) {
          const name = m[1];
          const next = lines[i + 1];
          const stackMatch = next && next.match(/stack:\s*(\S+)/);
          apps.push({ name, stack: stackMatch ? stackMatch[1] : '' });
        }
      }
    }
    res.json({ stacks: stacks.sort(), apps });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/trigger — create a PipelineRun (pr/merge via generate-run.sh, bootstrap via inline YAML)
app.post('/api/trigger', async (req, res) => {
  try {
    const {
      pipelineType,
      stack,
      app,
      prNumber,
      gitUrl,
      gitRevision,
      imageRegistry,
      versionOverrides,
      buildImages,
      storageClass,
    } = req.body || {};

    if (!pipelineType || !['pr', 'bootstrap', 'merge'].includes(pipelineType)) {
      return res.status(400).json({ error: 'pipelineType must be pr, bootstrap, or merge' });
    }
    if (!stack) return res.status(400).json({ error: 'stack is required' });
    if (pipelineType === 'pr' && !prNumber) return res.status(400).json({ error: 'prNumber is required for PR runs' });
    if (!app) return res.status(400).json({ error: 'app (changed-app) is required' });

    const gitUrlVal = gitUrl || 'https://github.com/jmjava/tekton-dag.git';
    const gitRevVal = gitRevision || 'main';
    const registryVal = imageRegistry || 'localhost:5000';
    const storageVal = storageClass != null && storageClass !== '' ? storageClass : '';

    let yaml = '';

    if (pipelineType === 'bootstrap') {
      const stackPath = stack.startsWith('stacks/') ? stack : `stacks/${stack}`;
      yaml = `apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  generateName: stack-bootstrap-
  namespace: ${NAMESPACE}
spec:
  pipelineRef:
    name: stack-bootstrap
  taskRunTemplate:
    serviceAccountName: tekton-pr-sa
  params:
    - name: git-url
      value: "${gitUrlVal}"
    - name: git-revision
      value: "${gitRevVal}"
    - name: stack-file
      value: "${stackPath}"
    - name: image-registry
      value: "${registryVal}"
    - name: image-tag
      value: "base-1"
  workspaces:
    - name: shared-workspace
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          resources:
            requests:
              storage: 10Gi
    - name: ssh-key
      secret:
        secretName: ${GIT_SSH_SECRET_NAME}
    - name: build-cache
      persistentVolumeClaim:
        claimName: ${CACHE_PVC}
`;
    } else {
      const scriptPath = join(SCRIPTS_DIR, 'generate-run.sh');
      if (!existsSync(scriptPath)) return res.status(500).json({ error: 'generate-run.sh not found' });
      const args = [
        scriptPath,
        '--mode', pipelineType,
        '--stack', stack,
        '--app', app,
        '--git-url', gitUrlVal,
        '--git-revision', gitRevVal,
        '--registry', registryVal,
        '--storage-class', storageVal || 'gp3',
      ];
      if (pipelineType === 'pr') args.push('--pr', String(prNumber));
      if (versionOverrides && typeof versionOverrides === 'string') args.push('--version-overrides', versionOverrides);
      if (buildImages) args.push('--build-images');
      yaml = await runScript(args);
    }

    const result = await kubectl(['create', '-f', '-'], yaml);
    let name = null;
    if (typeof result === 'string' && result.includes('/')) {
      const part = result.split('/').pop().trim();
      name = part.split(/\s/)[0] || part;
    } else if (result && result.metadata && result.metadata.name) {
      name = result.metadata.name;
    }
    res.json({ ok: true, pipelineRun: name || 'created', namespace: NAMESPACE });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Health
app.get('/api/health', (_req, res) => {
  res.json({ ok: true });
});

app.listen(PORT, () => {
  console.log(`Reporting API listening on http://localhost:${PORT} (namespace=${NAMESPACE})`);
});
