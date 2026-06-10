@echo off
setlocal
title Gateway Changer CLI

powershell.exe -ExecutionPolicy Bypass -File "%~dp0GatewayChanger.ps1"
endlocal