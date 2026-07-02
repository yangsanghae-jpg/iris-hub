# iris-hub UX 개선 설계서 — 테마·타이포그래피·밀도

- 작성일: 2026-07-02
- 대상: `.streamlit/config.toml`(신규), `data/themes/hub_ui.css`(신규), `app.py`,
  `src/ui_kit.py`(신규), `src/tabs/*.py`(15개 탭 전체, 헤더·CSS 정리)
- 전제(사전 점검, 2026-07-02 근거):
  - `.streamlit/config.toml` **없음** — 앱 전체가 Streamlit 기본 테마 그대로 렌더링 중
  - `font-family` 지정 **전무** — grep 결과 어떤 파일에도 없음
  - 탭마다 각자 `<style>` 블록을 인라인으로 인젝션(`unsafe_allow_html`) — 5개 파일에서 발견,
    개중 `wiki_k2.py`의 `.wiki-prog-*`/`.wiki-bar*`는 `inventory.py`의 `.inv-prog-*`/`.inv-bar*`와
    **바이트 단위로 동일**(주석에 "데이터 탭과 동일"이라고 스스로 명시돼 있음) — 이미 실제로
    중복이 발생한 상태, 가정이 아님
  - 앱 전체에서 `st.markdown("#"~"#####")`/`st.subheader`/`st.header` 형태의 **원시 헤더 40곳**
    (`flow.py` 6곳, `intake.py`/`dashboard.py` 각 5곳, `diagnosis_mgmt.py` 4곳 등) —
    Streamlit 기본 h3 크기(1.75rem=28px, weight 600)를 그대로 쓰고 있어 "처리 액션" 같은
    작은 소제목에도 페이지 타이틀급 크기가 적용됨
  - `st.divider()` 사용 **28곳** — 구분선 하나당 위아래 여백까지 이중으로 공간을 먹음
  - 설치 Streamlit 버전: **1.50.0** (`[theme.fontFaces]`, `font`의 CDN URL 문법 등 최신 테마
    기능 전부 지원 확인됨 — `streamlit config show`로 실제 스키마 확인)

---

## 0. 요약

| # | 문제 | 근본 원인 | 조치 |
|---|---|---|---|
| A | "학생 프로젝트 같다" | `.streamlit/config.toml` 부재 → 100% 기본 Streamlit 스타일 | 테마 파일 신설 (팔레트·폰트·radius) |
| B | 탭마다 스타일이 미묘하게 다름 | 5개 파일에 각자 CSS, 이미 실제 중복 발생(`wiki_k2`/`inventory` 동일 CSS) | 공유 스타일시트 `hub_ui.css`로 통합, 중복분 제거 |
| C | 큰 소제목이 화면을 많이 차지 | 원시 마크다운 헤더 40곳이 기본 h3(28px) 크기 그대로 사용 | `hub_section()` 컴포넌트로 통일 (이미 3개 탭에 부분적으로 존재하는 축소 라벨 패턴을 표준화) |
| D | 스크롤이 길다 | Streamlit 기본 블록 간격(요소당 ~1rem) + `st.divider()` 28곳의 이중 여백 | 전역 간격 압축 CSS + divider 감축(섹션 라벨로 대체) |

A+B+C+D는 사실상 **하나의 작업**(공유 CSS 파일 + 헤더 컴포넌트 하나 도입)으로 동시에 해결된다 —
새 기능이 아니라 이미 곳곳에 흩어져 있던 좋은 패턴(`.wiki-sec` 스타일 소제목, `.flow-card`의 절제된
패딩)을 표준화하고 전체 적용하는 작업.

---

## Part A — Streamlit 테마 (`.streamlit/config.toml`)

### A1. 신규 파일

