const STEP_LABELS = [
  '소스', '확장', '디자인', '렌더',
];
const STEP_TITLES = STEP_LABELS.map((lab) => ({ lab }));
const TEXT_UPLOAD_EXTENSIONS = ['.md', '.txt'];
const DEFAULT_UPLOAD_EXTENSIONS = ['.md', '.txt', '.pdf', '.docx', '.pptx', '.xlsx'];
let MAX_UPLOAD_BYTES = 20 * 1024 * 1024; // fallback — /api/ppt/source/formats가 있으면 그 값으로 교체
const DENSITY_OPTS = [
  ['spacious', '여유'],
  ['standard', '보통'],
  ['dense', '풍부'],
];
const PAGE_POS_OPTS = [
  ['bottom-left', '좌측 하단'],
  ['bottom-center', '중앙 하단'],
  ['bottom-right', '우측 하단'],
];

const SAMPLE_MD = `# IRIS 주간 보고
## 2026-06-20

---

## 처리 현황

- documents **1,304** 행
- chunks **5,231** 청크`;

let step = 0;
let busy = false;
let error = null;
let designStale = false;

const state = {
  sourceMode: 'direct',
  mdText: SAMPLE_MD,
  uploadName: null,
  uploadSize: null,
  uploadBusy: false,
  sourceFormats: {
    extensions: DEFAULT_UPLOAD_EXTENSIONS,
    accept: DEFAULT_UPLOAD_EXTENSIONS.join(','),
    max_bytes: MAX_UPLOAD_BYTES,
    label: '',
  },
  lang: '한국어',
  pageCount: '자동 (LLM 판단)',
  model: null,
  models: [],
  sources: { archive: [], docs: [], sources: [] },
  templates: [],
  titleFonts: [],
  defaultTemplateId: 'clean-light',
  expandResult: null,
  designResult: null,
  renderResult: null,
  outputFormat: 'PDF',
  saveDisk: false,
  useOtherDesignModel: false,
  designModel: null,
  templateId: 'clean-light',
  masterStyle: { titleFont: null, titleSizePt: null, titleColor: null },
  pageNumber: { enabled: true, position: 'bottom-right' },
  density: 'standard',
  previewId: null,
  previews: [],
  previewBusy: false,
  previewError: null,
  renderReview: {
    selectedPages: [], // 0-based slide_index
    issueTypes: [],
    otherNote: '',
  },
};

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function nextLabels() {
  return ['다음: 확장', '다음: 설계', '다음: 렌더', `${state.outputFormat} 생성`];
}

function effectiveDesignModel() {
  if (state.useOtherDesignModel && state.designModel) return state.designModel;
  return state.model;
}

function selectedTemplate() {
  return state.templates.find((t) => t.id === state.templateId) || null;
}

function resolvedTitleFont() {
  if (state.masterStyle.titleFont) return state.masterStyle.titleFont;
  return selectedTemplate()?.defaults?.title_font || 'Pretendard';
}
function resolvedTitleSize() {
  if (state.masterStyle.titleSizePt != null) return state.masterStyle.titleSizePt;
  return selectedTemplate()?.defaults?.title_size_pt || 32;
}
function resolvedTitleColor() {
  if (state.masterStyle.titleColor) return state.masterStyle.titleColor;
  return selectedTemplate()?.defaults?.title_color || '#FFFFFF';
}

function invalidateDesign() {
  state.designResult = null;
  state.renderResult = null;
  state.previews = [];
  state.previewId = null;
  state.previewError = null;
  resetReviewSelection();
  designStale = false;
}
function invalidateRender() {
  state.renderResult = null;
  // 스타일 변경 시 기존 프리뷰는 stale — ④ 진입/재빌드 시 갱신
  state.previews = [];
  state.previewId = null;
}
function markDesignStale() {
  if (state.designResult) designStale = true;
  state.renderResult = null;
  state.previews = [];
  state.previewId = null;
}

function stylePayload() {
  return {
    template_id: state.templateId,
    master_style: {
      title_font: state.masterStyle.titleFont,
      title_size_pt: state.masterStyle.titleSizePt,
      title_color: state.masterStyle.titleColor,
    },
    page_number: {
      enabled: state.pageNumber.enabled,
      position: state.pageNumber.position,
    },
  };
}

function resetReviewSelection() {
  state.renderReview.selectedPages = [];
  state.renderReview.issueTypes = [];
  state.renderReview.otherNote = '';
}

function toggleSelectedPage(selected, slideIndex) {
  const set = new Set(selected);
  if (set.has(slideIndex)) set.delete(slideIndex);
  else set.add(slideIndex);
  return [...set].sort((a, b) => a - b);
}

function toggleIssueType(types, typeId) {
  const set = new Set(types);
  if (set.has(typeId)) set.delete(typeId);
  else set.add(typeId);
  return [...set];
}

async function buildPreviews() {
  if (!state.designResult || designStale) return;
  state.previewBusy = true;
  state.previewError = null;
  render();
  try {
    const data = await api('/api/preview/build', {
      method: 'POST',
      body: JSON.stringify(stylePayload()),
    });
    state.previewId = data.preview_id;
    state.previews = data.previews || [];
    resetReviewSelection();
  } catch (e) {
    state.previewError = e.message;
    state.previews = [];
    state.previewId = null;
  }
  state.previewBusy = false;
  render();
  requestAnimationFrame(scalePreviewFrames);
}

