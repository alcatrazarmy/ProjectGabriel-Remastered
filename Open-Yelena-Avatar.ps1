$ErrorActionPreference = 'Stop'
$viewer = 'D:\Avatar\Yelena-Xiomora\Yelena-viewer.html'
$browser = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $viewer)) { throw 'Local avatar viewer is missing.' }
if (-not (Test-Path -LiteralPath $browser)) { throw 'The existing Windows browser was not found.' }
$env:TEMP = 'D:\Temp'
$env:TMP = 'D:\Temp'
Start-Process -FilePath $browser -ArgumentList '--user-data-dir=D:\Avatar\Yelena-Xiomora\viewer-profile','--no-first-run','--disable-extensions','--disable-background-networking','--new-window','file:///D:/Avatar/Yelena-Xiomora/Yelena-viewer.html'
