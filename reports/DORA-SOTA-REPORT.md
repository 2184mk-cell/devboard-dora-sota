# DevBoard DORA + SOTA Report

## Scope

This report measures the DevBoard delivery system using Argo CD deployment telemetry, Git commit timestamps, Prometheus, and Kubernetes/GitOps health signals.

## DORA metrics

| Metric | Definition | Prometheus metric / rule |
|---|---|---|
| Deployment Frequency | Successful production deployments per day | `devboard:dora:deployment_frequency_7d` |
| Lead Time for Changes | Git commit timestamp to successful deployment | `devboard_deployment_lead_time_seconds` |
| Change Failure Rate | Failed deployment events / all deployment events | `devboard:dora:change_failure_rate_30d` |
| Failed Deployment Recovery Time | Failed deployment to next successful deployment | `devboard_deployment_recovery_seconds` |

### Event model

```text
Git commit
   |
   v
GitOps revision
   |
   v
Argo CD sync
   |
   v
Healthy + Synced
   |
   v
DORA deployment event
```

A deployment is recorded when Argo CD reports a successful operation or the application is both `Synced` and `Healthy`. Failed Argo CD operations (`Failed`/`Error`) are recorded as failures.

## SOTA engineering scorecard

SOTA here means a project-defined **State of the Application / engineering maturity score**, not an official DORA classification.

| Area | Weight | Signals |
|---|---:|---|
| Delivery performance | 30% | DORA metrics |
| Reliability | 20% | Argo CD health / SLOs |
| GitOps | 15% | Argo CD sync / drift |
| Kubernetes | 15% | workload health / resources |
| Observability | 10% | Prometheus / Grafana / alerts |
| Security | 10% | SAST / dependency / image / DAST gates |

The score should be treated as a trend and engineering-improvement indicator, not a vendor certification.

## Existing DevBoard capabilities incorporated

- GitOps deployment flow
- Argo CD sync and health telemetry
- Prometheus alerting
- OutOfSync / Degraded / Missing application monitoring
- Kubernetes workload monitoring
- CI code quality, tests, dependency scanning, Docker scanning, SonarQube and OWASP ZAP workflows

## Dashboard

Import:

- `grafana/devboard-dora-dashboard.json`
- `grafana/devboard-sota-dashboard.json`

## Operational prerequisites

1. Deploy the exporter into a namespace with network access to Argo CD.
2. Create the `dora-exporter-argocd` secret using `secret.example.yaml`.
3. Install the Prometheus Operator `ServiceMonitor` support, or adapt the scrape configuration if your Prometheus is not operator-managed.
4. Configure the Argo CD application name in the Deployment if it differs from `devboard`.
5. Keep the deployment history PVC-backed so restarts do not erase the DORA event ledger.

## Limitations

- Historical DORA values begin when the exporter starts observing deployment events; they are not reconstructed from old Argo CD history automatically.
- Lead time requires the deployed revision to be resolvable in the configured GitHub repository.
- Recovery time requires a failed event followed by a later successful deployment observed by the exporter.
- For production use, pin the exporter image by immutable SHA rather than `latest`.
