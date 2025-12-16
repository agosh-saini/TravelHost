# Security Model

All control endpoints require a shared token.

## Changing the token

1. Edit the systemd service:
   Environment=WIFI_UI_TOKEN=your-token

2. Restart the service:
   sudo systemctl daemon-reload
   sudo systemctl restart travel-router-ui

3. Update index.html:
   const TOKEN = "your-token";

