# M2 셋업 지시서 — 재구축본 동기화

- 작성: 2026-07-03
- 대상: M2(개발·테스트 전용 머신). M5↔M2를 오가며 개발하기 위한 동기화.
- 전제: **재출발** — M2의 구 데이터를 고치거나 옮기지 않는다. 코드는 Git으로, 볼트는 새로 만든다.

---

## 0. 원칙 (왜 이렇게 하나)

| 무엇 | 동기화 수단 | 이유 |
|---|---|---|
| **코드** | **Git** (`push`/`pull`) | M5↔M2 백본. `config.py`가 hostname 기반이라 M2 경로는 자동. M2용 코드 수정 **불필요**. |
| **볼트 데이터** | **재생성**(`init_vault`) | M5 볼트도 지금 비어 있음(시드 개념 7개뿐). 옮길 실데이터 없음 → M2도 init 한 번이면 동일 상태. |
| **구 데이터**(iris-knowledge/iris-system) | **방치** | 재출발 전제. 고치는 건 자원 낭비. 보존은 S8에서 아카이브. |

> 결론: M2를 "고치지" 않는다. **pull + init_vault**로 M5와 같은 깨끗한 상태를 몇 분 만에 만든다.

---

## 1. 최초 1회 (repo 없을 때만)

```bash
# M2 개발 루트: ~/Documents/1Dev  (config가 이 경로를 M2 기본값으로 씀)
cd ~/Documents/1Dev
git clone git@github.com:yangsanghae-jpg/iris-hub.git
cd iris-hub
```

이미 clone돼 있으면 이 단계는 건너뛴다.

## 2. 셋업 (매번 이 한 줄)

```bash
bash scripts/setup_m2.sh
```

스크립트가 하는 일 (멱등 — 여러 번 실행 안전):
1. `git fetch` → `feat/hub-rebuild` 체크아웃 → `pull --ff-only`
2. `.venv` 생성 + `requirements.txt` 설치
3. `python -m scripts.init_vault` — `~/Documents/1Dev/iris-data` 빈 볼트 생성(스키마 v1 + 개념 시드)

특정 브랜치로: `bash scripts/setup_m2.sh main`

## 3. 실행

```bash
./.venv/bin/streamlit run app.py      # 앱 (기본 http://localhost:8501)
./.venv/bin/python -m pytest tests -q # 테스트
```

M2는 dev/test 전용이므로 iris-local 라이브 배포(:8765) 분리는 둘 필요 없이 **직접 실행**이 더 단순하다.

---

## 4. M5 ↔ M2 오가는 개발 루틴

Git이 곧 동기화다. 규칙은 두 줄:

- **떠나기 전 (머신 A):** `git add -A && git commit -m "..." && git push`
- **도착해서 (머신 B):** `bash scripts/setup_m2.sh` (또는 최소 `git pull`)

> 커밋 안 하고 머신을 바꾸면 그 변경은 다른 머신에 없다. 스크립트는 커밋 안 된 변경이 있으면 멈추고 경고한다.

---

## 5. 주의사항

- **iCloud/.nosync**: M2 볼트는 `~/Documents/1Dev/iris-data` 아래 생기고 Documents는 iCloud 미러다. 대용량 바이너리(`index.db`·faiss)는 설계상 `vault/.nosync/`(iCloud 제외)에 두고 심볼릭한다 — `init_vault`가 자동 처리하므로 iCloud로 DB가 새지 않는다.
- **시스템 의존성(선택)**: 일부 기능만 필요.
  - OCR·스캔 PDF: `brew install tesseract poppler`
  - Presenton/브라우저 렌더: `playwright install chromium`
  - 안 깔아도 앱·핵심 파이프라인은 동작.
- **구 데이터는 손대지 않는다**: `~/Documents/1Dev/iris-knowledge`, iris-system 심볼릭 등은 그대로 방치. S8에서 아카이브 처리.

---

## 6. (옵션) 실데이터 연속성이 필요해질 때만

M2가 순 dev/test인 한 볼트는 각자 비워도 된다. 다만 나중에 **M5에서 실문서를 대량 재수집**해두고 M2에서 그걸 이어 보고 싶다면, 그때만 볼트를 옮긴다:

```bash
# M5에서 실행 (실볼트 → M2로). .nosync 실파일만 rsync.
rsync -av --delete \
  ~/0Dev/iris-data/vault/.nosync/ \
  irisM2:~/Documents/1Dev/iris-data/vault/.nosync/
```

무거운 실배치는 M5(M5 Max·128GB)에서 돌리고, M2로는 필요할 때만 내려받는 걸 권장.
