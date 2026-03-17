{{/*
Chart name
*/}}
{{- define "tekton-dag.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Fully qualified app name (team-scoped)
*/}}
{{- define "tekton-dag.fullname" -}}
{{- printf "%s-%s" .Values.teamName (include "tekton-dag.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "tekton-dag.labels" -}}
app.kubernetes.io/part-of: tekton-job-standardization
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
tekton-dag/team: {{ .Values.teamName }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "tekton-dag.serviceAccountName" -}}
{{- .Values.rbac.serviceAccountName }}
{{- end }}