```toml
[theme]
base = "light"

# 팔레트 — Deck V3 설계서(docs/design/DECK_V3_DESIGN.md)의 accent와 동일 값으로 통일
# (PPT 산출물과 hub 화면이 같은 브랜드 색을 쓰게 됨)
primaryColor = "#2f80c4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f5f7fa"      # Deck V3의 --paper-dim과 동일
textColor = "#1f2937"
borderColor = "#d8dce3"

# 기존 탭 CSS에서 이미 쓰던 alert/warn 색을 그대로 승격 (시각적 급변 없음)
redColor = "#f08585"
orangeColor = "#ffb86b"
blueColor = "#5fa8ff"
greenColor = "#7ed6a3"

# 폰트 — 한글 렌더링 품질 우선. Pretendard 웹폰트.
# ⚠️ 구현 시 검증 필수: CDN URL은 예시이며 실제 접속 테스트로 확정할 것
# (jsdelivr의 pretendard 배포 경로가 static/variable 등 여러 갈래가 있음)
font = "Pretendard:https://cdn.jsdelivr.net/gh/orioncactus/pretendard@main/dist/web/static/pretendard.css, sans-serif"
headingFont = "Pretendard:https://cdn.jsdelivr.net/gh/orioncactus/pretendard@main/dist/web/static/pretendard.css, sans-serif"

baseRadius = "8px"          # 이미 .flow-card가 쓰던 8px와 통일
showWidgetBorder = true     # 위젯 경계 뚜렷하게 — "제품처럼" 보이는 데 의외로 효과 큼
```

### A2. 선택 사항 — 자체 호스팅 폰트 (CDN 실패 시 대안)

CDN 문법이 이 Streamlit 버전에서 기대대로 안 동작하면 `[[theme.fontFaces]]` + 정적 파일 서빙으로 대체:

```toml
[server]
enableStaticServing = true

[[theme.fontFaces]]
family = "Pretendard"
url = "app/static/Pretendard-Regular.woff2"
weight = "400"

[[theme.fontFaces]]
family = "Pretendard"
url = "app/static/Pretendard-SemiBold.woff2"
weight = "600"
```
(폰트 파일을 `static/`에 직접 두는 방식 — 오프라인·CDN 차단 환경에서도 동작. A1이 우선, 실패 시 이걸로.)

### A3. 검증 항목

- CDN 폰트가 실제로 로드되는지 브라우저 개발자도구 Network 탭에서 확인 (구현 시)
- `redColor`/`orangeColor`/`blueColor`/`greenColor`를 지정하면 Streamlit이 배경·텍스트 변형을
  자동 파생한다(`streamlit config show`에서 확인) — 기존 탭 CSS의 `rgba(240,133,133,0.08)` 같은
  수동 파생값과 미묘하게 다를 수 있으니, Part B 작업 시 Streamlit 자동파생값 우선 사용 검토

---

## Part B — 공유 스타일시트 (`data/themes/hub_ui.css`)

### B1. 설계 원칙

**앱의 커스텀 CSS는 이 파일 하나만 존재한다.** 개별 탭 파일은 더 이상 자체 `_CSS` 상수·
`unsafe_allow_html` `<style>` 블록을 갖지 않는다 — `app.py`가 시작 시 한 번만 주입.

기존 5개 파일의 인라인 CSS 중:
- **완전 중복**(`.wiki-prog-*`↔`.inv-prog-*`, `.wiki-bar*`↔`.inv-bar*`, `.wiki-zeros`↔`.inv-zeros`)
  → 접두어 없는 공용 클래스로 통합 (`.hub-prog-wrap`, `.hub-bar`, `.hub-zeros` 등)
- **탭 고유 컴포넌트**(`.flow-card`, `.flow-arrow`, `.flow-gap`) → 그대로 이관, 클래스명 유지
  (다른 탭이 안 쓰는 진짜 고유 UI이므로 접두어 유지, 단 색상값은 토큰으로 치환)

### B2. 디자인 토큰

