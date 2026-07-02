# PPT 탭 UX 재정렬 설계서 — 흐름 탭 패턴 적용

- 작성일: 2026-07-02
- 대상: `src/tabs/pptx.py`
- 기준 화면: `src/tabs/flow.py`
- 목표: PPT 탭을 독립 카드/입력 탭 스타일이 아니라, 흐름 탭의 처리 콘솔 UI와 동일한 문법으로 재구성한다.

## 1. 문제

현재 PPT 탭은 다음 문제가 있다.

1. 상단 설명, 소스 선택, 텍스트 입력, 엔진 선택이 기본 Streamlit 위젯 흐름으로 노출되어 `흐름` 탭과 시각 언어가 다르다.
2. 이전 수정에서 `입력` 탭의 mode card/panel header 계열 스타일이 섞여 `흐름` 탭과 통일되지 않았다.
3. pagebar 설명이 좁은 영역에서 잘리거나 한 줄로 압축되어 보일 수 있다.
4. PPT 생성 과정이 `소스 → 엔진 → 옵션 → 생성`이라는 처리 흐름임에도, `흐름` 탭처럼 단계 카드로 먼저 인지되지 않는다.

## 2. 기준 패턴: 흐름 탭

`flow.py`의 UX 문법은 아래 네 가지다.

1. `hub_pagebar()`
   - 페이지 타이틀, 콘솔 라벨, 설명, readiness pill을 한 줄 상단 콘솔로 표현한다.
2. `.flow-row` + `.flow-card` + `.flow-arrow`
   - 상태 또는 파이프라인을 가로 카드 흐름으로 보여준다.
   - active/empty/alert 상태를 카드 class로 구분한다.
3. `hub_section()`
   - 큰 마크다운 헤더 대신 파란 섹션 바를 사용한다.
4. 기본 Streamlit 위젯은 유지하되, 버튼/metric은 flow CSS로만 보정한다.

## 3. PPT 탭 매핑

PPT 탭의 구조를 `흐름` 탭 기준으로 다음처럼 매핑한다.

| 흐름 탭 개념 | PPT 탭 적용 |
|---|---|
| 처리 상태 카드 | PPT 생성 파이프라인 카드 |
| 대기 → 처리중 → 완료 → archive | 소스 → 원문 → 엔진 → 산출 |
| 처리 액션 섹션 | 변환 설정 섹션 |
| Obsidian 동기화 섹션 | 생성 액션 섹션 |
| flow-console-note | 선택된 소스/본문 길이 요약 |

## 4. 최종 레이아웃

1. `hub_pagebar("PPT", "Deck Console", ..., "Export Ready")`
2. `.flow-row.pipeline` 카드 4개
   - ① Source: 선택된 소스 유형
   - ② Markdown: 본문 글자 수
   - ③ Engine: Marp 또는 Design
   - ④ Export: PPTX/PDF/exports
3. `hub_section("소스 선택")`
   - radio + 선택된 소스별 입력 위젯
4. `hub_section("변환 설정")`
   - flow-console-note로 현재 소스 상태 표시
   - 엔진 선택 radio
   - 좌측: 디자인 엔진 메타 정보 또는 source summary
   - 우측: 모델/옵션/생성 버튼
5. 생성 결과는 기존 `_generate_marp`, `_generate_design` 로직 유지

## 5. 구현 원칙

- `입력` 탭 스타일 클래스(`pptx-mode-*`, `pptx-panel-*`)는 제거한다.
- PPT 전용 CSS는 `flow.py`의 class 이름과 구조를 그대로 사용한다.
- 기능 로직은 건드리지 않는다.
- 외부 탭 폐기 여부와 무관하게 PPT 탭만 수정한다.
- 목업은 만들지 않는다.

## 6. 검증

- `python3 -m py_compile src/tabs/pptx.py`
- `ReadLints`로 `src/tabs/pptx.py` 확인
