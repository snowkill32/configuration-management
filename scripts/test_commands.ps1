$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$vfsPath = Join-Path $projectRoot 'examples/deep.csv'
$scriptPath = Join-Path $projectRoot 'examples/stage4.txt'
$before = (Get-FileHash -LiteralPath $vfsPath).Hash

# abc поступает в стандартный ввод для команды rev без имени файла.
'abc' | & python $mainPath --vfs $vfsPath --script $scriptPath
if ($LASTEXITCODE -ne 0) { throw 'Stage 4 demonstration failed' }
$after = (Get-FileHash -LiteralPath $vfsPath).Hash
if ($before -ne $after) { throw 'Commands modified the source CSV' }

Write-Output 'OK: ls, cd, pwd, whoami, rev and unchanged CSV'
