#!/usr/bin/env bash
# iris-hub dev 머신 부트스트랩 (M2 대상 — hostname 기반 config라 어느 dev 머신에서도 동작).
#
# 하는 일: 최신 코드 pull → venv+deps → 빈 볼트(iris-data) 초기화.
# 안 하는 일: 구 데이터(iris-knowledge/iris-system) 이관·수정. 재출발 전제 — 방치(S8에서 아카이브).
#
# 사용:  bash scripts/setup_m2.sh            # 기본 브랜치 feat/hub-rebuild
#        bash scripts/setup_m2.sh main       # 특정 브랜치
#        PYTHON=python3.12 bash scripts/setup_m2.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
BRANCH="${1:-feat/hub-rebuild}"
PY="${PYTHON:-python3}"

echo "▶ iris-hub 부트스트랩"
echo "  repo   : $REPO_DIR"
echo "  branch : $BRANCH"
echo "  python : $($PY --version 2>&1)"
echo "  host   : $(hostname)"
echo

# ── 0) 커밋 안 된 로컬 변경 방어 ──────────────────────────────────────────
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "✋ 커밋되지 않은 로컬 변경이 있습니다. 머신 오갈 땐 먼저 commit/push 하세요."
  git status --short
  exit 1
fi

# ── 1) 최신 코드 ──────────────────────────────────────────────────────────
echo "① 코드 동기화 (git)"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
echo "   → $(git log --oneline -1)"
echo

# ── 2) venv + 의존성 ──────────────────────────────────────────────────────
echo "② Python 환경 (.venv)"
if [ ! -d .venv ]; then
  "$PY" -m venv .venv
  echo "   → .venv 생성"
fi
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt
echo "   → 의존성 설치 완료"
echo "   (참고: OCR/PDF 이미지·Presenton 등 일부 기능은 시스템 패키지 필요:"
echo "         brew install tesseract poppler   /   playwright install chromium)"
echo

# ── 3) 빈 볼트 초기화 (hostname 기반 config가 이 머신 경로 자동 결정) ─────────
echo "③ 볼트 초기화 (init_vault — 멱등)"
./.venv/bin/python -m scripts.init_vault
echo

# ── 4) 안내 ───────────────────────────────────────────────────────────────
echo "✅ 완료. 이 머신은 M5와 동일한 깨끗한 재구축본 + 빈 볼트 상태."
echo
echo "   실행:   ./.venv/bin/streamlit run app.py"
echo "   테스트: ./.venv/bin/python -m pytest tests -q"
echo
echo "   머신 오갈 때: 떠나기 전 'git add -A && git commit && git push',"
echo "                도착해서 'bash scripts/setup_m2.sh' (또는 git pull) 만 하면 됩니다."
