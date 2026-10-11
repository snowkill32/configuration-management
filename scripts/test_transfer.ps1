$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$vfsPath = Join-Path $projectRoot 'examples/deep.csv'
$scriptPath = Join-Path $projectRoot 'examples/stage5.txt'
$before = (Get-FileHash -LiteralPath $vfsPath).Hash

& python $mainPath --vfs $vfsPath --script $scriptPath
if ($LASTEXITCODE -ne 0) { throw 'Stage 5 demonstration failed' }
$after = (Get-FileHash -LiteralPath $vfsPath).Hash
if ($before -ne $after) { throw 'Commands modified the source CSV' }

# При новом запуске снова загружаются исходные данные из CSV.
@('ls /', 'ls /docs', 'exit') | & python $mainPath --vfs $vfsPath
if ($LASTEXITCODE -ne 0) { throw 'Restart failed' }
Write-Output 'OK: cp, mv, unchanged CSV and restart'
