# Milestone 4.1 — Library publishing and consumption strategy

This document covers how each standalone baggage library is published, consumed, and excluded from production builds.

## Library inventory

| Library | Package system | Location |
|---|---|---|
| `baggage-spring-boot-starter` | Maven | `libs/baggage-spring-boot-starter/` |
| `baggage-servlet-filter` | Maven | `libs/baggage-servlet-filter/` |
| `tekton-dag-baggage` | pip (Python) | `libs/baggage-python/` |
| `@tekton-dag/baggage` | npm (Node.js) | `libs/baggage-node/` |
| `tekton-dag/baggage-middleware` | Composer (PHP) | `libs/baggage-php/` |

All libraries live inside the `tekton-dag` platform repository under `libs/`. This mono-repo-style layout simplifies cross-library version tracking and CI validation. Each library has its own build file and can be published independently.

## Publishing mechanisms

### Maven (Spring Boot + Spring Legacy)

**Local install (current):**

```bash
cd libs/baggage-spring-boot-starter && mvn install -DskipTests
cd libs/baggage-servlet-filter && mvn install -DskipTests
```

App repos then resolve the artifact from the local `~/.m2/repository`.

**Registry (future):**

- **GitHub Packages**: add a `<distributionManagement>` block pointing to `https://maven.pkg.github.com/OWNER/REPO` and configure a `~/.m2/settings.xml` with a GitHub token.
- **Nexus / Artifactory**: same pattern, different URL.
- **Tekton CI**: a `publish-maven` task can run `mvn deploy` after tests pass.

### npm (Vue / Node)

**Local link (current):**

```json
"devDependencies": {
  "@tekton-dag/baggage": "file:../tekton-dag/libs/baggage-node"
}
```

`npm install` resolves the local path as a symlink.

**Registry (future):**

- `npm publish --registry https://npm.pkg.github.com` for GitHub Packages.
- Or publish to a private Verdaccio / Artifactory npm registry.
- Scope `@tekton-dag` should be configured in `.npmrc`.

### pip (Flask / Python)

**Local install (current):**

```
tekton-dag-baggage @ file:///path/to/tekton-dag/libs/baggage-python
```

Or install directly: `pip install ./libs/baggage-python`.

**Registry (future):**

- `pip install tekton-dag-baggage` from a private PyPI (e.g. AWS CodeArtifact, GitHub Packages, devpi).
- Or install from a Git URL: `pip install git+https://github.com/OWNER/tekton-dag.git#subdirectory=libs/baggage-python`.

### Composer (PHP)

**Path repository (current):**

```json
"repositories": [
  { "type": "path", "url": "../tekton-dag/libs/baggage-php" }
],
"require-dev": {
  "tekton-dag/baggage-middleware": "1.0.0"
}
```

Composer symlinks from the local path.

**Registry (future):**

- Publish to Packagist (public) or Private Packagist.
- Or use a Satis static repository.
- Or reference a VCS repository: `{ "type": "vcs", "url": "https://github.com/OWNER/tekton-dag" }`.

## Build-time exclusion

Each framework has a standard mechanism to ensure baggage middleware is absent from production artifacts.

| Framework | Mechanism | Production command |
|---|---|---|
| Spring Boot | Maven profile `baggage` | `mvn package` (omit `-Pbaggage`) |
| Spring Legacy | Maven profile `baggage` | `mvn package` (omit `-Pbaggage`) |
| Flask / Python | `requirements-dev.txt` | `pip install -r requirements.txt` (not `-dev`) |
| Vue / Node | `devDependencies` | `npm ci --omit=dev` |
| PHP | `require-dev` | `composer install --no-dev` |

**Dev / test builds** include the library:

```bash
# Java
mvn package -Pbaggage

# Python
pip install -r requirements-dev.txt

# Node
npm ci

# PHP
composer install
```

## Runtime safety (layer 2)

Even when the library is present on the classpath / in `node_modules`, it remains inert unless explicitly enabled:

| Framework | Guard |
|---|---|
| Spring Boot | `@ConditionalOnProperty(name = "baggage.enabled", havingValue = "true")` |
| Spring Legacy | `web.xml` filter registration (only added in dev configs) |
| Flask | `BAGGAGE_ENABLED` env var checked in `init_app()` |
| Node / Vue | `import.meta.env.VITE_BAGGAGE_ENABLED === 'true'` (tree-shaken in prod) |
| PHP | `BAGGAGE_ENABLED` env var checked in middleware constructor |

## Versioning

All libraries start at `1.0.0`. Version bumps follow semver:

- **Patch** (1.0.x): bug fixes, no API change.
- **Minor** (1.x.0): new features (e.g. new header support), backward compatible.
- **Major** (x.0.0): breaking changes (e.g. renamed config keys).

Library versions are independent of each other and of app repo versions.

## CI integration

The Tekton pipeline can validate libraries before app-repo PRs merge:

1. **`build-library` task**: runs `mvn test` / `npm test` / `pytest` / `phpunit` for the changed library.
2. **`build-app` task**: builds the consuming app with the library included (profile/dev-deps).
3. **`integration-test` task**: deploys a test stack and runs e2e header-propagation checks.

This is already supported by the test stacks defined in `stacks/*.yaml`.
