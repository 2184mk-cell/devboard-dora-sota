# DevBoard DORA + SOTA

This repository now contains a GitOps-friendly DORA observability implementation for DevBoard.

## Components

- `dora-exporter/` — FastAPI Prometheus exporter that polls Argo CD and resolves deployed revisions against GitHub.
- `k8s/dora-exporter/` — Kubernetes Deployment, Service, ServiceMonitor, RBAC and persistent event ledger.
- `prometheus/` — DORA recording rules and alerts.
- `grafana/` — DORA and engineering SOTA dashboards.
- `reports/` — metric definitions and operational guidance.

## Quick start

```bash
kubectl apply -k k8s/dora-exporter
kubectl -n dora-observability create secret generic dora-exporter-argocd \
  --from-literal=token='<ARGOCD_API_TOKEN>'

kubectl apply -f prometheus/dora-recording-rules.yaml
kubectl apply -f prometheus/dora-alerts.yaml
```

For an Argo CD installation using a self-signed certificate, configure the exporter TLS behavior before production use. The exporter intentionally keeps credentials in Kubernetes Secrets rather than Git.

## Metrics

```text
devboard_deployments_total
devboard_deployment_lead_time_seconds
devboard_deployment_recovery_seconds
devboard_change_failure_rate
devboard_deployment_frequency
devboard_argocd_sync_status
devboard_argocd_health_status
devboard_observed_revision_timestamp
```

Do not interpret the project-defined SOTA score as an official industry benchmark. It is a transparent engineering scorecard for this portfolio application.
