/**
 * V3.1 Shell — 탭 전환 + API 호출 (vanilla JS, no framework).
 *
 * Tab navigation: sidebar 클릭 → tab content toggle
 * API calls: intake upload/paste/folder/scan_tree/index → v31/server.py
 * Real-time: raw file list refresh, KPI update
 */
(function() {
  "use strict";

  var API = "/api";

  // Tab definitions (matches sidebar nav-item[data-section])
  var TABS = {
    ppt:     { phase: "작성", phaseClass: "create", bcPhase: "Create", bcCur: "PPT · DECK CONSOLE" },
    truth:   { phase: "핵심", phaseClass: "core", bcPhase: "Core", bcCur: "진실원" },
    input:   { phase: "핵심", phaseClass: "core", bcPhase: "Core", bcCur: "입력" },
    flow:    { phase: "핵심", phaseClass: "core", bcPhase: "Core", bcCur: "흐름" },
    data:    { phase: "분석", phaseClass: "knowledge", bcPhase: "Knowledge", bcCur: "데이터" },
    graph:   { phase: "분석", phaseClass: "knowledge", bcPhase: "Knowledge", bcCur: "그래프" },
    wiki:    { phase: "분석", phaseClass: "knowledge", bcPhase: "Knowledge", bcCur: "위키" },
    insight: { phase: "관측", phaseClass: "observ", bcPhase: "External", bcCur: "인사이트" },
    settings:{ phase: "관리", phaseClass: "manage", bcPhase: "External", bcCur: "설정" },
  };

  // State
  var _scanResult = null;
  var _selectedPaths = {};
  var _intakeMeta = { external_dir: "", archive_default: "" };

  function init() {
    var navItems = document.querySelectorAll(".nav-item[data-section]");
    var tabIds = Object.keys(TABS);

    navItems.forEach(function(item) {
      item.addEventListener("click", function() {
        showTab(this.dataset.section);
      });
    });
    var activeItem = document.querySelector(".nav-item.active");
    if (activeItem) {
      showTab(activeItem.dataset.section);
    }
  }

  function showTab(section) {
    var tabIds = Object.keys(TABS);
    tabIds.forEach(function(id) {
      var tab = document.getElementById("tab-" + id);
      if (tab) tab.style.display = "none";
    });

    var active = document.getElementById("tab-" + section);
    if (active) {
      active.style.display = "block";

      if (section === "input") {
        refreshIntakeMeta();
        refreshSourceList();
        refreshExternalRecent();
      }
    }

    var navItems = document.querySelectorAll(".nav-item[data-section]");
    navItems.forEach(function(item) {
      item.classList.toggle("active", item.dataset.section === section);
      item.classList.remove("done");
    });

    var sections = tabIds;
    var activeIdx = sections.indexOf(section);
    sections.forEach(function(s, i) {
      if (i < activeIdx) {
        var btn = document.querySelector(".nav-item[data-section='" + s + "']");
        if (btn) btn.classList.add("done");
      }
    });

    var info = TABS[section];
    var badge = document.getElementById("phaseBadge");
    badge.textContent = info.phase;
    badge.className = "phase-badge" + (info.phaseClass ? " " + info.phaseClass : "");
    document.getElementById("bcPhase").textContent = info.bcPhase;
    document.getElementById("bcCur").textContent = info.bcCur;
  }

  function api(path, options) {
    return fetch(API + path, options).then(function(res) {
      return res.json().then(function(data) {
        if (!res.ok) throw new Error(data.detail || "API error");
        return data;
      });
    });
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function formatSize(bytes) {
    if (!bytes) return "—";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function renderSourceRows(tbody, files) {
    if (!tbody) return;
    tbody.innerHTML = "";
    if (files.length === 0) {
      tbody.innerHTML = "<tr><td colspan='2' class='intake-empty'>비어 있음</td></tr>";
      return;
    }
    files.forEach(function(s) {
      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td class='mono'>" + escapeHtml(s.name) + "</td>" +
        "<td class='mono'>" + formatSize(s.size) + "</td>";
      tbody.appendChild(tr);
    });
  }

  function refreshIntakeMeta() {
    api("/api/intake/meta").then(function(data) {
      _intakeMeta = data;
      var hint = document.getElementById("archiveDefaultHint");
      if (hint && data.archive_default) {
        hint.textContent = "기본 archive: " + data.archive_default + " · 분류는 흐름 탭에서";
      }
      var pathEl = document.getElementById("extStoragePath");
      if (pathEl && data.external_dir) pathEl.textContent = data.external_dir;
      var srcCount = document.getElementById("extSourceCount");
      if (srcCount && data.external_sources) srcCount.textContent = data.external_sources;
    }).catch(function(err) {
      console.warn("[v31] refreshIntakeMeta failed:", err.message);
    });
  }

  // --- Refresh source list ---
  function refreshSourceList() {
    api("/api/sources").then(function(data) {
      var files = data.sources || [];
      renderSourceRows(document.querySelector("#sourceTableBodyTop"), files);

      var count = data.count != null ? data.count : files.length;
      var kpi = document.getElementById("inputKpiCount");
      if (kpi) kpi.textContent = count;
      ["inputRawCountTop"].forEach(function(id) {
        var el = document.getElementById(id);
        if (el) el.textContent = count;
      });
    }).catch(function(err) {
      console.warn("[v31] refreshSourceList failed:", err.message);
      var tbody = document.querySelector("#sourceTableBodyTop");
      if (tbody) {
        tbody.innerHTML = "<tr><td colspan='2' class='intake-empty'>로드 실패</td></tr>";
      }
    });
  }

  // --- Refresh external recent ---
  function refreshExternalRecent() {
    api("/api/external/recent").then(function(data) {
      var container = document.querySelector("#extRecentList");
      var countEl = document.getElementById("extRecentCount");
      var labelEl = document.getElementById("extRecentLabel");
      if (!container) return;

      var total = data.events ? data.events.length : 0;
      if (countEl) countEl.textContent = total;
      if (labelEl) labelEl.textContent = "총 " + total + "건";

      if (total === 0) {
        container.innerHTML = '<div class="intake-note">아직 박힌 이벤트가 없습니다.</div>';
        return;
      }

      var html = "";
      data.events.forEach(function(e, idx) {
        html += '<div class="intake-recent-item">' +
          '<div class="intake-recent-head">' +
          '<div><strong>' + escapeHtml(e.title) + '</strong>' +
          '<div class="intake-recent-meta">' +
          new Date(e.mtime * 1000).toLocaleString("ko") + ' · ' +
          formatSize(e.size) + '</div></div>' +
          '<span class="card-num">' + escapeHtml(e.source) + '</span></div>' +
          '<details class="intake-recent-body"><summary>미리보기 / 원본</summary>' +
          '<pre id="extPreview_' + idx + '">불러오는 중…</pre></details></div>';
      });
      container.innerHTML = html;

      data.events.forEach(function(e, idx) {
        var pre = document.getElementById("extPreview_" + idx);
        if (!pre || !e.path) return;
        api("/api/external/content?path=" + encodeURIComponent(e.path)).then(function(res) {
          pre.textContent = res.preview || res.body || "(empty)";
        }).catch(function() {
          pre.textContent = "(미리보기 로드 실패)";
        });
      });
    }).catch(function(err) {
      console.warn("[v31] refreshExternalRecent failed:", err.message);
    });
  }

  // --- Mode A: File Upload (enhanced) ---
  function handleFileUpload(files) {
    if (!files || files.length === 0) return;

    var dropZone = document.getElementById("dropZone");
    var originalText = dropZone.innerHTML;
    dropZone.innerHTML = "<strong>업로드 중 (" + files.length + "개)...</strong>";
    dropZone.classList.add("busy");

    var successCount = 0;
    var failCount = 0;
    var total = files.length;

    Array.prototype.forEach.call(files, function(file) {
      var formData = new FormData();
      formData.append("file", file);
      api("/api/intake/upload", { method: "POST", body: formData })
        .then(function(result) {
          successCount++;
          dropZone.innerHTML = "<strong>✅ " + successCount + "개 업로드 완료 · " + failCount + "개 실패</strong>";
          refreshSourceList();

          if (successCount + failCount >= total) {
            setTimeout(function() {
              dropZone.innerHTML = originalText;
              dropZone.classList.remove("busy", "error");
            }, 3000);
          }
        })
        .catch(function(err) {
          failCount++;
          dropZone.innerHTML = "<strong>❌ 실패 (" + failCount + "개)</strong>";
          dropZone.classList.add("error");

          if (successCount + failCount >= total) {
            setTimeout(function() {
              dropZone.innerHTML = originalText;
              dropZone.classList.remove("busy", "error");
            }, 5000);
          }
        });
    });
  }

  // --- Mode C: Text Paste (full metadata) ---
  function saveText() {
    var titleEl = document.getElementById("pasteTitle");
    var bodyEl = document.getElementById("pasteBody");
    var sourceEl = document.getElementById("pasteSource");
    var indEl = document.getElementById("pasteIndustry");
    var areaEl = document.getElementById("pasteArea");
    var levEl = document.getElementById("pasteLevel");

    var title = titleEl ? titleEl.value : "";
    var body = bodyEl ? bodyEl.value : "";
    var source = sourceEl ? sourceEl.value : "manual";
    var industry = indEl ? indEl.value : "";
    var area = areaEl ? areaEl.value : "";
    var level = levEl ? levEl.value : "";

    if (!title.trim() || !body.trim()) {
      alert("제목과 내용을 입력하세요.");
      return;
    }

    var btn = document.getElementById("pasteBtn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "저장 중...";
    }

    api("/api/intake/paste", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        source: source,
        body: body,
        industry: industry,
        area: area,
        level: level,
      }),
    }).then(function(result) {
      refreshSourceList();

      if (titleEl) titleEl.value = "";
      if (bodyEl) bodyEl.value = "";
      if (sourceEl) sourceEl.value = "openwebui-chat";
      if (indEl) indEl.value = "";
      if (areaEl) areaEl.value = "";
      if (levEl) levEl.value = "";

      if (btn) {
        btn.textContent = ".md 생성 후 저장 + 인제스트";
        btn.disabled = false;
      }

      alert("저장 완료: " + result.filename);
    }).catch(function(err) {
      console.error("[v31] paste failed:", err.message);
      alert("저장 실패: " + err.message);
      if (btn) {
        btn.textContent = ".md 생성 후 저장 + 인제스트";
        btn.disabled = false;
      }
    });
  }

  // --- Mode B: Folder Loading (Full) ---
  function pickFolder(inputId) {
    api("/api/pick_folder", { method: "POST" })
      .then(function(result) {
        if (result.path) {
          document.getElementById(inputId).value = result.path;
        }
      })
      .catch(function(err) {
        alert("폴더 선택을 실행할 수 없습니다.\n(localhost:8767의 macOS에서만 가능)\n경로를 직접 입력하세요.");
      });
  }

  function scanFolder(path) {
    if (!path || !path.trim()) {
      alert("폴더 경로를 입력하세요.");
      return;
    }

    var container = document.getElementById("folderTreeView");
    var treeEl = document.getElementById("folderTree");
    var emptyHint = document.getElementById("folderEmptyHint");
    var metricsEl = document.getElementById("folderScanMetrics");

    if (container) container.style.display = "block";
    if (emptyHint) emptyHint.style.display = "none";
    if (metricsEl) metricsEl.style.display = "none";
    if (treeEl) treeEl.innerHTML = '<div class="intake-empty">스캔 중…</div>';

    api("/api/intake/scan_tree", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        folder_path: path.trim(),
        recursive: document.getElementById("folderRecursive") ? document.getElementById("folderRecursive").checked : true,
      }),
    }).then(function(result) {
      _scanResult = result;
      Object.keys(_selectedPaths).forEach(function(k) { delete _selectedPaths[k]; });

      // Update metrics
      var totalEl = document.getElementById("scanTotal");
      var pendingEl = document.getElementById("scanPending");
      var processedEl = document.getElementById("scanProcessed");
      if (totalEl) totalEl.textContent = result.total;
      if (pendingEl) pendingEl.textContent = result.pending;
      if (processedEl) processedEl.textContent = result.processed;
      if (metricsEl) metricsEl.style.display = "grid";

      // Render tree view
      if (treeEl && result.directories) {
        var html = "";
        result.directories.forEach(function(dir) {
          var header = dir.is_root ? "(루트)" : dir.path;
          var pendingN = 0;
          var doneN = 0;
          dir.files.forEach(function(f) {
            if (f.processed) doneN++;
            else pendingN++;
          });

          html += '<details class="tree-dir">' +
            '<summary>📂 <strong>' + escapeHtml(header) + '</strong> — ⏳ ' + pendingN + ' · ✅ ' + doneN + '</summary>';

          html += '<div>';
          dir.files.forEach(function(f) {
            var key = 'fl_sel_' + f.path;
            var sizeKB = (f.size / 1024).toFixed(1);
            var mtime = new Date(f.mtime * 1000).toLocaleString("ko");
            var status = f.processed ? "📚" : "⏳";
            var forceEl = document.getElementById("folderForce");
            var defaultChecked = f.processed
              ? (forceEl ? forceEl.checked : false)
              : true;

            html += '<div class="tree-file">' +
              '<input type="checkbox" class="file-checkbox" id="' + key + '" ' +
              (defaultChecked ? 'checked' : '') + ' value="' + escapeHtml(f.path) + '" />' +
              '<label for="' + key + '" style="cursor:pointer;flex:1">' +
              status + ' <strong' + (f.processed ? ' style="color:#71717a"' : '') + '>' + escapeHtml(f.name) + '</strong>' +
              ' · <span class="intake-recent-meta">' + sizeKB + 'KB · ' + mtime + '</span>' +
              '</label></div>';
          });
          html += '</div></details>';
        });
        treeEl.innerHTML = html;

        // Attach checkbox listeners
        treeEl.querySelectorAll(".file-checkbox").forEach(function(cb) {
          cb.addEventListener("change", function() {
            updateSelectedPaths();
          });
        });
      }

      updateSelectedPaths();

    }).catch(function(err) {
      console.error("[v31] scan failed:", err.message);
      if (treeEl) treeEl.innerHTML = '<div style="text-align:center;padding:12px;color:var(--subtle)">스캔 실패: ' + escapeHtml(err.message) + '</div>';
      alert("폴더 스캔 실패: " + err.message);
    });
  }

  function updateSelectedPaths() {
    var checkboxes = document.querySelectorAll(".file-checkbox");
    Object.keys(_selectedPaths).forEach(function(k) { delete _selectedPaths[k]; });
    checkboxes.forEach(function(cb) {
      _selectedPaths[cb.value] = cb.checked;
    });

    var count = Object.keys(_selectedPaths).filter(function(k) { return _selectedPaths[k]; }).length;
    var countEl = document.getElementById("selectedCount");
    var runBtn = document.getElementById("runIndexBtn");

    if (countEl) countEl.textContent = count;
    if (runBtn) {
      runBtn.disabled = count === 0;
      runBtn.textContent = count + "건 인덱싱";
    }
  }

  function selectAll(select) {
    var checkboxes = document.querySelectorAll(".file-checkbox");
    checkboxes.forEach(function(cb) {
      cb.checked = select;
    });
    updateSelectedPaths();
  }

  function runIndex() {
    var files = [];
    document.querySelectorAll(".file-checkbox:checked").forEach(function(cb) {
      files.push(cb.value);
    });

    if (files.length === 0) {
      alert("선택된 파일이 없습니다.");
      return;
    }

    var lane = document.getElementById("folderLane") ? document.getElementById("folderLane").value : "reference";
    var force = document.getElementById("folderForce") ? document.getElementById("folderForce").checked : false;
    var archiveRoot = document.getElementById("archiveRoot") ? document.getElementById("archiveRoot").value.trim() : "";

    var progressEl = document.getElementById("indexProgress");
    var barEl = document.getElementById("indexProgressBar");
    var labelEl = document.getElementById("indexProgressLabel");
    var logEl = document.getElementById("indexLog");

    if (progressEl) progressEl.style.display = "block";
    if (barEl) barEl.value = 0;
    if (labelEl) labelEl.textContent = "준비 중...";
    if (logEl) logEl.textContent = "";

    var runBtn = document.getElementById("runIndexBtn");
    if (runBtn) runBtn.disabled = true;

    api("/api/intake/index", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        files: files,
        lane: lane,
        force: force,
        archive_root: archiveRoot || null,
      }),
    }).then(function(result) {
      if (progressEl) progressEl.style.display = "none";
      if (barEl) barEl.value = barEl.max;
      if (labelEl) labelEl.textContent = "완료";

      var resultsEl = document.getElementById("indexResults");
      var detailEl = document.getElementById("indexResultDetail");

      if (resultsEl) resultsEl.style.display = "block";

      var msg = "인덱싱 완료 — UPSERT " + result.upserted +
        " · 분류 " + result.classified +
        " · 빈본문 skip " + result.skipped_empty +
        " · 이미 처리 skip " + result.skipped_already;

      if (detailEl) {
        var html = '<div style="margin-bottom:8px;color:var(--accent-blue);font-weight:700">' + escapeHtml(msg) + '</div>';

        if (result.files && result.files.length > 0) {
          html += '<table class="data-table" style="margin-top:8px"><thead><tr><th>파일명</th><th>doc_id</th><th>chunks</th><th>분류기</th><th>industry</th><th>area</th><th>status</th></tr></thead><tbody>';
          result.files.forEach(function(fr) {
            var icon = fr.error ? "❌" : (fr.skipped_reason ? "⊘" : "✅");
            var sc = fr.error ? "var(--error)" : (fr.skipped_reason ? "var(--subtle)" : "var(--accent-blue)");
            html += '<tr><td class="mono">' + escapeHtml(fr.name) + '</td>';
            html += '<td class="mono">' + (fr.doc_id ? escapeHtml(fr.doc_id.substring(0, 16)) + "..." : "—") + '</td>';
            html += '<td class="mono">' + fr.chunks + '</td>';
            html += '<td class="mono">' + escapeHtml(fr.classifier) + '</td>';
            html += '<td class="mono">' + escapeHtml(fr.industry || "—") + '</td>';
            html += '<td class="mono">' + escapeHtml(fr.area || "—") + '</td>';
            html += '<td class="val" style="color:' + sc + '">' + icon + '</td></tr>';
            if (fr.error) {
              html += '<tr><td colspan="7" style="font-size:0.72rem;color:var(--error)">❌ ' + escapeHtml(fr.error) + '</td></tr>';
            }
          });
          html += '</tbody></table>';
        }

        if (result.errors && result.errors.length > 0) {
          html += '<div style="font-size:0.78rem;color:var(--error);margin-top:8px">⚠️ 실패 ' + result.errors.length + '건</div>';
        }

        detailEl.innerHTML = html;
      }

      refreshSourceList();
      _scanResult = null;
      Object.keys(_selectedPaths).forEach(function(k) { delete _selectedPaths[k]; });
      if (runBtn) runBtn.disabled = true;

    }).catch(function(err) {
      console.error("[v31] index failed:", err.message);
      if (progressEl) progressEl.style.display = "none";
      if (runBtn) runBtn.disabled = false;
      alert("인덱싱 실패: " + err.message);
    });
  }

  function renderExtResult(result) {
    var panel = document.getElementById("extResultPanel");
    if (!panel) return;

    var k2 = result.k2 || {};
    var html = '<div><strong>' + escapeHtml(result.filename) + '</strong> · ' +
      formatSize(result.size) + ' · ' + escapeHtml(result.source || "") + '</div>';

    html += '<div class="intake-metrics" style="margin-top:10px;display:grid">' +
      '<div class="intake-metric"><span class="intake-metric-k">industry</span><span class="intake-metric-v">' + escapeHtml(k2.industry || "—") + '</span></div>' +
      '<div class="intake-metric"><span class="intake-metric-k">area</span><span class="intake-metric-v">' + escapeHtml(k2.area || "—") + '</span></div>' +
      '<div class="intake-metric"><span class="intake-metric-k">level</span><span class="intake-metric-v">' + escapeHtml(k2.level || "—") + '</span></div>' +
      '<div class="intake-metric"><span class="intake-metric-k">chunks</span><span class="intake-metric-v">' + (result.chunks || 0) + '</span></div>' +
      '</div>';

    if (k2.summary) html += '<p class="intake-hint-line">요약: ' + escapeHtml(k2.summary) + '</p>';
    if (result.ingest_ok) {
      html += '<p class="intake-hint-line">documents/chunks/FTS 반영 완료</p>';
    } else {
      html += '<p class="intake-hint-line">인제스트 실패(raw .md는 보존됨)</p>';
    }
    panel.innerHTML = html;
  }

  function openExternalFolder() {
    var path = _intakeMeta.external_dir;
    if (!path) return;
    api("/api/open_path", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: path }),
    }).catch(function(err) {
      alert("폴더 열기 실패: " + err.message);
    });
  }

  // --- External Response Capture ---
  function captureExternal() {
    var titleEl = document.getElementById("extTitle");
    var bodyEl = document.getElementById("extBody");
    var sourceEl = document.getElementById("extSource");
    var promptEl = document.getElementById("extPrompt");

    var title = titleEl ? titleEl.value.trim() : "";
    var body = bodyEl ? bodyEl.value.trim() : "";
    var source = sourceEl ? sourceEl.value : "manual-note";
    var prompt = promptEl ? promptEl.value.trim() : "";

    if (!title || !body) {
      alert("이벤트명과 답변 본문을 입력하세요.");
      return;
    }

    var btn = document.getElementById("extSaveBtn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "저장 중 (K2 5~60초)...";
    }

    api("/api/external/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        source: source,
        prompt: prompt,
        body: body,
      }),
    }).then(function(result) {
      result.source = source;
      renderExtResult(result);

      if (titleEl) titleEl.value = "";
      if (bodyEl) bodyEl.value = "";
      if (promptEl) promptEl.value = "";

      refreshExternalRecent();

      if (btn) {
        btn.textContent = "저장 실행";
        btn.disabled = false;
      }

      alert("저장 완료: " + result.filename);

    }).catch(function(err) {
      console.error("[v31] capture failed:", err.message);
      alert("저장 실패: " + err.message);
      if (btn) {
        btn.textContent = "저장 실행";
        btn.disabled = false;
      }
    });
  }

  // Expose to global for HTML event handlers
  window.v31 = {
    showTab: showTab,
    refreshSourceList: refreshSourceList,
    refreshIntakeMeta: refreshIntakeMeta,
    openExternalFolder: openExternalFolder,
    handleFileUpload: handleFileUpload,
    saveText: saveText,
    scanFolder: scanFolder,
    pickFolder: pickFolder,
    selectAll: selectAll,
    runIndex: runIndex,
    captureExternal: captureExternal,
  };

  document.addEventListener("DOMContentLoaded", init);
})();
