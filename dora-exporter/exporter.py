import os
import sqlite3
import threading
import time
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

APP = os.getenv("ARGOCD_APP", "devboard")
ARGOCD_URL = os.getenv("ARGOCD_URL", "http://argocd-server.argocd.svc.cluster.local")
ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "30"))
DB_PATH = os.getenv("DB_PATH", "/data/dora.db")

app = FastAPI(title="DevBoard DORA Exporter", version="1.1.0")
DEPLOYMENTS = Counter("devboard_deployments_total", "Observed deployment events", ["application", "status"])
LEAD_TIME = Histogram("devboard_deployment_lead_time_seconds", "Git commit to successful deployment", ["application"], buckets=(60,300,900,1800,3600,7200,21600,86400,604800))
RECOVERY = Histogram("devboard_deployment_recovery_seconds", "Failed deployment to next successful deployment", ["application"], buckets=(60,300,900,1800,3600,7200,21600,86400))
FAILURE_RATE = Gauge("devboard_change_failure_rate", "Rolling change failure rate", ["application", "window"])
FREQUENCY = Gauge("devboard_deployment_frequency", "Successful deployments per day", ["application", "window"])
APP_SYNC = Gauge("devboard_argocd_sync_status", "Argo CD sync status", ["application", "status"])
APP_HEALTH = Gauge("devboard_argocd_health_status", "Argo CD health status", ["application", "status"])
OBSERVED_REVISION = Gauge("devboard_observed_revision_timestamp", "Deployment observation timestamp", ["application", "revision"])


def db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("CREATE TABLE IF NOT EXISTS deployments (id INTEGER PRIMARY KEY, app TEXT, revision TEXT, observed REAL, status TEXT, commit_time REAL, failure_start REAL, UNIQUE(app, revision))")
    con.commit()
    return con


def parse_ts(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def argocd_app():
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"} if ARGOCD_TOKEN else {}
    with httpx.Client(base_url=ARGOCD_URL, headers=headers, timeout=10) as client:
        r = client.get(f"/api/v1/applications/{APP}")
        r.raise_for_status()
        return r.json()


def github_commit_time(revision: str) -> Optional[float]:
    if not GITHUB_REPO or len(revision) < 7:
        return None
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        with httpx.Client(headers=headers, timeout=10) as client:
            r = client.get(f"https://api.github.com/repos/{GITHUB_REPO}/commits/{revision}")
            if r.status_code != 200:
                return None
            data = r.json()
            date = data.get("commit", {}).get("committer", {}).get("date") or data.get("commit", {}).get("author", {}).get("date")
            return parse_ts(date)
    except Exception:
        return None


def update_metrics(data):
    status = data.get("status", {})
    sync = status.get("sync", {}).get("status", "Unknown")
    health = status.get("health", {}).get("status", "Unknown")
    operation = status.get("operationState") or {}
    phase = operation.get("phase", "")
    revision = operation.get("syncResult", {}).get("revision") or status.get("sync", {}).get("revision", "")

    for s in ("Synced", "OutOfSync", "Unknown"):
        APP_SYNC.labels(APP, s).set(1 if sync == s else 0)
    for s in ("Healthy", "Degraded", "Missing", "Progressing", "Suspended", "Unknown"):
        APP_HEALTH.labels(APP, s).set(1 if health == s else 0)
    if not revision:
        return

    con = db()
    now = time.time()
    row = con.execute("SELECT id,status,commit_time,failure_start FROM deployments WHERE app=? AND revision=?", (APP, revision)).fetchone()
    deployment_failed = phase in ("Failed", "Error")
    deployment_succeeded = phase == "Succeeded" or (sync == "Synced" and health == "Healthy")

    if row is None and (deployment_failed or deployment_succeeded):
        commit_time = github_commit_time(revision) if deployment_succeeded else None
        failure_start = now if deployment_failed else None
        status_value = "failure" if deployment_failed else "success"
        con.execute("INSERT OR IGNORE INTO deployments(app,revision,observed,status,commit_time,failure_start) VALUES(?,?,?,?,?,?)", (APP, revision, now, status_value, commit_time, failure_start))
        con.commit()
        DEPLOYMENTS.labels(APP, status_value).inc()
        OBSERVED_REVISION.labels(APP, revision).set(now)
        if deployment_succeeded and commit_time:
            LEAD_TIME.labels(APP).observe(max(0, now - commit_time))
            failed = con.execute("SELECT id, failure_start FROM deployments WHERE app=? AND status='failure' AND failure_start IS NOT NULL ORDER BY failure_start DESC LIMIT 1", (APP,)).fetchone()
            if failed and failed[1] < now:
                RECOVERY.labels(APP).observe(now - failed[1])
                con.execute("UPDATE deployments SET failure_start=NULL WHERE id=?", (failed[0],))
                con.commit()

    recalc(con)
    con.close()


def recalc(con):
    start = time.time() - 30 * 86400
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
    update_metrics(argocd_app())
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
    threading.Thread(target=loop, daemon=True).start()
