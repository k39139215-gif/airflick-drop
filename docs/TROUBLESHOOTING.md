# AirFlick Drop Troubleshooting Guide

## 1. White Screen in Mobile Browser
- **Cause**: Using old LAN IP bookmark after router DHCP renewal or switching networks (e.g. from Wi-Fi to phone hotspot).
- **Solution**: Switch to **Cloudflare HTTPS (Universal)** mode in the desktop window. Cloudflare HTTPS URLs remain stable and reachable across Wi-Fi, Hotspot, and mobile cellular data without breaking.

## 2. Port 5050 In-Use Error (`WinError 10048`)
- **Cause**: Background server instance already running.
- **Solution**: AirFlick features auto-attachment. The companion GUI detects running instances on port 5050 and attaches without re-binding.

## 3. Router AP Isolation
- **Cause**: Public networks (college, hotel, corporate) block direct peer-to-peer LAN packets between devices.
- **Solution**: Use Cloudflare HTTPS mode. Traffic routes securely via Cloudflare edge servers, completely bypassing local AP isolation.
