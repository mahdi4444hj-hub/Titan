@echo off
set BASEDIR=%~dp0
set CONFIG=%BASEDIR%\..\config.yaml

echo Starting TitanFusion Portable...
TitanFusionCore.exe --portable --config "%CONFIG%"
pause
