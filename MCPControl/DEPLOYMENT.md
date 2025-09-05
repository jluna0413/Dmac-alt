# MCPControl Deployment

This guide covers running MCPControl as a Windows service (recommended for local/edge environments). Linux users can adapt to systemd similarly.

## Prerequisites
- Node.js 18+ installed and in PATH.
- Built artifacts present (run `npm run build`).
- [NSSM](https://nssm.cc/download) installed and available in PATH.

## Windows service (NSSM)

Install and start the service:

```powershell
# From the MCPControl root
npm run build
./scripts/install-windows-service.ps1 -ServiceName MCPControl -Env production
```

Uninstall the service:

```powershell
./scripts/uninstall-windows-service.ps1 -ServiceName MCPControl
```

Notes:
- Logs are written to `logs/MCPControl.out.log` and `logs/MCPControl.err.log`.
- Service runs the built `dist/index.js`. Rebuild and restart the service to deploy updates.
- Adjust service name with `-ServiceName` to run multiple instances.
- To require an API key for `/api/*`, set environment variable `MCPCONTROL_API_KEY` on the service.

## Linux (systemd) example

Create `/etc/systemd/system/mcpcontrol.service`:

```
[Unit]
Description=MCPControl Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mcpcontrol
ExecStart=/usr/bin/node /opt/mcpcontrol/dist/index.js
Restart=always
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcpcontrol
sudo systemctl start mcpcontrol
sudo journalctl -u mcpcontrol -f
```

## Health and readiness
- Ready: `GET http://127.0.0.1:8052/ready`
- Health: `GET http://127.0.0.1:8052/health`

## Upgrades
- Stop service
- Pull changes
- `npm ci && npm run build`
- Start service

## Troubleshooting
- If Archon isn’t running, discovery will warn but MCPControl remains operational.
- Check logs under `logs/` and Windows Event Viewer for service issues.
- Ensure firewall allows inbound on the configured port (default 8052).