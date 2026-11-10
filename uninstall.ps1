$ErrorActionPreference = "Continue"
Remove-Item (Join-Path $env:USERPROFILE "bin\hub.cmd") -Force
Remove-Item (Join-Path $env:LOCALAPPDATA "HUB") -Recurse -Force
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$bin = Join-Path $env:USERPROFILE "bin"
[Environment]::SetEnvironmentVariable("Path", (($userPath -split ";" | Where-Object { $_ -and $_ -ne $bin }) -join ";"), "User")
Write-Host "HUB application uninstalled. Your workspace files and folders were not deleted."
