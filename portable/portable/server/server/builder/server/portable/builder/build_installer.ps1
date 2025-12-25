# TitanFusion Installer Builder
param (
    [string]$SourcePath = "..\portable",
    [string]$OutputPath = "..\dist"
)

Write-Host "Building TitanFusion Installer..."

if (!(Test-Path $OutputPath)) {
    New-Item -ItemType Directory -Path $OutputPath | Out-Null
}

$exeName = "TitanFusion_Setup.exe"
$exePath = Join-Path $OutputPath $exeName

# Placeholder for installer build logic
Copy-Item "$SourcePath\*" $OutputPath -Recurse -Force

Write-Host "Installer files prepared at $OutputPath"
Write-Host "Use Inno Setup or NSIS to generate final EXE."