function scalePreviewFrames() {
  document.querySelectorAll('.render-slide-stage').forEach((stage) => {
    const scaler = stage.querySelector('.render-slide-scaler');
    if (!scaler) return;
    const w = stage.clientWidth || 1;
    const scale = w / 1920;
    scaler.style.transform = `scale(${scale})`;
    stage.style.height = `${1080 * scale}px`;
  });
}

function buildStatusStrip() {
  const modeLabel = {
    direct: '직접 입력',
    upload: '파일 업로드',
    archive: 'archive',
    docs: 'docs',
  }[state.sourceMode] || state.sourceMode;
  const srcReady = sourceModeHasContent();
  const srcDetail = state.sourceMode === 'direct'
    ? `${state.mdText.length.toLocaleString()}자`
    : state.sourceMode === 'upload'
      ? (state.uploadName || '미선택')
      : state.sourceMode === 'archive'
        ? `${state.sources.archive.length}건`
        : `${state.sources.docs.length}건`;
  const tpl = selectedTemplate()?.name || state.templateId || '—';
  const stepLab = STEP_LABELS[step] || '—';
  const out = state.renderResult
    ? `${state.renderResult.fmt} 완료`
    : `${state.outputFormat} 대기`;

  const el = document.getElementById('ppt-status-strip');
  if (!el) return;
  el.innerHTML = `
    단계 <strong>${step + 1}/4 ${esc(stepLab)}</strong> ·
    소스 <strong>${esc(modeLabel)}</strong>${srcReady ? ` · ${esc(srcDetail)}` : ' · 선택 대기'} ·
    언어 <strong>${esc(state.lang)}</strong> ·
    템플릿 <strong>${esc(tpl)}</strong> ·
    내보내기 <strong>${esc(out)}</strong>`;
}

/** @deprecated alias — 호출부 호환 */
function buildKPI() { buildStatusStrip(); }

function sourceModeHasContent() {
  if (state.sourceMode === 'direct' && state.mdText) return true;
  if (state.sourceMode === 'upload' && state.uploadName) return true;
  return false;
}

window.addEventListener('resize', () => {
  if (step === 3) scalePreviewFrames();
});

function onPageCheck(slideIndex, checked) {
  const set = new Set(state.renderReview.selectedPages);
  if (checked) set.add(slideIndex);
  else set.delete(slideIndex);
  state.renderReview.selectedPages = [...set].sort((a, b) => a - b);
  render();
  requestAnimationFrame(scalePreviewFrames);
}

function togglePageCard(slideIndex) {
  state.renderReview.selectedPages = toggleSelectedPage(
    state.renderReview.selectedPages, slideIndex,
  );
  render();
  requestAnimationFrame(scalePreviewFrames);
}

function selectAllPages() {
  state.renderReview.selectedPages = (state.previews || []).map((p) => p.slide_index);
  render();
  requestAnimationFrame(scalePreviewFrames);
}

function clearAllPages() {
  state.renderReview.selectedPages = [];
  render();
  requestAnimationFrame(scalePreviewFrames);
}

function onIssueTypeToggle(typeId) {
  state.renderReview.issueTypes = toggleIssueType(state.renderReview.issueTypes, typeId);
  render();
}

function onOtherNoteChange(v) {
  state.renderReview.otherNote = v;
}

function reviewHint() {
  const n = state.renderReview.selectedPages.length;
  const issues = state.renderReview.issueTypes;
  if (!n) return '문제가 있는 페이지를 먼저 선택하세요.';
  if (!issues.length) return '문제 유형을 하나 이상 선택하세요.';
  const labels = {
    language: '언어 오류',
    'content-density': '내용 밀도 오류',
    'text-overflow': '글자 겹침 또는 잘림',
    layout: '페이지 형식·레이아웃 오류',
    other: '기타',
  };
  const issueLab = issues.map((t) => labels[t] || t).join(' · ');
  return `선택한 ${n}개 페이지의 ${issueLab} 문제를 교정합니다. (교정 엔진은 준비 중)`;
}

async function api(path, opts) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.error || data.detail;
    const msg = typeof detail === 'string'
      ? detail
      : (Array.isArray(detail) ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ') : null);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return data;
}

