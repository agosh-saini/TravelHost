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
        return {"status": "error", "msg": "SSID required"}

    try:
        # 1. Disconnect wlan1
        run("nmcli device disconnect wlan1 || true")

        # 2. Delete any existing connections bound to wlan1
        conns = run("nmcli -t -f NAME,DEVICE connection show").splitlines()
        for c in conns:
            name, dev = c.split(":")
            if dev == "wlan1":
                run(f'nmcli connection delete "{name}"')

        # 3. Create fresh temporary connection
        if password:
            run(
                f'nmcli connection add type wifi ifname wlan1 con-name temp-wifi ssid "{ssid}" '
                f'wifi-sec.key-mgmt wpa-psk wifi-sec.psk "{password}"'
            )
        else:
            run(
                f'nmcli connection add type wifi ifname wlan1 con-name temp-wifi ssid "{ssid}"'
            )

        # 4. Bring it up
        out = run("nmcli connection up temp-wifi")

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

