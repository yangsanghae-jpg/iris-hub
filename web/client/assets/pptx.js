const HUES = ['--ch-1', '--ch-3', '--ch-4', '--ch-6'];
const STEP_TITLES = [
  { lab: '소스', sub: '' },
  { lab: '확장', sub: 'LLM으로 마크다운 변환' },
  { lab: '설계', sub: '템플릿 · 밀도 · 형식' },
  { lab: '렌더', sub: '결과 리뷰 · 다운로드' },
];
const NEXT_LABELS = ['다음: 확장', '다음: 설계', '다음: 렌더', 'PDF 생성'];

const SAMPLE_MD = `# IRIS 주간 보고
## 2026-06-20

---

## 처리 현황

- documents **1,304** 행
- chunks **5,231** 청크`;

let step = 0;
let busy = false;
let error = null;

const state = {
  sourceMode: 'direct',
  mdText: SAMPLE_MD,
  uploadName: null,
  lang: '한국어',
  pageCount: '자동 (LLM 판단)',
  model: null,
  models: [],
  sources: { archive: [], docs: [] },
  expandResult: null,
  designResult: null,
  renderResult: null,
  template: 'iris (다크)',
};

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || data.detail || `HTTP ${res.status}`);
  return data;
}

// ── 초기 로딩 ──────────────────────────────────────────────────────────
async function init() {
  buildStepper();
  render();
  try {
    const [models, sources] = await Promise.all([
      api('/api/models'),
      api('/api/sources'),
    ]);
    state.models = models.models;
    state.model = models.default && models.models.includes(models.default)
      ? models.default : (models.models[0] || null);
    state.sources = sources;
  } catch (e) {
    error = '초기 로딩 실패: ' + e.message;
  }
  render();
}

// ── 스텝퍼 ─────────────────────────────────────────────────────────────
function buildStepper() {
  const el = document.getElementById('stepper');
  el.innerHTML = STEP_TITLES.map((t, i) => `
    <div class="step" id="step-${i}" style="--hue:var(${HUES[i]});--tint:color-mix(in srgb, var(${HUES[i]}) 8%, white)" onclick="setStep(${i})">
      <div class="num">${i + 1}</div>
      <div><div class="lab">${t.lab}</div><div class="sub" id="step-sub-${i}">${t.sub}</div></div>
    </div>
  `).join('');
}

function stepSubLabels() {
  return [
    state.sourceMode === 'direct' ? `직접 입력 · ${state.mdText.length.toLocaleString()}자`
      : state.sourceMode === 'upload' ? (state.uploadName || '파일 업로드 · 미선택')
      : state.sourceMode,
    state.expandResult ? `${state.expandResult.model} · 완료` : '대기 중',
    state.designResult ? `${state.template} · ${state.pageCount}` : '대기 중',
    state.renderResult ? `${state.renderResult.fmt} 완료` : '대기 중',
  ];
}

// ── 단계 이동 ──────────────────────────────────────────────────────────
function setStep(i) { step = i; error = null; render(); }
async function nextStep() {
  if (busy) return;
  if (step === 1 && !state.expandResult) { await runExpand(); if (error) return; }
  if (step === 2 && !state.designResult) { await runDesign(); if (error) return; }
  if (step === 3) { await runRender('PDF'); return; }
  if (step < 3) { step++; render(); }
}
function prevStep() { if (step > 0) { step--; error = null; render(); } }

// ── ① 소스 ─────────────────────────────────────────────────────────────
function selectSourceMode(mode) {
  state.sourceMode = mode;
  render();
}
async function loadSourceContent(kind, id) {
  try {
    const data = await api(`/api/sources/content?kind=${kind}&id=${id}`);
    state.mdText = data.text;
    render();
  } catch (e) {
    error = '소스 로딩 실패: ' + e.message;
    render();
  }
}
function onFileUpload(input) {
  const file = input.files[0];
  if (!file) return;
  state.uploadName = file.name;
  const reader = new FileReader();
  reader.onload = () => { state.mdText = reader.result; render(); };
  reader.readAsText(file);
}
function onMdTextChange(el) { state.mdText = el.value; }
function onLangChange(v) { state.lang = v; }
function onPageCountChange(v) { state.pageCount = v; }
function onModelChange(v) { state.model = v; }