// api()와 달리 Content-Type을 강제하지 않는다 — multipart/form-data 경계는
// 브라우저가 FormData 전송 시 자동으로 설정해야 하므로, 여기서 헤더를 지정하면 깨진다.
async function apiUpload(path, formData) {
  const res = await fetch(path, { method: 'POST', body: formData });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = data.error || data.detail;
    const msg = typeof detail === 'string'
      ? detail
      : (Array.isArray(detail) ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ') : null);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return data;
}

async function init() {
  buildStepper();
  render();
  try {
    const [models, sources, templates, formats] = await Promise.all([
      api('/api/models'),
      api('/api/sources'),
      api('/api/ppt/templates'),
      api('/api/ppt/source/formats').catch(() => null),
    ]);
    state.models = models.models;
    if (formats && Array.isArray(formats.extensions)) {
      state.sourceFormats = formats;
      if (formats.max_bytes) MAX_UPLOAD_BYTES = formats.max_bytes;
    }
    state.model = models.default && models.models.includes(models.default)
      ? models.default : (models.models[0] || null);
    state.designModel = state.model;

    // Handle both 8766 source structure ({archive, docs}) and V3.1 source structure ({sources, archive, docs, count})
    if (sources.archive && sources.docs) {
      state.sources = sources;
    } else if (sources.sources && sources.archive) {
      state.sources = { archive: sources.archive, docs: sources.docs, sources: sources.sources };
    } else {
      state.sources = { archive: [], docs: [], sources: [] };
    }

    state.templates = templates.templates || [];
    state.titleFonts = templates.title_fonts || [];
    state.defaultTemplateId = templates.default || 'clean-light';
    state.templateId = state.defaultTemplateId;
  } catch (e) {
    error = '초기 로딩 실패: ' + e.message;
  }
  buildKPI();
  render();
}

function buildStepper() {
  const el = document.getElementById('stepper');
  el.innerHTML = STEP_LABELS.map((lab, i) => `
    <div class="ppt-step" id="step-${i}" onclick="setStep(${i})">${i + 1}. ${esc(lab)}</div>
  `).join('');
}

function densityLabel() {
  return (DENSITY_OPTS.find(([k]) => k === state.density) || [])[1] || state.density;
}

function stepSubLabels() {
  const pages = state.pageCount.startsWith('자동') ? '자동' : state.pageCount;
  const tpl = selectedTemplate()?.name || state.templateId;
  const designModel = state.designResult?.model || effectiveDesignModel();
  return [
    state.sourceMode === 'direct' ? `직접 입력 · ${state.mdText.length.toLocaleString()}자`
      : state.sourceMode === 'upload' ? (state.uploadName || '파일 업로드 · 미선택')
      : state.sourceMode,
    state.expandResult ? `${state.expandResult.model} · 완료` : '대기 중',
    state.designResult
      ? `${tpl} · ${densityLabel()} · ${designModel || '—'}`
      : `${tpl} · ${pages} · ${state.outputFormat}`,
    state.renderResult ? `${state.renderResult.fmt} 완료` : '대기 중',
  ];
}

function setStep(i) {
  step = i;
  error = null;
  render();
  if (i === 3 && state.designResult && !designStale && !state.previews.length && !state.previewBusy) {
    buildPreviews();
  }
}
async function nextStep() {
  if (busy) return;
  if (step === 1 && !state.expandResult) { await runExpand(); if (error) return; }
  if (step === 2 && (!state.designResult || designStale)) { await runDesign(); if (error) return; }
  if (step === 3) { await runRender(state.outputFormat); return; }
  if (step < 3) {
    step++;
    render();
    if (step === 3 && state.designResult && !designStale && !state.previews.length) {
      await buildPreviews();
    }
  }
}
function prevStep() { if (step > 0) { step--; error = null; render(); } }

function selectSourceMode(mode) {
  state.sourceMode = mode;
  // 소스 모드/소스 변경 → expandResult 및 설계 결과 전체 초기화
  state.expandResult = null;
  state.renderResult = null;
  state.previews = [];
  state.previewId = null;
  state.mdText = '';
  designStale = false;
  resetReviewSelection();
  render();
}
async function loadSourceContent(kind, id) {
  try {
    const data = await api(`/api/sources/content?kind=${kind}&id=${id}`);
    state.mdText = data.text;
    state.expandResult = null;
    invalidateDesign();
    render();
  } catch (e) {
    error = '소스 로딩 실패: ' + e.message;
    render();
  }
}

function clearUpload() {
  state.uploadName = null;
  state.uploadSize = null;
  state.mdText = '';
  state.expandResult = null;
  invalidateDesign();
  render();
}

function uploadExtOf(name) {
  const lower = (name || '').toLowerCase();
  const idx = lower.lastIndexOf('.');
  return idx >= 0 ? lower.slice(idx) : '';
}

function allowedUploadExtensions() {
  return (state.sourceFormats && state.sourceFormats.extensions) || DEFAULT_UPLOAD_EXTENSIONS;
}

function uploadAccept() {
  return (state.sourceFormats && state.sourceFormats.accept) || allowedUploadExtensions().join(',');
}

function uploadLabel() {
  if (state.sourceFormats && state.sourceFormats.label) return state.sourceFormats.label;
  const mb = Math.round(MAX_UPLOAD_BYTES / 1024 / 1024);
  return `${allowedUploadExtensions().join(' · ')} · 최대 ${mb}MB`;
}

async function applyUploadedFile(file) {
  if (!file) return;
  const name = file.name || '';
  const ext = uploadExtOf(name);
  const allowed = allowedUploadExtensions();
  if (!allowed.includes(ext)) {
    error = `지원 확장자는 ${allowed.join(', ')} 입니다.`;
    render();
    return;
  }
  if (file.size <= 0) {
    error = '빈 파일은 업로드할 수 없습니다.';
    render();
    return;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    error = `파일이 너무 큽니다 (최대 ${Math.round(MAX_UPLOAD_BYTES / 1024 / 1024)}MB).`;
    render();
    return;
  }

  if (TEXT_UPLOAD_EXTENSIONS.includes(ext)) {
    const reader = new FileReader();
    reader.onload = () => {
      state.uploadName = name;
      state.uploadSize = file.size;
      state.mdText = String(reader.result || '');
      state.sourceMode = 'upload';
      state.expandResult = null;
      invalidateDesign();
      error = null;
      render();
    };
    reader.onerror = () => {
      error = '파일을 읽지 못했습니다.';
      render();
    };
    reader.readAsText(file);
    return;
  }

  // 바이너리 포맷(.pdf/.docx/.pptx/.xlsx) — 서버 변환 경유
  state.uploadBusy = true;
  error = null;
  render();
  try {
    const formData = new FormData();
    formData.append('file', file, name);
    const data = await apiUpload('/api/ppt/source/convert', formData);
    state.uploadName = name;
    state.uploadSize = file.size;
    state.mdText = data.text || '';
    state.sourceMode = 'upload';
    state.expandResult = null;
    invalidateDesign();
    error = null;
  } catch (e) {
    error = '파일 변환 실패: ' + e.message;
  }
  state.uploadBusy = false;
  render();
}

function onFileUpload(input) {
  const file = input.files && input.files[0];
  applyUploadedFile(file);
  input.value = '';
}

function onDropzoneKey(ev) {
  if (ev.key === 'Enter' || ev.key === ' ') {
    ev.preventDefault();
    document.getElementById('file-input')?.click();
  }
}
function onDragOver(ev) {
  ev.preventDefault();
  ev.currentTarget.classList.add('dragover');
}
function onDragLeave(ev) {
  ev.currentTarget.classList.remove('dragover');
}
function onDrop(ev) {
  ev.preventDefault();
  ev.currentTarget.classList.remove('dragover');
  const file = ev.dataTransfer?.files?.[0];
  applyUploadedFile(file);
}

function onMdTextChange(el) { state.mdText = el.value; }
function onLangChange(v) { state.lang = v; invalidateDesign(); render(); }
function onPageCountChange(v) { state.pageCount = v; invalidateDesign(); render(); }
function onModelChange(v) {
  state.model = v;
  if (!state.useOtherDesignModel) state.designModel = v;
  invalidateDesign();
  render();
}
function targetSlides() {
  if (state.pageCount.startsWith('자동')) return null;
  const n = parseInt(state.pageCount, 10);
  return Number.isFinite(n) ? n : null;
}

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
    invalidateDesign();
  } catch (e) {
    error = '확장 실패: ' + e.message;
  }
  busy = false; render();
}

