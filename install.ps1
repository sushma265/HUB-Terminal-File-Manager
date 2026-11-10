# HUB one-command installer for Windows PowerShell.
# Published usage:
# irm https://raw.githubusercontent.com/sushma265/HUB-Terminal-File-Manager/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$Repo = "sushma265/HUB-Terminal-File-Manager"
$Branch = "main"
$Raw = "https://raw.githubusercontent.com/$Repo/$Branch"
$AppDir = Join-Path $env:LOCALAPPDATA "HUB"
$BinDir = Join-Path $env:USERPROFILE "bin"
$ConfigDir = Join-Path $env:APPDATA "HubFileManager"

Write-Host "`nHUB - Personal Terminal File Manager installer" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $AppDir, $BinDir, $ConfigDir | Out-Null

# Download the actual application from the public GitHub repository.
Invoke-WebRequest -Uri "$Raw/hub.py" -OutFile (Join-Path $AppDir "hub.py")

# Ask each user to choose their own workspace. Default is their Documents folder.
$defaultWorkspace = Join-Path $env:USERPROFILE "Documents"
$workspace = Read-Host "Workspace folder [$defaultWorkspace]"
if ([string]::IsNullOrWhiteSpace($workspace)) { $workspace = $defaultWorkspace }
$workspace = [Environment]::ExpandEnvironmentVariables($workspace.Trim('"'))
if (-not (Test-Path -LiteralPath $workspace -PathType Container)) {
    throw "Folder does not exist: $workspace. Create it first, then run the installer again."
}
$config = @{ workspace = $workspace } | ConvertTo-Json
Set-Content -Path (Join-Path $ConfigDir "config.json") -Value $config -Encoding UTF8

# A small command shim makes `hub` available from any working directory.
$cmd = "@echo off`r`npy -3 `"$AppDir\hub.py`" %*`r`n"
Set-Content -Path (Join-Path $BinDir "hub.cmd") -Value $cmd -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathParts = @($userPath -split ";" | Where-Object { $_ })
if ($pathParts -notcontains $BinDir) {
    [Environment]::SetEnvironmentVariable("Path", ((@($pathParts) + $BinDir) -join ";"), "User")
}
if (($env:Path -split ";") -notcontains $BinDir) { $env:Path += ";$BinDir" }

Write-Host "`nHUB installed successfully." -ForegroundColor Green
Write-Host "Workspace: $workspace"
Write-Host "Open a NEW terminal and run: hub"
Write-Host "Change workspace later with: hub config"
