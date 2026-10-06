$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$startupPath = Join-Path $projectRoot 'examples/startup.txt'

foreach ($name in @('minimal', 'files', 'deep')) {
    $vfsPath = Join-Path $projectRoot "examples/$name.xml"
    & python $mainPath --vfs $vfsPath --script $startupPath
    if ($LASTEXITCODE -ne 0) { throw "Explicit parameters failed: $name" }

    # Передаем exit в программу, чтобы она не ждала ввода.
    'exit' | & python $mainPath --vfs $vfsPath
    if ($LASTEXITCODE -ne 0) { throw "Interactive mode failed: $name" }
}

& python $mainPath --script $startupPath
if ($LASTEXITCODE -ne 0) { throw 'Default VFS parameter failed' }

Write-Output 'OK: configuration and interactive mode'
