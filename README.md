# TravelHost (Raspberry Pi Zero 2 W)
A secret santa gift costing less than $30 for people who travel. A lightweight, local-first travel router built on Raspberry Pi OS using
NetworkManager and FastAPI.

This device creates a permanent Wi-Fi access point (wlan0) while allowing
dynamic upstream Wi-Fi switching (wlan1) via a local web UI.

## Features
- Permanent AP (travel-host)
- Dynamic upstream Wi-Fi switching
- Captive portal detection + login helper
- NAT + DHCP via NetworkManager
- Token-protected local web UI
- systemd auto-start

## Usage
1. Connect to Wi-Fi `travel-host`
2. Open http://<PI_IP>:8000 (PI_IP can be found by typing hostname -I in Pi terminal)
3. Select upstream Wi-Fi
4. Login to captive portal if required

## License
Licensed under the Apache License, Version 2.0 (the "License");
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