function onOutputFormatChange(value) {
  state.outputFormat = value;
  invalidateRender();
  render();
}
function setSaveDisk(on) { state.saveDisk = !!on; render(); }
function setUseOtherDesignModel(on) {
  state.useOtherDesignModel = !!on;
  if (on && !state.designModel) state.designModel = state.model;
  markDesignStale();
  render();
}
function onDesignModelChange(v) {
  state.designModel = v;
  markDesignStale();
  render();
}
function selectTemplate(id) {
  state.templateId = id;
  invalidateRender();
  render();
}
function onDensityChange(v) {
  state.density = v;
  markDesignStale();
  render();
}
function onTitleFontChange(v) {
  state.masterStyle.titleFont = v === '' ? null : v;
  invalidateRender();
  render();
}
function onTitleSizeChange(v) {
  state.masterStyle.titleSizePt = v === '' ? null : parseInt(v, 10);
  invalidateRender();
  render();
}
function onTitleColorChange(v) {
  state.masterStyle.titleColor = v === '' ? null : v;
  invalidateRender();
  render();
}
function setPageNumberEnabled(on) {
  state.pageNumber.enabled = !!on;
  invalidateRender();
  render();
}
function onPagePositionChange(v) {
  state.pageNumber.position = v;
  invalidateRender();
  render();
}
function resetMasterStyle() {
  state.masterStyle = { titleFont: null, titleSizePt: null, titleColor: null };
  invalidateRender();
  render();
}

function toggleSwitch(on, setterFn, opts) {
  // 네이티브 <input type="checkbox"> 기반 스위치. 이전엔 ON/OFF 버튼 2개를
  // 직접 그려 재렌더 시 방향 표시가 겹쳐 보이는 등 문제가 있어, 상태·포커스·
  // 키보드 처리를 브라우저가 알아서 하는 네이티브 컨트롤로 교체했다.
  const disabled = opts && opts.disabled ? 'disabled' : '';
  const onchange = disabled ? '' : `onchange="${setterFn}(this.checked)"`;
  return `<label class="switch ${disabled ? 'is-disabled' : ''}">
    <input type="checkbox" ${on ? 'checked' : ''} ${disabled} ${onchange} />
    <span class="switch-track"><span class="switch-thumb"></span></span>
  </label>`;
}

async function runDesign() {
  if (!state.expandResult) { error = '②확장을 먼저 실행하세요.'; render(); return; }
  busy = true; error = null; render();
  try {
    const data = await api('/api/design', {
      method: 'POST',
      body: JSON.stringify({
        model: effectiveDesignModel(),
        lang: state.lang,
        target_slides: targetSlides(),
        density: state.density,
      }),
    });
    state.designResult = data;
    state.renderResult = null;
    state.previews = [];
    state.previewId = null;
    designStale = false;
  } catch (e) {
    error = '설계 실패: ' + e.message;
  }
  busy = false; render();
}

function renderAs(fmt) {
  state.outputFormat = fmt;
  return runRender(fmt);
}

