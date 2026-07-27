#!/usr/bin/env bash
# V3.1 Shell — 시작 스크립트 (port 8767)
# Usage:  bash v31/start.sh
set -euo pipefail
cd "$(dirname "$0")/.."
# --reload 은 소스 디렉터리만 감시한다.
# 루트 전체를 감시하면 external/(node_modules·vite·esbuild), .git 까지 폴링해
# 요청이 없어도 리로더가 CPU를 지속 점유(스래싱)한다.
exec /Users/iris/iris-local/venv/iris-hub/bin/python3 -m uvicorn v31.server:app \
  --host 127.0.0.1 --port 8767 --reload \
  --reload-dir v31 --reload-dir src --reload-dir web
