$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$vfsPath = Join-Path $projectRoot 'vfs.csv'
$startupPath = Join-Path $projectRoot 'examples/startup.txt'

foreach ($name in @(
    'error_unknown', 'error_arguments', 'error_exit', 'error_ls', 'error_quotes'
)) {
    $scriptPath = Join-Path $projectRoot "examples/$name.txt"
    & python $mainPath --vfs $vfsPath --script $scriptPath
    if ($LASTEXITCODE -ne 0) { throw "Script did not continue: $name" }
}

$missingPath = Join-Path $projectRoot 'examples/missing-script.txt'
& python $mainPath --vfs $vfsPath --script $missingPath
if ($LASTEXITCODE -ne 1) { throw 'Expected missing script error' }

'exit' | & python $mainPath --vfs $vfsPath
if ($LASTEXITCODE -ne 0) { throw 'Interactive mode failed' }

& python $mainPath --script $startupPath
if ($LASTEXITCODE -ne 0) { throw 'Default VFS parameter failed' }

Write-Output 'OK: script errors'