```css
/* data/themes/hub_ui.css */
:root {
  --hub-muted: #888;
  --hub-muted-2: #999;
  --hub-muted-3: #bbb;
  --hub-border: rgba(120,120,120,0.20);
  --hub-bg-tint: rgba(120,120,120,0.06);
  --hub-bg-tint-strong: rgba(120,120,120,0.10);
  --hub-accent: #2f80c4;            /* config.toml primaryColor와 동일 값 유지 */
  --hub-grad-start: #7ed6a3;        /* 기존 progress bar 그라디언트 그대로 보존 */
  --hub-grad-end: #5fa8ff;
  --hub-alert: #f08585;
  --hub-warn: #ffb86b;
  --hub-radius: 8px;
}
```

### B3. 공용 컴포넌트 (기존 중복 코드 대체)

```css
.hub-section {
  font-size: 0.78em; font-weight: 600; color: var(--hub-muted);
  letter-spacing: 0.5px; margin: 14px 0 6px 0; text-transform: none;
}
.hub-prog-wrap {
  position: relative; height: 28px; background: var(--hub-bg-tint-strong);
  border: 1px solid var(--hub-border); border-radius: 6px; overflow: hidden;
}
.hub-prog-fill {
  position: absolute; left: 0; top: 0; bottom: 0;
  background: linear-gradient(90deg, var(--hub-grad-start) 0%, var(--hub-grad-end) 100%);
}
.hub-prog-text {
  position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; font-size: 0.85em; font-weight: 600;
  color: #fff; text-shadow: 0 1px 2px rgba(0,0,0,0.6);
}
.hub-bar { display: flex; height: 26px; border-radius: 6px; overflow: hidden;
           background: var(--hub-bg-tint-strong); border: 1px solid var(--hub-border); }
.hub-bar-seg {
  height: 100%; display: flex; align-items: center; justify-content: flex-start;
  padding: 0 9px; color: #fff; font-size: 0.78em; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  text-shadow: 0 1px 1px rgba(0,0,0,0.45);
}
.hub-zeros { font-size: 0.78em; color: var(--hub-muted); margin-top: 5px; }
.hub-zeros span { margin-right: 10px; }
```

이관 대상: `wiki_k2.py`(`.wiki-*`), `inventory.py`(`.inv-*`) 두 파일의 progress/bar/zeros
관련 규칙 전량 삭제 → 호출부만 `class="wiki-prog-wrap"` → `class="hub-prog-wrap"` 식으로 치환.

### B4. 전역 블록 간격 압축 (Part D의 근거이기도 함)

```css
/* Streamlit 1.50.0 기준 내부 testid — 향후 버전 업그레이드 시 선택자 재확인 필요 */
div[data-testid="stVerticalBlock"] { gap: 0.6rem !important; }
div[data-testid="element-container"] { margin-bottom: 0 !important; }
hr { margin: 0.8rem 0 !important; }               /* st.divider() 여백 절반 축소 */
.block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }  /* app.py 기존값 이관 */
```

`app.py`의 `_inject_css()`는 이 파일을 읽어 한 번만 주입하는 함수로 축소:

```python
def _inject_css() -> None:
    css_path = Path(__file__).parent / "data" / "themes" / "hub_ui.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)
```

---

## Part C — 섹션 헤더 컴포넌트화 (`src/ui_kit.py`, 신규)

### C1. 문제의 실체

앱 전체에서 **원시 마크다운 헤더 40곳**이 소제목 용도로 쓰이는데, config.toml 기본값 기준 h3는
**1.75rem(28px)**, weight 600이다. "처리 액션", "동기 점검" 같은 문장이 화면 타이틀만큼 커서
①시각적으로 유치해 보이고(전문성 문제와 직결) ②세로 공간을 크게 잡아먹는다(밀도 문제와 직결).

