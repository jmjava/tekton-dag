# tekton-dag + ArgoCD Architecture Guide

## Purpose

This document explains how the `tekton-dag` project integrates with Tekton Pipelines and ArgoCD.

The goal is to provide context so future development (especially using Cursor AI) understands:

- What `tekton-dag` is responsible for
- What Tekton is responsible for
- What ArgoCD is responsible for
- How builds/tests are executed
- What resources are managed via GitOps vs runtime

---

# System Overview

The system consists of three main layers:

Git Events / CLI  
↓  
tekton-dag (orchestrator)  
↓  
Tekton Pipelines (execution engine)  
↓  
Kubernetes Pods (build + test)

Infrastructure is managed by:

ArgoCD

- installs Tekton
- installs Tekton Tasks
- installs Tekton Pipelines
- installs tekton-dag service

---

# Responsibilities

## ArgoCD

ArgoCD manages desired cluster state.

It installs and maintains:

- Tekton CRDs
- Tekton controllers
- Tekton Tasks
- Tekton Pipelines
- Tekton Triggers
- RBAC
- tekton-dag deployment

ArgoCD does NOT run pipelines.

ArgoCD only reconciles YAML resources.

### Managed Resources

- Task
- Pipeline
- TriggerTemplate
- TriggerBinding
- EventListener
- ServiceAccount
- Role / RoleBinding
- Deployment (tekton-dag)

### Not Managed by ArgoCD

These are runtime resources:

- PipelineRun
- TaskRun
- Pod

These are created dynamically by `tekton-dag` or Tekton Triggers.

---

# Tekton

Tekton is the pipeline execution engine.

Conceptual model:

Step → container command  
Task → group of steps  
Pipeline → DAG of tasks  
PipelineRun → execution instance

Example pipeline graph:

clone  
↓  
build  
↓  
unit-tests  
├── integration-tests  
└── security-scan  
 ↓  
 deploy-preview

Each task runs as a Kubernetes Pod.

---

# tekton-dag

`tekton-dag` is a pipeline orchestration tool built on top of Tekton.

Responsibilities:

- Define high-level pipeline workflows
- Generate or trigger Tekton PipelineRuns
- Coordinate multi-platform builds
- Run test DAGs
- Collect test results
- Store pipeline output in database or storage

Conceptually:

tekton-dag

- receives PR event
- determines pipeline DAG
- creates PipelineRun

↓

Tekton

↓

Pods execute tasks

---

# Example Pipeline Flow

## 1 PR Opened

GitHub or Gitea PR triggers:

Webhook  
↓  
tekton-dag

---

## 2 tekton-dag Generates PipelineRun

Example resource created dynamically:

apiVersion: tekton.dev/v1  
kind: PipelineRun  
metadata:  
 generateName: pr-test-  
spec:  
 pipelineRef:  
 name: pr-pipeline  
 params:  
 - name: repo  
 value: https://github.com/org/app

---

## 3 Tekton Executes Pipeline

Tekton schedules tasks:

clone  
↓  
build  
↓  
unit-tests  
↓  
integration-tests  
↘ playwright  
 ↓  
publish-results

Each task runs in a pod.

---

# GitOps Layout

Recommended repo structure:

repo  
├── argocd  
│ └── applications  
│  
├── tekton  
│ ├── tasks  
│ │ ├── build.yaml  
│ │ ├── unit-test.yaml  
│ │ └── playwright.yaml  
│ │  
│ └── pipelines  
│ └── pr-pipeline.yaml  
│  
└── tekton-dag  
 └── deployment.yaml

ArgoCD points at this repository.

---

# ArgoCD Application Example

apiVersion: argoproj.io/v1alpha1  
kind: Application  
metadata:  
 name: tekton-dag  
 namespace: argocd  
spec:  
 project: default  
 source:  
 repoURL: https://github.com/jmjava/tekton-dag  
 targetRevision: main  
 path: k8s  
 destination:  
 server: https://kubernetes.default.svc  
 namespace: tekton-dag  
 syncPolicy:  
 automated:  
 prune: true  
 selfHeal: true

---

# Sync Ordering

Tekton CRDs must exist before pipelines are applied.

Recommended sync order:

Wave -1  
Tekton CRDs

Wave 0  
RBAC  
ServiceAccounts

Wave 1  
Tasks

Wave 2  
Pipelines

Wave 3  
Triggers  
EventListeners

Wave 4  
tekton-dag deployment

Annotation example:

argocd.argoproj.io/sync-wave: "2"

---

# Result Storage

Pipeline outputs should be exported.

Typical storage options:

- S3
- Database
- Object storage
- Logs
- Artifacts

Example artifact structure:

test-results/

- junit.xml
- playwright-report.html
- coverage.json

These can be visualized via:

- Retool
- Grafana
- Custom dashboard

---

# Design Principles

## Pipelines are declarative

Tekton YAML defines execution graph.

## PipelineRuns are ephemeral

They should not be stored in Git.

## GitOps manages infrastructure

ArgoCD installs pipelines but does not execute them.

## tekton-dag orchestrates execution

It decides when and how pipelines run.

---

# Potential Improvements

Future work may include:

### Dynamic Pipeline Generation

Instead of static pipelines:

tekton-dag → generate pipeline spec

### Test Matrix Execution

Example fan-out:

- java
- python
- node

### Parallel DAG Execution

Tekton supports:

- fan-out
- fan-in
- conditional execution

### Result Aggregation

Centralized system for:

- test results
- build artifacts
- coverage
- logs

---

# Future Enhancements

## Pipeline Metadata Database

Store:

- pipeline_run_id
- status
- duration
- artifacts
- logs

## Web UI

Display:

- pipeline DAG
- task logs
- test reports

## GitOps Pipeline Versioning

Pipeline definitions tied to git SHA.

---

# Summary

System architecture:

ArgoCD → installs infrastructure  
tekton-dag → orchestrates workflows  
Tekton → executes DAG pipelines  
Kubernetes → runs containers

This separation provides:

- reproducible infrastructure
- scalable pipeline execution
- flexible orchestration logic
- GitOps compliance