async function runRender(fmt) {
  if (!state.designResult || designStale) {
    error = designStale
      ? '밀도 또는 설계 모델이 변경되었습니다. ③설계를 다시 실행하세요.'
      : '③설계를 먼저 실행하세요.';
    render();
    return;
  }
  busy = true; error = null; render();
  try {
    const data = await api('/api/render', {
      method: 'POST',
      body: JSON.stringify({
        format: fmt,
        save_disk: state.saveDisk,
        ...stylePayload(),
      }),
    });
    state.renderResult = data;
    state.outputFormat = data.fmt || fmt;
    if (data.previews && data.previews.length) {
      state.previews = data.previews;
      state.previewId = data.preview_id;
      resetReviewSelection();
    }
    if (step < 3) step = 3;
  } catch (e) {
    error = '렌더 실패: ' + e.message;
  }
  busy = false; render();
  requestAnimationFrame(scalePreviewFrames);
}
function downloadRender() {
  if (state.renderResult) window.location = state.renderResult.download_url;
}

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

  // archive와 docs 모드에서 source 데이터 출처에 맞게 항목 선택
  const archiveItems = state.sources.archive || [];
  const docsItems = state.sources.docs || [];

  let body = '';
  if (state.sourceMode === 'direct') {
    body = `<textarea rows="13" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>`;
  } else if (state.sourceMode === 'upload') {
    const sizeLab = state.uploadSize != null
      ? ` · ${(state.uploadSize / 1024).toFixed(1)} KB` : '';
    body = `
      <div class="dropzone ${state.uploadBusy ? 'is-busy' : ''}" id="dropzone" role="button" tabindex="0"
           aria-label="문서 파일 업로드"
           onclick="${state.uploadBusy ? '' : "document.getElementById('file-input').click()"}"
           onkeydown="onDropzoneKey(event)"
           ondragover="onDragOver(event)" ondragleave="onDragLeave(event)" ondrop="onDrop(event)">
        <div class="dz-title">${state.uploadBusy ? '<span class="spin"></span>파일 변환 중…' : '파일을 여기에 놓거나 클릭하여 선택'}</div>
        <div class="dz-sub">${esc(uploadLabel())}</div>
      </div>
      <input id="file-input" type="file" accept="${esc(uploadAccept())}" hidden ${state.uploadBusy ? 'disabled' : ''} onchange="onFileUpload(this)" />
      ${state.uploadName ? `<div class="upload-meta">
        <span>선택: <strong>${esc(state.uploadName)}</strong>${sizeLab}</span>
        <button type="button" class="btn-ghost btn-sm" ${state.uploadBusy ? 'disabled' : ''} onclick="clearUpload()">제거</button>
      </div>
      <textarea rows="10" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>` : ''}`;
  } else {
    const items = state.sourceMode === 'archive' ? archiveItems : docsItems;
    if (!items.length) {
      body = `<div class="expand-note">사용 가능한 ${esc(state.sourceMode)} 자료가 없습니다.</div>`;
    } else {
      body = `<div style="display:flex;flex-direction:column;gap:6px;max-height:280px;overflow:auto">
        ${items.map((it) => `<button style="text-align:left" onclick="loadSourceContent('${state.sourceMode}', ${it.id})">${esc(it.label)}</button>`).join('')}
      </div>
      <textarea rows="8" style="margin-top:10px" oninput="onMdTextChange(this)">${esc(state.mdText)}</textarea>`;
    }
  }

  return `<div class="card-h">
      <span class="card-num">SRC</span>
      <span class="card-ttl">소스 선택</span>
    </div>
    <div class="card-body">
      <div class="expand-note">PPT로 만들 원본을 고릅니다. 직접 입력·드래그앤드롭 업로드·archive/docs 선택이 가능합니다.</div>
      <div class="ppt-src-tabs">${tabsHtml}</div>
      ${body}
    </div>`;
}

function panelExpand() {
  if (!state.mdText.trim()) {
    return `<div class="card-h">
      <span class="card-num">EXP</span>
      <span class="card-ttl">확장 · LLM 변환</span>
    </div>
    <div class="card-body"><div class="expand-note">①소스에서 원본을 먼저 고르세요.</div>`;
  }
  const r = state.expandResult;
  const status = r
    ? `<div class="llm-status"><span class="dot done"></span>${esc(r.model)} · 변환 완료 · ${r.elapsed.toFixed(1)}초 · 소스 ${r.in.toLocaleString()}자 → ${r.out.toLocaleString()}자</div>`
    : `<div class="llm-status"><span class="dot" style="background:#f59e0b"></span>아직 확장되지 않음</div>`;
  const btnLabel = busy ? '<span class="spin"></span>처리 중…' : (r ? '🔁 재생성' : '▶ 확장 시작');
  return `<div class="card-h">
      <span class="card-num">EXP</span>
      <span class="card-ttl">확장 · LLM 변환</span>
    </div>
    <div class="card-body">
    <div class="expand-note">언어·페이지 수·모델로 LLM이 소스를 슬라이드용 마크다운으로 재구조화합니다.</div>
    <div class="llm-row">${status}<button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runExpand()">${btnLabel}</button></div>
    ${r ? `<div class="expand-sub">출력 · LLM이 생성한 슬라이드용 마크다운</div>
    <div class="expand-box accent">${esc(r.md.slice(0, 4000))}${r.md.length > 4000 ? '…' : ''}</div>` : ''}`;
}