이미 `wiki_k2.py`/`inventory.py`/`diagnosis_mgmt.py`에 `.wiki-sec`/`.inv-sec`/`.dt-phase-hdr`라는
**작은 라벨 스타일이 존재**하지만 각 파일에 국지적으로만 쓰이고, 같은 파일 안에서도 어떤 소제목은
이 작은 라벨을, 어떤 소제목은 원시 `### `를 쓰는 등 **일관성 없이 혼용**되고 있다
(예: `diagnosis_mgmt.py`는 `.dt-phase-hdr`를 갖고 있으면서도 `st.markdown("### 📍 Git 스냅샷")` 등
4곳에서 원시 헤더를 그대로 씀).

### C2. 신규 컴포넌트

```python
# src/ui_kit.py
from __future__ import annotations
import streamlit as st

def hub_section(text: str, *, level: str = "sub") -> None:
    """소제목 통일 컴포넌트. level='sub'(기본, 탭 내 섹션) | 'page'(탭 최상단 타이틀 1회만)."""
    if level == "page":
        st.markdown(f"#### {text}")   # 페이지 타이틀급은 h4(1.5rem)까지만 허용 — h1/h2/h3 사용 금지
    else:
        st.markdown(f"<div class='hub-section'>{text}</div>", unsafe_allow_html=True)
```

### C3. 적용 규칙

- 탭 안의 **모든 소제목**("처리 액션", "K2 단계별 진척", "Obsidian 동기화" 등)은
  `hub_section("처리 액션")`로 교체 — `st.markdown("### ...")`/`st.subheader`/`st.header` 금지.
- 탭당 **최상단 타이틀 1개만** `level="page"`(h4) 허용 — 그 이상 큰 헤더(h1~h3)는 앱 전체에서
  `app.py`의 `# 📊 iris-hub` 메인 타이틀 하나로 제한.
- 적용 범위: `flow.py`(6) · `diagnosis_mgmt.py`(4) · `intake.py`(5) · `dashboard.py`(5) ·
  `external_capture.py`(3) · `pptx.py`(1) · `presenton.py`(1) · `placeholders.py`(12) —
  총 40곳 전량 교체.

### C4. `st.divider()` 감축

28곳 중 상당수는 "소제목 앞 구분선" 용도 — `hub_section()` 자체가 `margin: 14px 0 6px 0`으로
이미 위쪽 여백을 가지므로, **바로 위에 오는 `st.divider()`는 대부분 제거 가능** (구분선 여백 +
섹션 라벨 여백의 이중 지출 제거). 정말 시각적으로 별개 블록임을 강조해야 하는 곳(예: 탭 전체를
가르는 큰 구획)만 유지. 탭별 실사 재검토 필요 — 일괄 삭제 아님.

---

## Part D — 이 설계에서 하지 않는 것

- **레이아웃 전면 재설계(컬럼 재배치)**: 점검 결과 `flow.py`의 K2 3단계 진척 등 이미 `st.columns()`로
  적절히 가로 배치된 곳이 많음 — 밀도 문제의 실체는 컬럼 부재가 아니라 B4(블록 간격)·C4(divider)의
  누적 여백이었다. 컬럼 재배치는 이번 라운드 이후 체감을 보고 개별 탭 단위로 판단.
- **다크 모드**: `base`를 바꾸는 건 더 큰 시각적 변화라 이번 스코프에서 제외. `[theme]`가 light/dark
  둘 다 지원하므로 이후 원하면 쉽게 추가 가능(설계상 확장 지점만 남겨둠).
- **15개 탭 전체 리디자인**: 이번 설계는 **인프라(테마·공유 CSS·헤더 컴포넌트)** 까지만 —
  탭별 개별 UX(정보 배치·워크플로 개선)는 별도 스코프.

---

## 구현 순서 (PR 단위)

