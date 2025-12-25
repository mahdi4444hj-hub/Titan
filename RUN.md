# Titan – Run Modes

## Portable Mode (Windows)
- No installation
- Manual start via PowerShell
- No auto-restart

## Server Mode (Windows Service)
- Runs as a Windows Service
- Auto-restart enabled (NSSM)
- Logs enabled

## Notes
- Configuration: config.yaml
- Core entrypoint: core/api.py
- «HTTPS فعال است و از certs/ استفاده می‌کند».