function panelDesign() {
  if (!state.expandResult) {
    return `<div class="card-h">
      <span class="card-num">DES</span>
      <span class="card-ttl">디자인 설정</span>
    </div>
    <div class="card-body"><div class="expand-note">②확장을 먼저 실행하세요.</div>`;
  }

  const tplGrid = (state.templates.length ? state.templates : []).map((t) => {
    const prev = t.preview || {};
    return `<div class="tpl-card ${state.templateId === t.id ? 'on' : ''}" role="button" tabindex="0"
      aria-pressed="${state.templateId === t.id ? 'true' : 'false'}"
      onclick="selectTemplate('${esc(t.id)}')"
      onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectTemplate('${esc(t.id)}')}">
      <div class="tpl-thumb" style="background="${esc(prev.background || '#111827')}"></div>
      <div class="tpl-name">${esc(t.name)}</div>
      <div class="tpl-desc">${esc(t.description || '')}</div>
    </div>`;
  }).join('');

  const fontOpts = [`<option value="">템플릿 기본값 (${esc(resolvedTitleFont())})</option>`]
    .concat((state.titleFonts || []).map((f) =>
      `<option value="${esc(f)}" ${state.masterStyle.titleFont === f ? 'selected' : ''}>${esc(f)}</option>`)).join('');
  const sizeOpts = [`<option value="">템플릿 기본값 (${resolvedTitleSize()}pt)</option>`]
    .concat([24, 28, 32, 34, 36, 40, 48].map((n) =>
      `<option value="${n}" ${state.masterStyle.titleSizePt === n ? 'selected' : ''}>${n}pt</option>`)).join('');

  const designModelOpts = state.models.length
    ? state.models.map((m) => `<option ${m === (state.designModel || state.model) ? 'selected' : ''}>${esc(m)}</option>`).join('')
    : '<option>모델 없음</option>';

  const d = state.designResult;
  const usedModel = d?.model || effectiveDesignModel();
  const statusHtml = designStale
    ? `<div class="llm-status"><span class="dot" style="background:#f59e0b"></span>밀도/모델 변경 — 재설계가 필요합니다</div>`
    : (d
      ? `<div class="llm-status"><span class="dot done"></span>설계 완료 · ${esc(usedModel)} · ${d.page_count}페이지 · ${esc(d.density || state.density)}</div>`
      : `<div class="llm-status"><span class="dot" style="background:#f59e0b"></span>아직 설계되지 않음</div>`);
  const btnLabel = busy ? '<span class="spin"></span>처리 중…' : ((d && !designStale) ? '🔁 재설계' : '▶ 설계 실행');

  return `<div class="card-h">
      <span class="card-num">DES</span>
      <span class="card-ttl">디자인 설정</span>
    </div>
    <div class="card-body">
    <div class="expand-note">선택한 템플릿·제목 스타일·페이지 번호는 PDF와 PPTX에 동일하게 적용됩니다. 레이아웃 밀도는 설계 단계에서 슬라이드별 콘텐츠 정보량을 조절합니다.</div>

    <div class="tpl-section">
      <label>내부 비즈니스 템플릿</label>
      <div class="pending-note soft">외부 템플릿 가져오기는 지원 예정입니다. 아래는 시스템에 내장된 템플릿입니다.</div>
      <div class="tpl-import">
        <input type="text" disabled placeholder="외부 템플릿 URL/검색 — 지원 예정" aria-disabled="true" />
        <button type="button" class="btn-ghost btn-sm" disabled>가져오기</button>
      </div>
      <div class="tpl-grid">${tplGrid || '<div class="expand-note">템플릿 목록을 불러오지 못했습니다.</div>'}</div>
    </div>

    <div class="master-section">
      <label>마스터 스타일 <span class="hint">— 템플릿을 바꿔도 직접 지정한 값은 유지됩니다</span>
        <button type="button" class="btn-ghost btn-sm" style="float:right" onclick="resetMasterStyle()">템플릿 기본값으로 초기화</button>
      </label>
      <div class="field-row">
        <div class="field">
          <label>제목 폰트</label>
          <select onchange="onTitleFontChange(this.value)">${fontOpts}</select>
        </div>
        <div class="field">
          <label>제목 크기</label>
          <select onchange="onTitleSizeChange(this.value)">${sizeOpts}</select>
        </div>
        <div class="field">
          <label>제목 색상</label>
          <div class="color-row">
            <input type="color" value="${esc(resolvedTitleColor())}"
              onchange="onTitleColorChange(this.value.toUpperCase())" aria-label="제목 색상" />
            <input type="text" value="${esc(state.masterStyle.titleColor || '')}"
              placeholder="템플릿 기본 (#RRGGBB)"
              onchange="onTitleColorChange(this.value.trim() || null)" />
          </div>
        </div>
      </div>
      <div class="compact-row">
        <div class="compact-field">
          <span class="lab">페이지 번호</span>
          ${toggleSwitch(state.pageNumber.enabled, 'setPageNumberEnabled')}
        </div>
        <div class="compact-field">
          <span class="lab">페이지 번호 위치</span>
          <select ${state.pageNumber.enabled ? '' : 'disabled'} onchange="onPagePositionChange(this.value)">
            ${PAGE_POS_OPTS.map(([k, lab]) =>
              `<option value="${k}" ${state.pageNumber.position === k ? 'selected' : ''}>${lab}</option>`).join('')}
          </select>
        </div>
        <div class="compact-field control-disabled" aria-disabled="true">
          <span class="lab">로고 고정 표시 <span class="pending-badge">지원 예정</span></span>
          ${toggleSwitch(false, 'noop', { disabled: true })}
        </div>
      </div>
    </div>

    <div class="compact-row active-settings">
      <div class="compact-field">
        <span class="lab">출력 형식</span>
        <select onchange="onOutputFormatChange(this.value)">
          <option ${state.outputFormat === 'PDF' ? 'selected' : ''}>PDF</option>
          <option ${state.outputFormat === 'PPTX' ? 'selected' : ''}>PPTX</option>
        </select>
      </div>
      <div class="compact-field">
        <span class="lab">레이아웃 밀도</span>
        <select onchange="onDensityChange(this.value)">
          ${DENSITY_OPTS.map(([k, lab]) =>
            `<option value="${k}" ${state.density === k ? 'selected' : ''}>${lab}</option>`).join('')}
        </select>
      </div>
      <div class="compact-field">
        <span class="lab">exports 저장</span>
        ${toggleSwitch(state.saveDisk, 'setSaveDisk')}
      </div>
    </div>

    <div class="model-override">
      <div class="compact-row" style="margin-bottom:8px">
        <div class="compact-field" style="flex:1">
          <span class="lab">설계에서 다른 LLM 쓰기 <span class="hint">(기본: ②와 동일 · ${esc(state.model || '—')})</span></span>
          ${toggleSwitch(state.useOtherDesignModel, 'setUseOtherDesignModel')}
        </div>
      </div>
      ${state.useOtherDesignModel ? `
        <div class="field">
          <label>설계용 모델</label>
          <select onchange="onDesignModelChange(this.value)">${designModelOpts}</select>
        </div>` : ''}
    </div>

    <div class="llm-row" style="margin-top:14px">${statusHtml}<button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runDesign()">${btnLabel}</button></div>
    ${d && !designStale ? `<div class="expand-sub">설계된 슬라이드 (${d.page_count}장) · ${esc(d.model || '')}</div>
    <div class="expand-box">${d.slides.map((s, i) => `${i + 1}. [${esc(s.pattern)}] ${esc(s.title)}`).join('\n')}</div>` : ''}`;
}


