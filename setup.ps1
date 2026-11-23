# Run from PowerShell. An existing Python 3.12–3.14 and Node.js 22+ are required.
param(
    [string]$PyPIMirror = "https://pypi.tuna.tsinghua.edu.cn/simple",
    [string]$NpmMirror = "https://registry.npmmirror.com",
    [switch]$Official
)
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program failed with exit code $LASTEXITCODE" }
}

if ($Official) {
    $PyPIMirror = "https://pypi.org/simple"
    $NpmMirror = "https://registry.npmjs.org"
}
Push-Location -LiteralPath $PSScriptRoot
try {
    Invoke-Checked python @("-c", "import sys; assert (3,12) <= sys.version_info[:2] < (3,15), 'Python 3.12 to 3.14 is required'")
    Invoke-Checked node @("-e", "if (+process.versions.node.split('.')[0] < 22) throw Error('Node.js 22+ is required')")
    $venvPython = Join-Path $PSScriptRoot ".venv/Scripts/python.exe"
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Invoke-Checked python @("-m", "venv", ".venv")
    }
    $deps = & $venvPython -c "import tomllib; from pathlib import Path; print(*tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))['project']['dependencies'], sep=chr(10))"
    if ($LASTEXITCODE -ne 0) { throw "Could not read dependencies from pyproject.toml" }
    Invoke-Checked $venvPython (@("-m", "pip", "install", "--only-binary=:all:", "--index-url", $PyPIMirror) + $deps)
    Invoke-Checked npm.cmd @("ci", "--registry", $NpmMirror, "--no-audit", "--no-fund")
    Write-Host "Ready. Run .\.venv\Scripts\python.exe wallpaper.py build"
} finally {
    Pop-Location
}
