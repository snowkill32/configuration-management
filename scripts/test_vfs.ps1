$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$scriptPath = Join-Path $projectRoot 'examples/demo_all.txt'

foreach ($name in @('minimal', 'files', 'deep')) {
    $vfsPath = Join-Path $projectRoot "examples/$name.csv"
    # Сравниваем содержимое исходного CSV до и после выполнения команд.
    $before = (Get-FileHash -LiteralPath $vfsPath).Hash
    & python $mainPath --vfs $vfsPath --script $scriptPath
    if ($LASTEXITCODE -ne 0) { throw "VFS demo failed: $name" }
    $after = (Get-FileHash -LiteralPath $vfsPath).Hash
    if ($before -ne $after) { throw "CSV was modified: $name" }
}

& python $mainPath --script $scriptPath
if ($LASTEXITCODE -ne 0) { throw 'Default VFS failed' }

foreach ($name in @('missing', 'invalid')) {
    $vfsPath = Join-Path $projectRoot "examples/$name.csv"
    & python $mainPath --vfs $vfsPath --script $scriptPath
    if ($LASTEXITCODE -ne 1) { throw "Expected loading error: $name" }
}

Write-Output 'OK: VFS examples, unchanged CSV and loading errors'
