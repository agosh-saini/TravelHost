from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import urllib.request

app = FastAPI()

# ------------------------
# Helper
# ------------------------
def run(cmd):
    if cmd.strip().startswith("nmcli "):
        cmd = "sudo " + cmd
    return subprocess.check_output(
        cmd, shell=True, text=True, stderr=subprocess.STDOUT
    )

TOKEN = os.getenv("WIFI_UI_TOKEN")

def require_token(request: Request):
    if not TOKEN:
        return
    token = request.query_params.get("token")
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

# ------------------------
# API: Scan networks
# ------------------------
@app.get("/api/networks")
def networks(request: Request):
    require_token(request)
    out = run("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY device wifi list ifname wlan1")
    results = []

    for line in out.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 4:
            continue

        in_use, ssid, signal, security = parts[:4]
        results.append({
            "connected": in_use == "*",
            "ssid": ssid,
            "signal": int(signal) if signal.isdigit() else 0,
            "security": security
        })

    return results

# ------------------------
# API: Connection status
# ------------------------
@app.get("/api/status")
def status(request: Request):
    require_token(request)
    try:
        state = run("nmcli -t -f DEVICE,STATE,CONNECTION device show wlan1").strip()
        ip = run("nmcli -t -f IP4.ADDRESS device show wlan1 | head -n1").strip()
        return {
            "device": "wlan1",
            "state": state,
            "ip": ip if ip else None
        }
    except:
        return {
            "device": "wlan1",
            "state": "disconnected",
            "ip": None
        }

# ------------------------
# API: Connect (travel-router safe)
# ------------------------
@app.post("/api/connect")
def connect(
    request: Request,
    ssid: str = Query(...),
    password: str = Query("")
):
    require_token(request)

    if not ssid:
        raise HTTPException(status_code=400, detail="SSID required")

    try:
        # 0. Ensure wlan1 is managed
        run("nmcli device set wlan1 managed yes")

        # 1. Hard disconnect
        run("nmcli device disconnect wlan1 || true")

        # 2. Remove stale temp connections (defensive)
        conns = run("nmcli -t -f NAME,DEVICE connection show").splitlines()
        for c in conns:
            name, dev = c.split(":")
            if dev == "wlan1" or name == "temp-wifi":
                run(f'nmcli connection delete "{name}"')

        # 3. Connect NON-INTERACTIVELY (KEY FIX)
        if password:
            out = run(
                f'nmcli device wifi connect "{ssid}" '
                f'password "{password}" ifname wlan1'
            )
        else:
            out = run(
                f'nmcli device wifi connect "{ssid}" ifname wlan1'
            )

        return {
            "status": "ok",
            "output": out
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "output": e.output
        }


# ------------------------
# Captive Portal
# ------------------------
@app.get("/api/captive")
def captive(request: Request):
    require_token(request)

    TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"

    try:
        req = urllib.request.Request(
            TEST_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            # If we get 204, we have real internet
            if r.status == 204:
                return {"captive": False}

        # Any other status = captive portal
        return {"captive": True}

    except Exception:
        # DNS hijack, redirect, timeout, etc.
        return {"captive": True}


# ------------------------
# Static UI
# ------------------------
app.mount("/", StaticFiles(directory=".", html=True), name="static")

