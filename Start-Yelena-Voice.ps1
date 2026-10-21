param([string]$Device = 'auto')
$ErrorActionPreference = 'Stop'
$voicePython = 'A:\Tools\yelena-tts\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $voicePython)) {
    throw 'The isolated voice environment is missing. See LOCAL-SERVICES.md.'
}
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = 'D:\Temp'
$env:TMP = 'D:\Temp'
& $voicePython -B (Join-Path $PSScriptRoot 'scripts\serve_local_voice.py') --config (Join-Path $PSScriptRoot 'config.yml') --device $Device
exit $LASTEXITCODE
