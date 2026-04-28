#!/usr/bin/env python3
"""Record daily check-in: names must match roster.csv (UTF-8)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROSTER = BASE / "roster.csv"
ALIASES = BASE / "app_aliases.json"
ATT_DIR = BASE / "attendance"


def load_roster_names() -> list[str]:
    import csv

    with open(ROSTER, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r["name"].strip() for r in rows if r.get("name", "").strip()]


def load_aliases() -> dict[str, str]:
    if not ALIASES.is_file():
        return {}
    data = json.loads(ALIASES.read_text(encoding="utf-8"))
    return {str(k).strip(): str(v).strip() for k, v in data.items() if k and v}


def normalize_names(text: str) -> list[str]:
    """Split pasted text: commas, Chinese commas, newlines, spaces."""
    parts = re.split(r"[,，、\n\r\t]+", text)
    return [p.strip() for p in parts if p.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Write daily attendance JSON under attendance/")
    parser.add_argument(
        "date",
        nargs="?",
        default=None,
        help="YYYY-MM-DD (default: today local date)",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="File with one name per line or comma-separated names",
    )
    parser.add_argument(
        "-t",
        "--text",
        help="Inline names, comma or newline separated",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON only, do not write",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="与已有 attendance/YYYY-MM-DD.json 合并 present（保留 activity 等字段，只追加新姓名）",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="从已有 attendance/YYYY-MM-DD.json 的 present 中移除指定姓名（并写回 absent/计数）",
    )
    args = parser.parse_args()

    if args.merge and args.remove:
        print("不能同时使用 --merge 与 --remove。", file=sys.stderr)
        sys.exit(2)

    if args.file and args.text:
        print("Use either --file or --text, not both.", file=sys.stderr)
        sys.exit(2)

    if not ROSTER.is_file():
        print(f"Missing roster: {ROSTER}", file=sys.stderr)
        sys.exit(1)

    roster_set = set(load_roster_names())
    if not roster_set:
        print("Roster is empty.", file=sys.stderr)
        sys.exit(1)

    aliases = load_aliases()

    if args.file:
        raw = args.file.read_text(encoding="utf-8")
    elif args.text:
        raw = args.text
    else:
        raw = sys.stdin.read()

    present = normalize_names(raw)
    resolved: list[str] = []
    for n in present:
        r = aliases.get(n, n)
        resolved.append(r)
    present = resolved

    unknown = sorted({n for n in present if n not in roster_set})
    if unknown:
        print("Names not in roster (fix typos or update roster.csv):", file=sys.stderr)
        for n in unknown:
            print(f"  - {n}", file=sys.stderr)
        sys.exit(1)

    d = args.date
    if d:
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            print("Date must be YYYY-MM-DD", file=sys.stderr)
            sys.exit(2)
    else:
        d = date.today().isoformat()

    seen: set[str] = set()
    present_ordered: list[str] = []
    for n in present:
        if n in roster_set and n not in seen:
            seen.add(n)
            present_ordered.append(n)

    ATT_DIR.mkdir(parents=True, exist_ok=True)
    out = ATT_DIR / f"{d}.json"

    if args.remove:
        if not out.is_file():
            print(f"没有 {out}，无法 --remove。", file=sys.stderr)
            sys.exit(2)
        data = json.loads(out.read_text(encoding="utf-8"))
        old_present = data.get("present", [])
        if not isinstance(old_present, list):
            old_present = []
        remove_set = set(present_ordered)
        kept: list[str] = []
        kept_seen: set[str] = set()
        for n in old_present:
            s = str(n).strip()
            if not s or s not in roster_set:
                continue
            if s in remove_set:
                continue
            if s not in kept_seen:
                kept_seen.add(s)
                kept.append(s)
        data["present"] = kept
        data["absent"] = sorted(roster_set - kept_seen)
        data["roster_count"] = len(roster_set)
        if "roster_present_count" in data:
            data["roster_present_count"] = len(kept)
        um = data.get("unmatched_in_app", [])
        extra_app = len(um) if isinstance(um, list) else 0
        if "app_completed_count" in data:
            data["app_completed_count"] = len(kept) + extra_app
        note = str(data.get("mapping_notes", "") or "").strip()
        rm_line = f"remove：从 present 移除 {', '.join(sorted(remove_set)) if remove_set else '（无）'}"
        data["mapping_notes"] = (note + " " + rm_line).strip() if note else rm_line
        actually = [n for n in sorted(remove_set) if n in {str(x).strip() for x in old_present}]
        if not actually and remove_set:
            print("提示：要移除的名字都不在当天 present 里，未改动名单。", file=sys.stderr)
        payload = data
    elif args.merge:
        if not out.is_file():
            print(f"没有 {out}，无法 --merge。请先建好该日文件或去掉 --merge。", file=sys.stderr)
            sys.exit(2)
        data = json.loads(out.read_text(encoding="utf-8"))
        old_present = data.get("present", [])
        if not isinstance(old_present, list):
            old_present = []
        merged: list[str] = []
        merged_seen: set[str] = set()
        for n in old_present:
            s = str(n).strip()
            if s in roster_set and s not in merged_seen:
                merged_seen.add(s)
                merged.append(s)
        for n in present_ordered:
            if n not in merged_seen:
                merged_seen.add(n)
                merged.append(n)
        data["present"] = merged
        data["absent"] = sorted(roster_set - merged_seen)
        data["roster_count"] = len(roster_set)
        if "roster_present_count" in data:
            data["roster_present_count"] = len(merged)
        um = data.get("unmatched_in_app", [])
        extra_app = len(um) if isinstance(um, list) else 0
        if "app_completed_count" in data:
            data["app_completed_count"] = len(merged) + extra_app
        note = str(data.get("mapping_notes", "") or "").strip()
        old_name_set = {str(x).strip() for x in old_present if str(x).strip()}
        added = [n for n in present_ordered if n not in old_name_set]
        merge_line = f"补录 merge：追加 {', '.join(added) if added else '（无新姓名）'}"
        data["mapping_notes"] = (note + " " + merge_line).strip() if note else merge_line
        payload = data
    else:
        absent = sorted(roster_set - seen)
        payload = {
            "date": d,
            "present_count": len(present_ordered),
            "roster_count": len(roster_set),
            "present": present_ordered,
            "absent": absent,
        }

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    if args.remove:
        plen = len(payload.get("present", []))
        print(f"移除后 present: {plen}/{payload.get('roster_count', len(roster_set))}")
    elif args.merge:
        plen = len(payload.get("present", []))
        print(f"合并后 present: {plen}/{payload.get('roster_count', len(roster_set))}")
    else:
        print(f"Present: {payload['present_count']}/{payload['roster_count']}, absent: {len(payload['absent'])}")


if __name__ == "__main__":
    main()
