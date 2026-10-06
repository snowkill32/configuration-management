$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$vfsPath = Join-Path $projectRoot 'vfs.xml'

foreach ($name in @(
    'error_unknown', 'error_arguments', 'error_exit', 'error_ls'
)) {
    $scriptPath = Join-Path $projectRoot "examples/$name.txt"
    & python $mainPath --vfs $vfsPath --script $scriptPath
    if ($LASTEXITCODE -ne 1) { throw "Expected script error: $name" }
}

$missingPath = Join-Path $projectRoot 'examples/missing-script.txt'
& python $mainPath --vfs $vfsPath --script $missingPath
if ($LASTEXITCODE -ne 1) { throw 'Expected missing script error' }

Write-Output 'OK: script errors'