function panelRender() {
  if (!state.designResult || designStale) {
    return `<div class="card-h">
      <span class="card-num">RND</span>
      <span class="card-ttl">렌더 · 페이지 리뷰</span>
    </div>
    <div class="card-body"><div class="expand-note">${designStale
      ? '밀도 또는 설계 모델이 변경되었습니다. ③에서 재설계하세요.'
      : '아직 설계된 슬라이드가 없습니다.'}</div>`;
  }
  const r = state.renderResult;
  const selN = state.renderReview.selectedPages.length;
  const total = state.previews.length || state.designResult.page_count || 0;

  let statusHtml;
  if (state.previewBusy) {
    statusHtml = `<div class="render-status"><span class="dot pending"></span>전체 덱 프리뷰 생성 중…</div>`;
  } else if (r) {
    const saved = r.saved_to
      ? `<div class="render-saved">exports 저장 완료: <code>${esc(r.saved_to)}</code></div>` : '';
    statusHtml = `<div class="render-status"><span class="dot"></span>${esc(r.fmt)} 생성 완료 · ${r.page_count}페이지 · ${r.size_kb.toFixed(1)}KB</div>${saved}`;
  } else {
    statusHtml = `<div class="render-status"><span class="dot pending"></span>프리뷰 검토 후 다운로드할 형식을 렌더하세요 · 기본 ${esc(state.outputFormat)}</div>`;
  }

  let pagesHtml;
  if (state.previewError && !state.previews.length) {
    pagesHtml = `<div class="preview-fail">미리보기를 생성하지 못했습니다: ${esc(state.previewError)}<br/>원본 파일은 렌더 후 다운로드할 수 있습니다.
      <button type="button" class="btn-ghost btn-sm" onclick="buildPreviews()">다시 시도</button></div>`;
  } else if (!state.previews.length) {
    pagesHtml = `<div class="expand-note">프리뷰가 없습니다. <button type="button" class="btn-ghost btn-sm" onclick="buildPreviews()">프리뷰 생성</button></div>`;
  } else {
    pagesHtml = `<div class="render-pages-scroll">${state.previews.map((p) => {
      const selected = state.renderReview.selectedPages.includes(p.slide_index);
      const fail = !p.html_url;
      return `<article class="render-page-review ${selected ? 'selected' : ''}"
          aria-selected="${selected ? 'true' : 'false'}" data-slide-index="${p.slide_index}">
        <header class="render-page-toolbar">
          <label class="page-check">
            <input type="checkbox" ${selected ? 'checked' : ''}
              onchange="onPageCheck(${p.slide_index}, this.checked)"
              aria-label="${p.page_number}페이지 선택" />
            <span>페이지 ${p.page_number}</span>
          </label>
          <div class="render-page-meta">
            <span class="pattern-pill">${esc(p.pattern)}</span>
            <span class="page-title">${esc(p.title)}</span>
            <button type="button" class="btn-ghost btn-sm" onclick="event.stopPropagation();togglePageCard(${p.slide_index})">
              ${selected ? '선택 해제' : '이 페이지 선택'}
            </button>
          </div>
        </header>
        <div class="render-slide-stage" onclick="togglePageCard(${p.slide_index})"
             role="button" tabindex="0"
             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();togglePageCard(${p.slide_index})}"
             aria-label="${p.page_number}페이지 슬라이드 미리보기: ${esc(p.title)}">
          ${fail
            ? `<div class="preview-fail">미리보기를 생성하지 못했습니다.<br/>원본 파일은 다운로드할 수 있습니다.</div>`
            : `<div class="render-slide-scaler">
                <iframe title="${p.page_number}페이지 슬라이드 미리보기: ${esc(p.title)}"
                  src="${esc(p.html_url)}" width="1920" height="1080"
                  loading="lazy" tabindex="-1"
                  sandbox="allow-same-origin"></iframe>
              </div>`}
        </div>
        <footer class="render-page-footer">
          <span>문제가 있으면 페이지를 선택하세요.</span>
          <button type="button" class="btn-ghost btn-sm" disabled title="스키마 직접 편집은 후속 작업">편집 · 준비 중</button>
        </footer>
      </article>`;
    }).join('')}</div>`;
  }

  return `<div class="card-h">
      <span class="card-num">RND</span>
      <span class="card-ttl">렌더 · 페이지 리뷰</span>
    </div>
    <div class="card-body">
    <div class="expand-note">각 슬라이드를 실제 렌더 템플릿(16:9)으로 세로 스크롤하며 검토합니다. 문제가 있는 페이지만 선택하세요.</div>
    ${statusHtml}
    <div class="render-review-bar">
      <span>총 ${total}페이지 · <strong>${selN}개 페이지 선택됨</strong></span>
      <div class="review-bar-actions">
        <button type="button" class="btn-ghost btn-sm" onclick="selectAllPages()">전체 선택</button>
        <button type="button" class="btn-ghost btn-sm" onclick="clearAllPages()">전체 해제</button>
        <button type="button" class="btn-ghost btn-sm" ${state.previewBusy ? 'disabled' : ''} onclick="buildPreviews()">프리뷰 다시 생성</button>
      </div>
    </div>
    ${pagesHtml}
    <div class="render-actions">
      <span class="lab">출력</span>
      <select onchange="onOutputFormatChange(this.value)" ${busy ? 'disabled' : ''}>
        <option ${state.outputFormat === 'PDF' ? 'selected' : ''}>PDF</option>
        <option ${state.outputFormat === 'PPTX' ? 'selected' : ''}>PPTX</option>
      </select>
      <button class="btn-ghost btn-sm" ${busy ? 'disabled' : ''} onclick="runRender(state.outputFormat)">
        ${busy ? '<span class="spin"></span>렌더 중…' : '다시 렌더'}
      </button>
      <button class="btn-primary btn-sm" ${r ? '' : 'disabled'} onclick="downloadRender()">⬇ 다운로드</button>
    </div>`;
}

