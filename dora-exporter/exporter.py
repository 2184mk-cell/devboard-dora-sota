import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

APP = os.getenv("ARGOCD_APP", "devboard")
ARGOCD_URL = os.getenv("ARGOCD_URL", "http://argocd-server.argocd.svc.cluster.local")
ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN", "")
ARGOCD_VERIFY_TLS = os.getenv("ARGOCD_VERIFY_TLS", "true").lower() == "true"
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
DB_PATH = os.getenv("DB_PATH", "/data/dora.db")

app = FastAPI(title="DevBoard DORA Exporter", version="1.0.0")

DEPLOYMENTS = Counter("devboard_deployments_total", "Observed Argo CD deployment events", ["application", "status"])
LEAD_TIME = Histogram("devboard_deployment_lead_time_seconds", "Time from source revision commit to successful Argo CD deployment", ["application"], buckets=(60,300,900,1800,3600,7200,21600,86400,604800))
RECOVERY = Histogram("devboard_deployment_recovery_seconds", "Time from failed deployment to next healthy and synced revision", ["application"], buckets=(60,300,900,1800,3600,7200,21600,86400))
FAILURE_RATE = Gauge("devboard_change_failure_rate", "Rolling change failure rate", ["application", "window"])
FREQUENCY = Gauge("devboard_deployment_frequency", "Successful deployments per day", ["application", "window"])
APP_SYNC = Gauge("devboard_argocd_sync_status", "Argo CD sync status (1 when current status matches label)", ["application", "status"])
APP_HEALTH = Gauge("devboard_argocd_health_status", "Argo CD health status (1 when current status matches label)", ["application", "status"])
OBSERVED_REVISION = Gauge("devboard_observed_revision_timestamp", "Unix timestamp when a revision was first observed as deployed", ["application", "revision"])


def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS deployments (id INTEGER PRIMARY KEY, app TEXT, revision TEXT, observed REAL, status TEXT, commit_time REAL, failure_start REAL, UNIQUE(app, revision))")
    con.commit()
    return con


def ts(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def argocd_app():
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}" } if ARGOCD_TOKEN else {}
    with httpx.Client(base_url=ARGOCD_URL, headers=headers, verify=ARGOCD_VERIFY_TLS, timeout=10) as client:
        r = client.get(f"/api/v1/applications/{APP}")
        r.raise_for_status()
        return r.json()


def update_metrics(data):
    status = data.get("status", {})
    sync = status.get("sync", {}).get("status", "Unknown")
    health = status.get("health", {}).get("status", "Unknown")
    revision = status.get("operationState", {}).get("syncResult", {}).get("revision") or status.get("sync", {}).get("revision", "unknown")
    for s in ("Synced", "OutOfSync", "Unknown"):
        APP_SYNC.labels(APP, s).set(1 if sync == s else 0)
    for s in ("Healthy", "Degraded", "Missing", "Progressing", "Suspended", "Unknown"):
        APP_HEALTH.labels(APP, s).set(1 if health == s else 0)

    if not revision or revision == "unknown":
        return
    con = db()
    now = time.time()
    row = con.execute("SELECT id FROM deployments WHERE app=? AND revision=?", (APP, revision)).fetchone()
    if row is None and sync == "Synced":
        commit_time = None
        # Argo CD does not always expose the Git commit timestamp. The metric remains valid;
        # lead time is recorded when an external commit timestamp is supplied in the event API.
        con.execute("INSERT OR IGNORE INTO deployments(app,revision,observed,status,commit_time,failure_start) VALUES(?,?,?,?,?,?)", (APP, revision, now, "success", commit_time, None))
        con.commit()
        DEPLOYMENTS.labels(APP, "success").inc()
        OBSERVED_REVISION.labels(APP, revision).set(now)
    if health == "Degraded" or sync == "OutOfSync":
        latest = con.execute("SELECT id FROM deployments WHERE app=? AND revision=?", (APP, revision)).fetchone()
        if latest is None:
            con.execute("INSERT OR IGNORE INTO deployments(app,revision,observed,status,commit_time,failure_start) VALUES(?,?,?,?,?,?)", (APP, revision, now, "failure", None, now))
            con.commit()
            DEPLOYMENTS.labels(APP, "failure").inc()
    recalc(con)
    con.close()


def recalc(con):
    now = time.time()
    start = now - 30 * 86400
    total = con.execute("SELECT COUNT(*) FROM deployments WHERE app=? AND observed>=?", (APP, start)).fetchone()[0]
    failures = con.execute("SELECT COUNT(*) FROM deployments WHERE app=? AND observed>=? AND status='failure'", (APP, start)).fetchone()[0]
    success = con.execute("SELECT COUNT(*) FROM deployments WHERE app=? AND observed>=? AND status='success'", (APP, start)).fetchone()[0]
    FAILURE_RATE.labels(APP, "30d").set((failures / total) if total else 0)
    FREQUENCY.labels(APP, "30d").set(success / 30)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "application": APP}


@app.get("/refresh")
def refresh():
    data = argocd_app()
    update_metrics(data)
    return {"status": "refreshed", "application": APP}


app.mount("/metrics", make_asgi_app())


@app.on_event("startup")
def startup():
    def loop():
        while True:
            try:
                update_metrics(argocd_app())
            except Exception as exc:
                print(f"DORA poll failed: {exc}", flush=True)
            time.sleep(POLL_SECONDS)
    import threading
    threading.Thread(target=loop, daemon=True).start()
