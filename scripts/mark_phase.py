"""CLI: Phase 상태 마킹 (V2.5.3 §4.5).

Examples:
    python -m scripts.mark_phase done  --version V2.6 --phase 1 --note "001+002 적용"
    python -m scripts.mark_phase start --version V2.6 --phase 2
    python -m scripts.mark_phase skip  --version V2.5 --phase 0.5 --reason "m2-venv"
    python -m scripts.mark_phase unset --version V2.6 --phase 1
    python -m scripts.mark_phase list
"""
from __future__ import annotations

import argparse
import sys

from src import phases as ph
from src import state as st_mod


def _find_phase(version: str, phase_id: str) -> ph.Phase:
    phs = ph.load_phases()
    for p in phs:
        if p.version == version and p.id == phase_id:
            return p
    raise SystemExit(f"[ERROR] Phase not found: {version}/{phase_id}")


def cmd_done(args):
    p = _find_phase(args.version, args.phase)
    st_mod.mark_done(p, note=args.note)
    print(f"[OK] {p.key} → done" + (f" (note: {args.note})" if args.note else ""))


def cmd_start(args):
    p = _find_phase(args.version, args.phase)
    st_mod.mark_start(p)
    print(f"[OK] {p.key} → in_progress")


def cmd_skip(args):
    p = _find_phase(args.version, args.phase)
    st_mod.mark_skip(p, reason=args.reason)
    print(f"[OK] {p.key} → skipped (reason: {args.reason})")


def cmd_unset(args):
    p = _find_phase(args.version, args.phase)
    st_mod.mark_unset(p)
    print(f"[OK] {p.key} → unset")


def cmd_list(args):
    phs = ph.load_phases()
    sk = st_mod.status_by_key_for_phases(phs)
    for p in phs:
        block = st_mod.get_phase_block(p)
        display = ph.derive_display_status(p, block.get("status"), sk)
        extra = ""
        if block.get("done"):
            extra = f" done={block['done']}"
        elif block.get("skipped"):
            extra = f" skip='{block['skipped']}'"
        elif block.get("started"):
            extra = f" started={block['started']}"
        print(f"  {p.key:12s}  {display:12s}  {p.title}{extra}")


def main() -> int:
    parser = argparse.ArgumentParser(description="iris-hub Phase marker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for action in ("done", "start", "skip", "unset"):
        sp = sub.add_parser(action)
        sp.add_argument("--version", required=True)
        sp.add_argument("--phase", required=True)
        if action == "done":
            sp.add_argument("--note", default=None)
        elif action == "skip":
            sp.add_argument("--reason", required=True)

    sub.add_parser("list")

    args = parser.parse_args()
    {
        "done": cmd_done,
        "start": cmd_start,
        "skip": cmd_skip,
        "unset": cmd_unset,
        "list": cmd_list,
    }[args.cmd](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
