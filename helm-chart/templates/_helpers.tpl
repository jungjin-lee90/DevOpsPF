{{/* Generate a name for the deployment */}}
{{- define "streamlit-app.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Generate a full name */}}
{{- define "streamlit-app.fullname" -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
