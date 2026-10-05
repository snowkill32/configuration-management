$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$mainPath = Join-Path $projectRoot 'src/main.py'
$startupPath = Join-Path $projectRoot 'examples/startup.txt'

foreach ($name in @('minimal', 'files', 'deep')) {
    $vfsPath = Join-Path $projectRoot "examples/$name.xml"
    $before = (Get-FileHash -LiteralPath $vfsPath).Hash
    & python $mainPath --vfs $vfsPath --script $startupPath
    if ($LASTEXITCODE -ne 0) { throw "VFS loading failed: $name" }
    $after = (Get-FileHash -LiteralPath $vfsPath).Hash
    if ($before -ne $after) { throw "VFS was modified: $name" }
}

$vfsPath = Join-Path $projectRoot 'examples/deep.xml'
$scriptPath = Join-Path $projectRoot 'examples/demo_all.txt'
& python $mainPath --vfs $vfsPath --script $scriptPath
if ($LASTEXITCODE -ne 1) { throw 'Expected demo error after valid commands' }

foreach ($name in @('invalid', 'missing')) {
    $vfsPath = Join-Path $projectRoot "examples/$name.xml"
    & python $mainPath --vfs $vfsPath --script $startupPath
    if ($LASTEXITCODE -ne 1) { throw "Expected VFS error: $name" }
}

Write-Output 'OK: VFS examples, unchanged XML and loading errors'
