param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$avatarSelection = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config\avatar-local.json') -Raw | ConvertFrom-Json
if ($avatarSelection.enabled -eq $false -or -not $avatarSelection.vrm_path) {
    throw 'Previous avatar removed. The selected MetaHuman assets must be configured before opening a replacement.'
}
$windowPython = if ($env:YELENA_PYTHON) { $env:YELENA_PYTHON } else { 'A:\Tools\gabriel-venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $windowPython)) { throw 'Companion Python is missing. Set YELENA_PYTHON to its python.exe.' }
$windowUrl = 'http://127.0.0.1:8768'
$windowData = Join-Path $PSScriptRoot 'data\desktop-window'
New-Item -ItemType Directory -Force -Path $windowData | Out-Null
$windowStatus = $null
try { $windowStatus = Invoke-RestMethod "$windowUrl/api/status" -TimeoutSec 2 } catch {}
if ($windowStatus -and $windowStatus.service -ne 'yelena-desktop') { throw 'Port 8768 belongs to another service.' }
if (-not $windowStatus) {
    $windowScript = Join-Path $PSScriptRoot 'scripts\serve_desktop_window.py'
    $windowProcess = Start-Process -FilePath $windowPython -ArgumentList @('-B', ('"' + $windowScript + '"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $windowData 'server.stdout.log') -RedirectStandardError (Join-Path $windowData 'server.stderr.log')
    $windowProcess.Id | Set-Content (Join-Path $windowData 'server.pid')
    for ($windowAttempt = 0; $windowAttempt -lt 40; $windowAttempt++) {
        if ($windowProcess.HasExited) { throw "Window server exited. See $windowData\server.stderr.log" }
        try { $windowStatus = Invoke-RestMethod "$windowUrl/api/status" -TimeoutSec 1; break } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $windowStatus -or $windowStatus.service -ne 'yelena-desktop') { throw 'Window server did not become ready.' }
}
if (-not $NoBrowser) {
    $windowBrowser = @('A:\Apps\Microsoft\Edge\Application\msedge.exe', 'A:\Tools\Microsoft\Edge\Application\msedge.exe', 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', 'C:\Program Files\Microsoft\Edge\Application\msedge.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $windowBrowser) { throw "Open $windowUrl in your browser; Edge executable was not found." }
    $windowProfile = Join-Path $windowData 'browser-profile'
    Start-Process -FilePath $windowBrowser -ArgumentList @("--app=$windowUrl/?motion=1", ('--user-data-dir="' + $windowProfile + '"'), '--no-first-run') -WindowStyle Normal
}
Write-Output "Yelena window: $windowUrl"
Write-Output 'Avatar movement is active. Messages and speech movement connect to the original app on port 8766.'
Write-Output 'Conversation audio uses the original app output. The window output selector controls voice tests only.'