| PR | 내용 | 규모 | 의존 |
|---|---|---|---|
| PR-1 | `.streamlit/config.toml` 신설 (Part A) | 소 | — |
| PR-2 | `data/themes/hub_ui.css` 신설 + `app.py` `_inject_css()` 교체 (Part B2~B4) | 중 | — |
| PR-3 | `wiki_k2.py`/`inventory.py` 중복 CSS 제거, `hub-*` 클래스로 치환 (Part B3) | 소 | PR-2 |
| PR-4 | `src/ui_kit.py` 신설 + `hub_section()` | 극소 | PR-2 |
| PR-5 | 40곳 원시 헤더 → `hub_section()` 치환 (탭별로 쪼개 진행 가능) | 대(분할 가능) | PR-4 |
| PR-6 | `st.divider()` 28곳 개별 검토·감축 (Part C4) | 중 | PR-5 |

권장 순서: PR-1·PR-2 동시 착수(즉시 전체 화면 인상 개선) → PR-3(중복 제거) → PR-4·PR-5(가장
체감 큰 밀도 개선, 탭 많으니 여러 PR로 쪼개도 됨) → PR-6(마무리 다듬기).

## 테스트 계획

기능 변경이 없는 순수 UI 작업이라 자동 테스트보다 **시각 회귀 확인**이 핵심:

```
1. PR-1·2 적용 전/후 스크린샷: 흐름·위키·데이터·진단툴 4개 탭 (가장 CSS 밀집)
2. 폰트 로드 실패 시나리오: CDN 접속 차단 상태에서 fallback(sans-serif)이 깨지지 않는지
3. PR-3 이후: wiki_k2/inventory 두 탭의 progress bar·stacked bar 시각적 동일성 (색상·높이·글자)
4. PR-5 이후: 각 탭 hub_section() 치환분이 원래 텍스트·이모지 그대로 보존됐는지 (오타 방지)
5. 회귀: 기존 pytest 스위트 전체 실행 — UI 텍스트 문자열을 assert하는 테스트가 있다면 확인
   (hub_section 치환 시 마크다운 문법(#/##)만 사라지고 텍스트 자체는 유지되므로 낮은 위험)
```

## 리스크

| 리스크 | 완화 |
|---|---|
| Pretendard CDN URL이 틀리거나 접속 안 됨 | A3 검증 절차 + A2 자체 호스팅 폰트 대안 마련해둠 |
| `stVerticalBlock`/`element-container` 선택자가 Streamlit 버전업 시 바뀜 | B4에 버전 명시 주석, 업그레이드 시 재확인 항목으로 CHANGELOG에 기록 권장 |
| 40곳 헤더 일괄 치환 중 일부 탭에서 오타·이모지 누락 | PR-5를 탭별로 쪼개 진행 + 치환 전후 텍스트 diff만 확인(로직 변경 없음이라 위험 낮음) |
| `redColor`/`blueColor` 등 config.toml 자동파생색이 기존 수동 alert/warn 색과 미묘히 달라짐 | B2 토큰을 기존 수동값 그대로 유지(자동파생값에 의존하지 않음)로 이미 방지 설계됨 |
| `showWidgetBorder=true`가 일부 위젯에서 과하게 두꺼워 보일 가능성 | 적용 후 육안 확인, 필요시 `false`로 되돌리기 쉬움(설정 한 줄) |

## 부록 — 이 설계가 재사용하는 기존 패턴

- `.wiki-sec`/`.inv-sec`/`.dt-phase-hdr`의 "작은 대문자 라벨" 스타일 → `hub_section()`의 기반
- `.flow-card`의 절제된 8px radius·12-14px padding → `baseRadius`·컴포넌트 패딩 기준값
- 기존 progress bar 그라디언트(`#7ed6a3`→`#5fa8ff`) → 그대로 보존, 토큰화만
- Deck V3 설계서(`DECK_V3_DESIGN.md`)의 accent(`#2f80c4`)·paper-dim(`#f5f7fa`) → hub 테마와 통일,
  PPT 산출물과 hub 화면이 같은 브랜드 색을 쓰게 되는 부수 효과
