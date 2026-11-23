#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

pypi_mirror="${PIP_MIRROR:-https://pypi.tuna.tsinghua.edu.cn/simple}"
npm_mirror="${NPM_MIRROR:-https://registry.npmmirror.com}"
case "${1:-}" in
    --official)
        pypi_mirror=https://pypi.org/simple
        npm_mirror=https://registry.npmjs.org
        ;;
    '') ;;
    *) echo "Usage: bash setup.sh [--official]" >&2; exit 2 ;;
esac

python3 -c 'import sys; assert (3,12) <= sys.version_info[:2] < (3,15), "Python 3.12 to 3.14 is required"'
node -e 'if (+process.versions.node.split(".")[0] < 22) throw Error("Node.js 22+ is required")'

if [[ ! -x .venv/bin/python ]]; then
    if python3 -c 'import ensurepip' 2>/dev/null; then
        python3 -m venv .venv
    else
        python3 -m venv --without-pip .venv
    fi
fi
if .venv/bin/python -m pip --version >/dev/null 2>&1; then
    pip_command=(.venv/bin/python -m pip)
elif python3 -m pip --version >/dev/null 2>&1; then
    pip_command=(python3 -m pip --python .venv/bin/python)
else
    echo "Install Ubuntu's python3-venv package, then rerun setup.sh." >&2
    exit 1
fi
dependencies="$(.venv/bin/python -c 'import tomllib; from pathlib import Path; print(*tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"], sep=chr(10))')"
mapfile -t packages <<< "$dependencies"
"${pip_command[@]}" install --only-binary=:all: --index-url "$pypi_mirror" "${packages[@]}"
npm ci --registry "$npm_mirror" --no-audit --no-fund
echo "Ready. Run .venv/bin/python wallpaper.py build"
