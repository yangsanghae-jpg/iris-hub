#!/bin/bash
# PPT 탭 웹 셸(진단툴과 동일 기술 스택) 개발 서버 실행.
set -euo pipefail
cd "$(dirname "$0")/.."
exec /Users/iris/iris-local/venv/iris-hub/bin/python3 -m uvicorn web.server:app \
  --host 127.0.0.1 --port 8766 --reload