function targetSlides() {
  if (state.pageCount.startsWith('자동')) return null;
  const n = parseInt(state.pageCount, 10);
  return Number.isFinite(n) ? n : null;
}

// ── ② 확장 ─────────────────────────────────────────────────────────────
async function runExpand() {
  if (!state.mdText.trim()) { error = '①소스에서 원본을 먼저 고르세요.'; render(); return; }
  busy = true; error = null; render();
  try {
    const data = await api('/api/expand', {
      method: 'POST',
      body: JSON.stringify({
        md_text: state.mdText,
        lang: state.lang,
        model: state.model,
        pages: state.pageCount,
        target_slides: targetSlides(),
      }),
    });
    state.expandResult = data;
    state.designResult = null;
    state.renderResult = null;
  } catch (e) {
    error = '확장 실패: ' + e.message;
  }
  busy = false; render();
}

// ── ③ 설계 ─────────────────────────────────────────────────────────────
function selectTemplate(name) { state.template = name; render(); }

async function runDesign() {
  if (!state.expandResult) { error = '②확장을 먼저 실행하세요.'; render(); return; }
  busy = true; error = null; render();
  try {
    const data = await api('/api/design', {
      method: 'POST',
      body: JSON.stringify({ model: state.model, lang: state.lang, target_slides: targetSlides() }),
    });
    state.designResult = data;
    state.renderResult = null;
  } catch (e) {
    error = '설계 실패: ' + e.message;
  }
  busy = false; render();
}

// ── ④ 렌더 ─────────────────────────────────────────────────────────────
async function runRender(fmt) {
  if (!state.designResult) { error = '③설계를 먼저 실행하세요.'; render(); return; }
  busy = true; error = null; render();
  try {
    const data = await api('/api/render', { method: 'POST', body: JSON.stringify({ format: fmt }) });
    state.renderResult = data;
    if (step < 3) step = 3;
  } catch (e) {
    error = '렌더 실패: ' + e.message;
  }
  busy = false; render();
}
function downloadRender() {
  if (state.renderResult) window.location = state.renderResult.download_url;
}

// ── 진행 요약 스트립 ───────────────────────────────────────────────────
function buildProgress() {
  const subs = stepSubLabels();
  const editable = [true, true, true, false];
  const el = document.getElementById('progress-strip');
  el.innerHTML = STEP_TITLES.map((t, i) => `
    <div class="p-item" ${editable[i] ? `onclick="setStep(${i})"` : ''}>
      <div class="p-k"><span>${['①', '②', '③', '④'][i]} ${t.lab}</span>${editable[i] ? `<a onclick="event.stopPropagation();setStep(${i})">편집</a>` : ''}</div>
      <div class="p-v${i > step ? ' muted' : ''}">${esc(subs[i])}</div>
    </div>
  `).join('');
}

// ── 패널 렌더러 (단계별) ───────────────────────────────────────────────
function panelSource() {
  const tabs = [
    ['direct', '직접 입력'],
    ['upload', '파일 업로드'],
    ['archive', `archive · ${state.sources.archive.length}건`],
    ['docs', `docs/system · ${state.sources.docs.length}건`],
  ];
  const tabsHtml = tabs.map(([mode, lab]) =>
    `<button class="${state.sourceMode === mode ? 'on' : ''}" onclick="selectSourceMode('${mode}')">${esc(lab)}</button>`
  ).join('');

  let body = '';
  if (state.sourceMode === 'direct') {
    body = `<textarea rows="13" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>`;
  } else if (state.sourceMode === 'upload') {
    body = `<input type="file" accept=".md,.txt" onchange="onFileUpload(this)" />
      ${state.uploadName ? `<div class="expand-sub" style="margin-top:10px">불러온 파일: ${esc(state.uploadName)}</div>
      <textarea rows="10" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>` : ''}`;
  } else {
    const items = state.sources[state.sourceMode] || [];
    if (!items.length) {
      body = `<div class="expand-note">사용 가능한 ${esc(state.sourceMode)} 자료가 없습니다.</div>`;
    } else {
      body = `<div style="display:flex;flex-direction:column;gap:6px;max-height:280px;overflow:auto">
        ${items.map((it) => `<button style="text-align:left" onclick="loadSourceContent('${state.sourceMode}', ${it.id})">${esc(it.label)}</button>`).join('')}
      </div>
      <textarea rows="8" style="margin-top:10px" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>`;
    }
  }

  return `<h3>① 소스 선택</h3>
    <div class="expand-note">PPT로 만들 원본을 고릅니다. 직접 입력하거나, 파일을 올리거나, archive · docs/system에 이미 있는 자료를 골라도 됩니다. 오른쪽에서 정한 언어 · 페이지 수 · 모델이 다음 단계 LLM 변환에 그대로 쓰입니다.</div>
    <div class="src-tabs">${tabsHtml}</div>
    ${body}`;
}

