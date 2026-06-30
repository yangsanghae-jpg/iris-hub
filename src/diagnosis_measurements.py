"""diagnosis-tool git 저장소 스냅샷 (읽기 전용)."""
from __future__ import annotations

from dataclasses import dataclass

from .diagnosis_git import DiagnosisRepo, git_tracked_paths, resolve_diagnosis_repo


@dataclass
class DiagnosisSnapshot:
    repo: DiagnosisRepo | None
    tracked_data_src: int
    tracked_poc_scripts: int
    tracked_docs: int


def measure_diagnosis() -> DiagnosisSnapshot:
    repo = resolve_diagnosis_repo()
    if repo is None:
        return DiagnosisSnapshot(repo=None, tracked_data_src=0, tracked_poc_scripts=0, tracked_docs=0)

    tracked = git_tracked_paths(repo)
    data_src = sum(1 for p in tracked if p.startswith("data/src/"))
    poc = sum(1 for p in tracked if p.startswith("scripts/data_poc/"))
    docs = sum(1 for p in tracked if p.startswith("docs/data_restructure/"))
    return DiagnosisSnapshot(
        repo=repo,
        tracked_data_src=data_src,
        tracked_poc_scripts=poc,
        tracked_docs=docs,
    )
