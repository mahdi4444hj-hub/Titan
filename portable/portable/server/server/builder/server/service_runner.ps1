# TitanFusion Server Runner
$ErrorActionPreference = "SilentlyContinue"

$basePath = Split-Path -Parent $MyInvocation.MyCommand.Path
$config = Join-Path $basePath "..\config.yaml"

while ($true) {
    Start-Process -FilePath "TitanFusionCore.exe" `
        -ArgumentList "--server --config `"$config`"" `
        -WindowStyle Hidden
    Start-Sleep -Seconds 5
}
