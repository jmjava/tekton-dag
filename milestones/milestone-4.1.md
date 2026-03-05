# Milestone 4.1: Extract standalone, reusable baggage middleware libraries

> **Active milestone.** Follows [milestone 4](milestone-4.md) section 1 (baggage middleware). Other active: [milestone-2.1](milestone-2.1.md), [milestone-4](milestone-4.md), [milestone-5](milestone-5.md).

## Current state

Milestone 4 implemented role-aware baggage middleware **directly inside each app repo**. The code works and is tested, but it is embedded — another Spring Boot app, another Flask app, etc. would need to copy-paste or fork the code. The middleware is not yet consumable as a dependency.

| App repo | Middleware location | Tests |
|---|---|---|
| `tekton-dag-spring-boot` | `com.example.dag.baggage.*` | 22 (JUnit 5) |
| `tekton-dag-spring-legacy` | `com.example.dag.baggage.*` | 13 (JUnit 5) |
| `tekton-dag-flask` | `baggage.py` (root module) | 18 (pytest) |
| `tekton-dag-php` | `src/Baggage/*` | 19 (PHPUnit) |
| `tekton-dag-vue-fe` | `src/baggage.js` | 15 (vitest) |

## Goal

Extract each framework's middleware into a **standalone, publishable library** so any application on that framework can add baggage propagation by including a single dependency. The app repos then consume these libraries instead of containing the code directly.

## Scope

### 1. One library repo (or module) per framework

| Library | Package type | Source |
|---|---|---|
| `baggage-spring-boot-starter` | Maven artifact (separate module or repo) | Extract from `tekton-dag-spring-boot` `com.example.dag.baggage` |
| `baggage-servlet-filter` | Maven artifact | Extract from `tekton-dag-spring-legacy` `com.example.dag.baggage` |
| `@tekton-dag/baggage` | npm package | Extract from `tekton-dag-vue-fe` `src/baggage.js` |
| `tekton-dag-baggage` | pip package (PyPI or local) | Extract from `tekton-dag-flask` `baggage.py` |
| `tekton-dag/baggage-middleware` | Composer package (Packagist or local) | Extract from `tekton-dag-php` `src/Baggage/` |

### 2. Per-library deliverables

For each library:

- **Dedicated repo or module** with its own build file (`pom.xml`, `package.json`, `setup.py`/`pyproject.toml`, `composer.json`).
- **Moved source code** from the app repo into the library, with proper namespacing (e.g. `com.tektondag.baggage` instead of `com.example.dag.baggage`).
- **Moved tests** from the app repo into the library's own test suite.
- **README** covering installation, configuration (role, header name, baggage key), production-safety setup, and usage examples.
- **Publishing mechanism**: local install / registry publish so the app repos can declare a dependency and pull the library.

### 3. App repos become consumers

After extraction, each app repo:

- **Removes** the embedded middleware code.
- **Adds** the library as a dependency (`pom.xml`, `requirements.txt`, `composer.json`, `package.json`).
- **Wires** the library via configuration only (Spring Boot auto-configuration, Flask `init_app`, PHP middleware registration, Vite plugin/interceptor setup).
- **Retains** the basic app smoke test but delegates middleware tests to the library.

### 4. Build-time exclusion (production safety layer 1)

With standalone libraries, the build-time exclusion guard becomes straightforward:

- **Spring Boot / Legacy**: library added under a Maven profile (`dev` / `baggage`). Production build skips the profile — artifact absent from WAR/JAR.
- **Node**: library in `devDependencies`. Production `npm ci --omit=dev` excludes it.
- **Flask**: library as an extras group (`pip install myapp[baggage]`). Production Dockerfile installs without the extra.
- **PHP**: `composer require-dev`. Production `composer install --no-dev` excludes it.

### 5. Versioning and publishing strategy

- Each library gets semantic versioning (start at `1.0.0`).
- **Maven**: publish to a local Maven repo, GitHub Packages, or a private Nexus/Artifactory.
- **npm**: publish to a private registry or use `npm link` / workspace references.
- **pip**: publish to a private PyPI or install from Git URL.
- **Composer**: publish to Packagist (private) or use a path/Git repository.
- Document the publishing and consumption workflow for each package type.

## Outcomes

- **Five standalone library packages**, each in its own repo or module with build file, source, tests, and README.
- **App repos** consume the libraries as dependencies — no embedded middleware code.
- **Build-time exclusion** verified: production builds exclude the library artifact entirely.
- **Publishing workflow** documented for each package type.

## Notes

- The W3C Baggage codec, role enum, context holder, and production guard patterns are identical across frameworks. Consider whether a shared spec / test contract makes sense to ensure consistency as libraries evolve independently.
- The Spring Boot library should use `@AutoConfiguration` + `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` for proper starter conventions (vs. the current `@Configuration` that relies on component scanning within the app).
- Header names and baggage keys remain configurable per library (default: `x-dev-session` / `dev-session`).
