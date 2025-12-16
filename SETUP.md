Raspberry Pi Travel Hotspot Setup

This document describes how to configure a Raspberry Pi Zero 2 W to act as a
travel hotspot, using:

- USB Wi-Fi dongle (wlan1) -> upstream internet (client mode)
- On-chip Wi-Fi (wlan0) -> permanent hotspot (AP mode)

The setup uses NetworkManager only (no hostapd, no raspi-config).

------------------------------------------------------------

FINAL BEHAVIOR

On every boot:

- wlan1 automatically connects to an upstream Wi-Fi network
- wlan0 broadcasts a hotspot:
  - SSID: travel-host
  - Password: travel-host
- Devices connected to the hotspot have internet access via NAT

------------------------------------------------------------

REQUIREMENTS

- Raspberry Pi OS Bookworm
- NetworkManager enabled (default on Bookworm)
- USB Wi-Fi dongle that supports client mode (TP-LINK TL-WN725N USB Wi-Fi dongle)
- On-chip Wi-Fi (Pi Zero 2 W) supports AP mode

------------------------------------------------------------

VERIFY INTERFACES

Run:
nmcli device

If wlan1 does not appear, install firmware:

sudo apt update
sudo apt install firmware-realtek
sudo reboot

------------------------------------------------------------

STEP 1 — CONNECT USB WI-FI DONGLE TO UPSTREAM NETWORK

Scan using the dongle:

nmcli device wifi list ifname wlan1

Connect (explicit WPA-PSK avoids key-mgmt errors):

sudo nmcli device wifi connect "UPSTREAM_SSID" \\
  ifname wlan1 \\
  wifi-sec.key-mgmt wpa-psk \\
  password "UPSTREAM_PASSWORD"

Make the connection persistent:

nmcli -g NAME,DEVICE connection show --active
sudo nmcli connection modify "<CONNECTION_NAME_FOR_WLAN1>" connection.autoconnect yes

------------------------------------------------------------

STEP 2 — CREATE PERMANENT HOTSPOT ON ON-CHIP WI-FI

Create the hotspot:

sudo nmcli device wifi hotspot ifname wlan0 ssid travel-host password travel-host

Make it persistent and locked to wlan0:

sudo nmcli connection modify Hotspot connection.autoconnect yes
sudo nmcli connection modify Hotspot connection.interface-name wlan0
sudo nmcli connection modify Hotspot 802-11-wireless.mode ap
sudo nmcli connection modify Hotspot ipv4.method shared
sudo nmcli connection modify Hotspot ipv6.method ignore

(Optional) Set autoconnect priority:

sudo nmcli connection modify Hotspot connection.autoconnect-priority 50

------------------------------------------------------------

STEP 3 — REBOOT AND VERIFY

sudo reboot

After reboot:
nmcli device

Expected:
wlan1  wifi  connected  <upstream-wifi>
wlan0  wifi  connected  Hotspot

From another device:
- Connect to travel-host
- Password: travel-host
- Internet access should work

------------------------------------------------------------

CHANGE HOTSPOT NAME OR PASSWORD

The hotspot is managed by NetworkManager using the connection named Hotspot.

Change password only:

sudo nmcli connection modify Hotspot 802-11-wireless-security.psk "NEW_PASSWORD"
sudo nmcli connection down Hotspot
sudo nmcli connection up Hotspot

Password must be at least 8 characters.

Change SSID only:

sudo nmcli connection modify Hotspot 802-11-wireless.ssid "NEW_SSID"
sudo nmcli connection down Hotspot
sudo nmcli connection up Hotspot

Change both SSID and password:

sudo nmcli connection modify Hotspot 802-11-wireless.ssid "NEW_SSID"
sudo nmcli connection modify Hotspot 802-11-wireless-security.psk "NEW_PASSWORD"
sudo nmcli connection down Hotspot
sudo nmcli connection up Hotspot

Verify current hotspot settings:

nmcli connection show Hotspot | grep -E "ssid|psk"

------------------------------------------------------------

NOTES

- p2p-dev-wlan0 is normal (Wi-Fi Direct); ignore it
- USB dongle does not need AP support
- NAT and DHCP are handled automatically by NetworkManager
- No additional drivers or services required

------------------------------------------------------------

ARCHITECTURE SUMMARY

Internet
   |
wlan1 (USB dongle, client)
   |
NAT
   |
wlan0 (on-chip Wi-Fi, hotspot)