function panelExpand() {
  if (!state.mdText.trim()) {
    return `<h3>② 확장 · LLM 변환</h3><div class="expand-note">①소스에서 원본을 먼저 고르세요.</div>`;
  }
  const r = state.expandResult;
  const status = r
    ? `<div class="llm-status"><span class="dot done"></span>${esc(r.model)} · 변환 완료 · ${r.elapsed.toFixed(1)}초 · 소스 ${r.in.toLocaleString()}자 → ${r.out.toLocaleString()}자</div>`
    : `<div class="llm-status"><span class="dot" style="background:#f59e0b"></span>아직 확장되지 않음</div>`;
  const btnLabel = busy ? '<span class="spin"></span>처리 중…' : (r ? '🔁 재생성' : '▶ 확장 시작');
  return `<h3>② 확장 · LLM 변환</h3>
    <div class="expand-note">①에서 정한 언어 · 페이지 수 · 모델로 LLM이 소스를 읽고, 슬라이드용으로 더 풍부하게 재구조화한 마크다운을 생성합니다. 이 결과가 ③설계 단계의 입력이 됩니다.</div>
    <div class="llm-row">${status}<button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runExpand()">${btnLabel}</button></div>
    ${r ? `<div class="expand-sub">출력 · LLM이 생성한 슬라이드용 마크다운 (③설계 입력)</div>
    <div class="expand-box accent">${esc(r.md.slice(0, 4000))}${r.md.length > 4000 ? '…' : ''}</div>` : ''}`;
}

const TEMPLATES = [
  ['iris (다크)', '#111827'], ['iris (라이트)', '#f3f4f6'], ['미니멀', '#e5e7eb'],
];

function panelDesign() {
  if (!state.expandResult) {
    return `<h3>③ 변환 설정</h3><div class="expand-note">②확장을 먼저 실행하세요.</div>`;
  }
  const tplGrid = TEMPLATES.map(([name, color]) => `
    <div class="tpl-card ${state.template === name ? 'on' : ''}" onclick="selectTemplate('${name}')">
      <div class="tpl-thumb" style="background:${color}"></div>
      <div class="tpl-name">${esc(name)}</div>
    </div>`).join('');

  const d = state.designResult;
  const statusHtml = d
    ? `<div class="llm-status"><span class="dot done"></span>설계 완료 · ${d.page_count}페이지</div>`
    : `<div class="llm-status"><span class="dot" style="background:#f59e0b"></span>아직 설계되지 않음</div>`;
  const btnLabel = busy ? '<span class="spin"></span>처리 중…' : (d ? '🔁 재설계' : '▶ 설계 실행');

  return `<h3>③ 변환 설정</h3>
    <div class="expand-note">②에서 나온 마크다운을 슬라이드로 렌더링합니다. 페이지별 본문형식에 맞는 레이아웃을 LLM이 골라 템플릿에 맞춰 그려냅니다.</div>
    <div class="tpl-section">
      <label>템플릿 <span class="hint" style="font-weight:500;color:var(--muted)">(선택만 반영 — 실제 렌더 스타일 배선은 후속 작업)</span></label>
      <div class="tpl-grid">${tplGrid}</div>
    </div>
    <div class="llm-row">${statusHtml}<button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runDesign()">${btnLabel}</button></div>
    ${d ? `<div class="expand-sub">설계된 슬라이드 (${d.page_count}장)</div>
    <div class="expand-box">${d.slides.map((s, i) => `${i + 1}. [${esc(s.pattern)}] ${esc(s.title)}`).join('\n')}</div>` : ''}`;
}