const PANEL_FNS = [panelSource, panelExpand, panelDesign, panelRender];

const ISSUE_TYPES = [
  ['language', '언어 오류'],
  ['content-density', '내용 밀도 오류'],
  ['text-overflow', '글자 겹침 또는 잘림'],
  ['layout', '페이지 형식·레이아웃 오류'],
  ['other', '기타'],
];

function sideReviewPanel() {
  const checks = ISSUE_TYPES.map(([id, lab]) => {
    const on = state.renderReview.issueTypes.includes(id);
    return `<label class="issue-item">
      <input type="checkbox" ${on ? 'checked' : ''} onchange="onIssueTypeToggle('${id}')" />
      <span>${lab}</span>
    </label>`;
  }).join('');
  const showOther = state.renderReview.issueTypes.includes('other');
  return `<div class="card-h">
      <span class="card-num">RVW</span>
      <span class="card-ttl">검토 및 재생성</span>
    </div>
    <div class="card-body">
      <div class="input-group" style="margin-bottom:12px">
    <fieldset class="issue-fieldset">
      <legend>문제 유형</legend>
      ${checks}
    </fieldset>
    ${showOther ? `<div class="field" style="margin-top:10px">
      <label>수정 요청을 입력하세요</label>
      <textarea rows="3" oninput="onOtherNoteChange(this.value)">${esc(state.renderReview.otherNote)}</textarea>
    </div>` : ''}
    <div class="review-hint">${esc(reviewHint())}</div>
    <button type="button" class="btn-ghost btn-sm" style="width:100%;margin-top:12px" disabled>
      선택 페이지 교정 — 준비 중
    </button>
    <div class="src-settings-note" style="margin-top:10px">부분 교정은 deck 슬라이드 단위 LLM 재작성이 필요해 후속 작업입니다. 선택·문제 유형 상태는 유지됩니다.</div>`;
}

function sideGenSettings() {
  const modelOpts = state.models.length
    ? state.models.map((m) => `<option ${m === state.model ? 'selected' : ''}>${esc(m)}</option>`).join('')
    : '<option>모델 없음</option>';
  return `<div class="card-h">
      <span class="card-num">OPT</span>
      <span class="card-ttl">옵션</span>
    </div>
    <div class="card-body">
      <div class="input-group" style="margin-bottom:12px">
      <label class="input-label">언어</label>
      <select class="select-field" onchange="onLangChange(this.value)">
        ${['한국어', 'English', '中文'].map((l) => `<option ${l === state.lang ? 'selected' : ''}>${l}</option>`).join('')}
      </select>
    </div>
    <div class="input-group" style="margin-bottom:12px">
      <label class="input-label">페이지 수</label>
      <select class="select-field" onchange="onPageCountChange(this.value)">
        ${['자동 (LLM 판단)', '5장', '10장', '15장'].map((p) => `<option ${p === state.pageCount ? 'selected' : ''}>${p}</option>`).join('')}
      </select>
    </div>
    <div class="input-group">
      <label class="input-label">LLM 모델 ${state.models.length ? `(${state.models.length}개 설치)` : ''}</label>
      <select class="select-field" onchange="onModelChange(this.value)">${modelOpts}</select>
    </div>
    <div class="src-settings-note">언어·페이지 수·모델은 ②확장에 적용됩니다. 템플릿·밀도·스타일은 ③디자인에서 설정합니다.</div>`;
}

const SIDE_FNS = [sideGenSettings, sideGenSettings, sideGenSettings, sideReviewPanel];

function render() {
  buildKPI();
  document.getElementById('panel-content').innerHTML = PANEL_FNS[step]();
  const sideEl = document.getElementById('side');
  sideEl.innerHTML = SIDE_FNS[step]();
  sideEl.classList.toggle('ppt-review-sticky', step === 3);
  document.getElementById('error-box').innerHTML = error ? `<div class="err-box">${esc(error)}</div>` : '';

  for (let i = 0; i < 4; i++) {
    const s = document.getElementById('step-' + i);
    s.classList.remove('done', 'active');
    if (i < step) s.classList.add('done');
    if (i === step) s.classList.add('active');
  }
  document.getElementById('prev-btn').style.visibility = step === 0 ? 'hidden' : 'visible';
  document.getElementById('next-btn').textContent = busy ? '처리 중…' : nextLabels()[step];
  document.getElementById('next-btn').disabled = busy;
  buildProgress();
  if (step === 3) requestAnimationFrame(scalePreviewFrames);
}

init();
