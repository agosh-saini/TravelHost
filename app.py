from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import urllib.request

app = FastAPI()

def run(cmd):
    if cmd.strip().startswith("nmcli "):
        cmd = "sudo " + cmd
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

TOKEN = os.getenv("WIFI_UI_TOKEN")

def require_token(request: Request):
    if not TOKEN:
        return
    if request.query_params.get("token") != TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/api/networks")
def networks(request: Request):
    require_token(request)
    out = run("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY device wifi list ifname wlan1")
    results = []
    for line in out.strip().split("\\n"):
        if not line:
            continue
        in_use, ssid, signal, security = line.split(":")[:4]
        results.append({
            "connected": in_use == "*",
            "ssid": ssid,
            "signal": int(signal) if signal.isdigit() else 0,
            "security": security
        })
    return results

@app.get("/api/status")
def status(request: Request):
    require_token(request)
    try:
        ip = run("nmcli -t -f IP4.ADDRESS device show wlan1 | head -n1").strip()
        return {"ip": ip or None}
    except:
        return {"ip": None}

@app.get("/api/captive")
def captive(request: Request):
    require_token(request)
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(
                "http://connectivitycheck.gstatic.com/generate_204",
                headers={"User-Agent": "Mozilla/5.0"}
            ),
            timeout=5
        )
        return {"captive": r.status != 204}
    except:
        return {"captive": True}

@app.post("/api/connect")
def connect(request: Request, ssid: str = Query(...), password: str = Query("")):
    require_token(request)
    run("nmcli device disconnect wlan1 || true")
    conns = run("nmcli -t -f NAME,DEVICE connection show").splitlines()
    for c in conns:
        name, dev = c.split(":")
        if dev == "wlan1":
            run(f'nmcli connection delete "{name}"')
    if password:
        run(f'nmcli connection add type wifi ifname wlan1 con-name temp-wifi ssid "{ssid}" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "{password}"')
    else:
        run(f'nmcli connection add type wifi ifname wlan1 con-name temp-wifi ssid "{ssid}"')
    return {"status": "ok", "output": run("nmcli connection up temp-wifi")}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