function panelRender() {
  if (!state.designResult) {
    return `<h3>④ 렌더 · 결과 리뷰</h3><div class="expand-note">아직 설계된 슬라이드가 없습니다. ③설계 단계를 먼저 실행하세요.</div>`;
  }
  const r = state.renderResult;
  const statusHtml = r
    ? `<div class="render-status"><span class="dot"></span>${r.fmt} 생성 완료 · ${r.page_count}페이지 · ${r.size_kb.toFixed(1)}KB</div>`
    : `<div class="render-status"><span class="dot pending"></span>아직 렌더되지 않음 — 아래 버튼을 눌러주세요.</div>`;
  const cards = state.designResult.slides.map((s, i) => `
    <div class="render-card">
      <div class="render-thumb">
        <div class="render-thumb-title">${esc(s.title)}</div>
        <div class="render-thumb-sub">${esc(s.pattern)}</div>
      </div>
      <div class="render-meta"><span>page ${i + 1}</span></div>
    </div>`).join('');

  return `<h3>④ 렌더 · 결과 리뷰</h3>
    <div class="expand-note">설계된 페이지를 확인하고, PDF 또는 PPTX로 내보냅니다.</div>
    ${statusHtml}
    <div class="render-grid">${cards}</div>
    <div class="render-actions">
      <button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runRender('PDF')">${busy ? '<span class="spin"></span>렌더 중…' : '🔁 PDF로 렌더'}</button>
      <button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runRender('PPTX')">PPTX로 렌더</button>
      <button class="btn-primary btn-sm" ${r ? '' : 'disabled'} onclick="downloadRender()">⬇ 다운로드</button>
    </div>`;
}

const PANEL_FNS = [panelSource, panelExpand, panelDesign, panelRender];

// ── 사이드 렌더러 ──────────────────────────────────────────────────────
function sideGenSettings() {
  const modelOpts = state.models.length
    ? state.models.map((m) => `<option ${m === state.model ? 'selected' : ''}>${esc(m)}</option>`).join('')
    : '<option>모델 없음</option>';
  return `<h4>생성 설정</h4>
    <div class="field">
      <label>언어</label>
      <select onchange="onLangChange(this.value)">
        ${['한국어', 'English', '중국어'].map((l) => `<option ${l === state.lang ? 'selected' : ''}>${l}</option>`).join('')}
      </select>
    </div>
    <div class="field">
      <label>페이지 수</label>
      <select onchange="onPageCountChange(this.value)">
        ${['자동 (LLM 판단)', '5장', '10장', '15장'].map((p) => `<option ${p === state.pageCount ? 'selected' : ''}>${p}</option>`).join('')}
      </select>
    </div>
    <div class="field">
      <label>LLM 모델 ${state.models.length ? `(${state.models.length}개 설치)` : ''}</label>
      <select onchange="onModelChange(this.value)">${modelOpts}</select>
    </div>
    <div class="src-settings-note">여기서 정한 값이 ②확장의 LLM 변환에 그대로 적용됩니다.</div>`;
}

const SIDE_FNS = [sideGenSettings, sideGenSettings, sideGenSettings, sideGenSettings];

// ── 메인 렌더 ──────────────────────────────────────────────────────────
function render() {
  document.getElementById('panel').innerHTML = PANEL_FNS[step]();
  document.getElementById('side').innerHTML = SIDE_FNS[step]();
  document.getElementById('error-box').innerHTML = error ? `<div class="err-box">${esc(error)}</div>` : '';

  for (let i = 0; i < 4; i++) {
    const s = document.getElementById('step-' + i);
    s.classList.remove('done', 'active');
    if (i < step) s.classList.add('done');
    if (i === step) s.classList.add('active');
    document.getElementById('step-sub-' + i).textContent = stepSubLabels()[i];
  }
  document.getElementById('prev-btn').style.visibility = step === 0 ? 'hidden' : 'visible';
  document.getElementById('next-btn').textContent = busy ? '처리 중…' : NEXT_LABELS[step];
  document.getElementById('next-btn').disabled = busy;
  buildProgress();
}

init();
