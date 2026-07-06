"""STEP 1 self-test — q3 server/client 미러 동시 반영 (ST1-a..f)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

# iris-hub src on path when run from repo root
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.diagnosis_git import resolve_diagnosis_repo
from src.store import dx_editor, dx_index

MANIFEST_PACK = "q3_scale_profile"
RUNTIME_RELS = [
    "server/data/step3/scale_profile_v3.json",
    "client/data/step3/scale_profile_v3.json",
]
DX_PIDS = ["q3_scale_profile_server", "q3_scale_profile_client"]
EDIT_KEY = "A01|weights.site_scope"


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def _ok(label: str, detail: str = "") -> None:
    line = f"PASS {label}"
    if detail:
        line += f" — {detail}"
    print(line)


def st1_a(repo_root: Path) -> None:
    for rel in RUNTIME_RELS:
        if not (repo_root / rel).is_file():
            _fail(f"ST1-a: missing {rel}")
    _ok("ST1-a", "server·client 두 runtime 존재")


def st1_b(repo) -> None:
    idx, err = dx_index.load_dx_index(repo)
    if idx is None:
        _fail(f"ST1-b: {err}")
    st, det = dx_index.pack_mirror_sync_status(
        repo.root, idx.q_matrix, idx.q_framework, MANIFEST_PACK
    )
    idx.close()
    if st != "synced":
        _fail(f"ST1-b: 무편집 byte-0 불일치 — {det}")
    _ok("ST1-b", "무편집 두 미러 byte-0 일치 → 배너 일치 조건 충족")


def _read_nested(row: dict, fp: str):
    return dx_index.get_nested(row.get("value_json") or {}, fp)


def st1_c_d_e(repo) -> None:
  qm_orig = dx_editor.load_q_matrix(repo.root)
  sub, fp = EDIT_KEY.split("|", 1)
  server_row = next(
      r for r in qm_orig if r.get("pack_id") == DX_PIDS[0] and r.get("sub_code") == sub
  )
  orig_val = _read_nested(server_row, fp)
  if not isinstance(orig_val, int):
      _fail(f"ST1-c: expected int weight at {EDIT_KEY}, got {orig_val!r}")
  new_val = orig_val - 1 if orig_val > 0 else orig_val + 1

  # dirty → pending
  pending = {EDIT_KEY: new_val}
  qm_dirty = dx_index.apply_q3_grid_edits(copy.deepcopy(qm_orig), MANIFEST_PACK, pending)
  idx, _ = dx_index.load_dx_index(repo)
  st_dirty, _ = dx_index.pack_mirror_sync_status(
      repo.root, qm_dirty, idx.q_framework, MANIFEST_PACK
  )
  idx.close()
  if st_dirty == "synced":
      _fail("ST1-d: 편집 후(미저장)에도 synced — 배너 미반영 조건 실패")

  # both dx mirrors get same value
  for dx_pid in DX_PIDS:
      row = next(r for r in qm_dirty if r.get("pack_id") == dx_pid and r.get("sub_code") == sub)
      got = _read_nested(row, fp)
      if got != new_val:
          _fail(f"ST1-c: dx {dx_pid} not updated ({got} != {new_val})")

  result = dx_editor.save_q_pack_and_rebuild(repo, qm_dirty, MANIFEST_PACK)
  if not result.ok:
      _fail(f"ST1-c save: {result.message}")

  for rel in RUNTIME_RELS:
      text = (repo.root / rel).read_text(encoding="utf-8")
      payload = json.loads(text)
      prof = payload.get("subindustry_profiles", {}).get(sub, {})
      got = dx_index.get_nested(prof, fp)
      if got != new_val:
          _fail(f"ST1-c: runtime {rel} missing new value ({got} != {new_val})")

  idx, _ = dx_index.load_dx_index(repo)
  st_saved, det = dx_index.pack_mirror_sync_status(
      repo.root, qm_dirty, idx.q_framework, MANIFEST_PACK
  )
  idx.close()
  if st_saved != "synced":
      _fail(f"ST1-d: 저장 후 불일치 — {det}")
  _ok("ST1-c", f"편집→저장 후 server·client 둘 다 {fp}={new_val}")
  _ok("ST1-d", "편집 후 미반영 / 저장 후 일치")

  # restore
  restore = dx_editor.save_q_pack_and_rebuild(repo, qm_orig, MANIFEST_PACK)
  if not restore.ok:
      _fail(f"restore failed: {restore.message}")
  idx, _ = dx_index.load_dx_index(repo)
  st_back, _ = dx_index.pack_mirror_sync_status(
      repo.root, qm_orig, idx.q_framework, MANIFEST_PACK
  )
  idx.close()
  if st_back != "synced":
      _fail("restore: byte-0 mismatch after rollback")


def st1_e() -> None:
    locks = dx_index.field_locks()
    q3_paths = dx_index.q3_editable_field_paths()
    if not q3_paths:
        _fail("ST1-e: no q3 whitelist")
    if "q3" not in locks.get("dx_q_matrix", {}).get("value_json_edit_patterns", {}):
        _fail("ST1-e: field_locks missing q3 patterns")
    _ok("ST1-e", f"whitelist {len(q3_paths)} fields · locks loaded")


def st1_f(repo_root: Path) -> None:
    violations = dx_editor.grep_dx_only_writes(repo_root)
    if violations:
        _fail(f"ST1-f: {violations}")
    allowed = dx_editor.audit_allowed_write_targets()
    _ok("ST1-f", f"쓰기 허용={len(allowed)}경로 (dx+runtime 미러)")


def main() -> None:
    repo = resolve_diagnosis_repo()
    if repo is None:
        _fail("diagnosis-tool clone 없음")
    print(f"repo: {repo.root}")
    st1_a(repo.root)
    st1_b(repo)
    st1_c_d_e(repo)
    st1_e()
    st1_f(repo.root)
    print("\n=== ST1 ALL GREEN ===")


if __name__ == "__main__":
    main()
