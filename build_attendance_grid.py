#!/usr/bin/env python3
"""Read roster.csv + attendance/*.json → 分享_体育作业打卡.html

布局：行为全班学生（序号、姓名），列为日期，打卡格显示 🏆，末列累计。
4.16 与 4.17 之间可插入一列空白：前四个日期（通常为 4.13～4.16）均打卡则显示 🚩。
4.19 列后可插入一列空白：4.17～4.19 三天均打卡则显示 🚩。
4.26 列后可插入一列空白：4.24～4.26 三天均打卡则显示 🚩。
学生行按姓名汉语拼音排序（需安装 pypinyin）。
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from html import escape
from pathlib import Path

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:
    print("请先安装: pip3 install pypinyin", file=sys.stderr)
    sys.exit(1)

BASE = Path(__file__).resolve().parent
ROSTER = BASE / "roster.csv"
ATT_DIR = BASE / "attendance"
OUT = ATT_DIR / "分享_体育作业打卡.html"


def load_roster_rows() -> list[tuple[int, str]]:
    with open(ROSTER, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out: list[tuple[int, str]] = []
    for r in rows:
        name = (r.get("name") or "").strip()
        if not name:
            continue
        rank = int(float(r["rank"]))
        out.append((rank, name))
    return out


def pinyin_sort_key(name: str) -> str:
    """全拼小写，用于与「首字母」一致的通讯录式排序。"""
    return "".join(lazy_pinyin(name, style=Style.NORMAL)).lower()


def sort_roster_names_by_pinyin(rows: list[tuple[int, str]]) -> list[str]:
    names = [r[1] for r in rows]
    return sorted(names, key=pinyin_sort_key)


def load_days() -> list[dict]:
    days: list[dict] = []
    for path in sorted(ATT_DIR.glob("*.json")):
        if path.name.startswith("."):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if "present" not in data or "date" not in data:
            continue
        days.append(
            {
                "date": data["date"],
                "activity": data.get("activity", data["date"]),
                "present": set(data["present"]),
                "grades": data.get("grades", {}),
            }
        )
    days.sort(key=lambda d: d["date"])
    return days


def day_headers(days: list[dict]) -> tuple[list[str], str]:
    """Return (short header per column, subtitle for page)."""
    if not days:
        return [], ""

    parsed: list[tuple[int, int, int, str]] = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        parsed.append((dt.year, dt.month, dt.day, d["activity"]))

    y0, m0, _, _ = parsed[0]
    same_ym = all(p[0] == y0 and p[1] == m0 for p in parsed)
    # 表头日期：月.日（如 4.3、4.10），跨月时自动区分
    headers: list[str] = []
    for _y, m, day, _act in parsed:
        headers.append(f"{m}.{day}")

    subtitle = f"{y0}年{m0}月" if same_ym else f"{y0}年（跨月）"
    return headers, subtitle


def export_filename(days: list[dict]) -> str:
    if not days:
        return "作业打卡表.png"
    a, b = days[0]["date"], days[-1]["date"]
    return f"作业打卡表_{a}_至_{b}.png"


def build_html(roster_names: list[str], days: list[dict]) -> str:
    check = "🏆"
    grade_marks = {"A+": "🏅", "A": "🥈", "B": "🥉"}
    full_mark = "🚩"
    col_labels, period_subtitle = day_headers(days)
    fname = export_filename(days)
    # 旧空白列：保留在 4.7 前（历史规则）
    old_spacer_index = next((i for i, x in enumerate(col_labels) if x == "4.7"), None)
    # 新空白列：加在 4.9 后（用于三天连卡）
    anchor_index = next((i for i, x in enumerate(col_labels) if x == "4.9"), None)
    new_spacer_index = (anchor_index + 1) if anchor_index is not None else None
    # 4.16 与 4.17 之间空白列：前四个日期均打卡则显示 🚩
    spacer_before_417_index = next((i for i, x in enumerate(col_labels) if x == "4.17"), None)
    # 4.19 列后空白列：4.17、4.18、4.19 均打卡则显示 🚩
    idx_417 = next((i for i, x in enumerate(col_labels) if x == "4.17"), None)
    idx_418 = next((i for i, x in enumerate(col_labels) if x == "4.18"), None)
    idx_419 = next((i for i, x in enumerate(col_labels) if x == "4.19"), None)
    spacer_after_419 = all(x is not None for x in (idx_417, idx_418, idx_419))
    # 4.23 列后空白列：4.20～4.23 四天均打卡则显示 🚩
    idx_420 = next((i for i, x in enumerate(col_labels) if x == "4.20"), None)
    idx_421 = next((i for i, x in enumerate(col_labels) if x == "4.21"), None)
    idx_422 = next((i for i, x in enumerate(col_labels) if x == "4.22"), None)
    idx_423 = next((i for i, x in enumerate(col_labels) if x == "4.23"), None)
    spacer_after_423 = all(x is not None for x in (idx_420, idx_421, idx_422, idx_423))
    # 4.26 列后空白列：4.24、4.25、4.26 均打卡则显示 🚩
    idx_424 = next((i for i, x in enumerate(col_labels) if x == "4.24"), None)
    idx_425 = next((i for i, x in enumerate(col_labels) if x == "4.25"), None)
    idx_426 = next((i for i, x in enumerate(col_labels) if x == "4.26"), None)
    spacer_after_426 = all(x is not None for x in (idx_424, idx_425, idx_426))

    day_ths = []
    for i, d in enumerate(days):
        if old_spacer_index is not None and i == old_spacer_index:
            day_ths.append('<th scope="col" class="spacer-col"></th>')
        if new_spacer_index is not None and i == new_spacer_index:
            day_ths.append('<th scope="col" class="spacer-col"></th>')
        if spacer_before_417_index is not None and i == spacer_before_417_index:
            day_ths.append(
                '<th scope="col" class="spacer-col" title="前四个日期均打卡"></th>'
            )
        lab = col_labels[i] if i < len(col_labels) else ""
        title = escape(d["activity"])
        day_ths.append(f'<th scope="col" class="day-col" title="{title}">{escape(lab)}</th>')
        if idx_423 is not None and i == idx_423:
            day_ths.append(
                '<th scope="col" class="spacer-col" title="4.20～4.23 均打卡"></th>'
            )
        if idx_426 is not None and i == idx_426:
            day_ths.append(
                '<th scope="col" class="spacer-col" title="4.24～4.26 均打卡"></th>'
            )
    if spacer_after_419:
        day_ths.append(
            '<th scope="col" class="spacer-col" title="4.17～4.19 均打卡"></th>'
        )
    day_th_row = "".join(day_ths)

    body_rows: list[str] = []
    for seq, name in enumerate(roster_names, start=1):
        cells: list[str] = []
        total = 0
        for i, d in enumerate(days):
            if old_spacer_index is not None and i == old_spacer_index:
                # 旧空白列：4.3~4.6 全勤打旗
                pre_days = days[:old_spacer_index]
                full_old = bool(pre_days) and all(name in x["present"] for x in pre_days)
                cells.append(f'<td class="spacer-col">{full_mark if full_old else ""}</td>')
            if new_spacer_index is not None and i == new_spacer_index and anchor_index is not None:
                # 在 4.9 后空白列标记：4.7~4.9 连续三天打卡
                start = max(0, anchor_index - 2)
                pre_days = days[start : anchor_index + 1]
                full = len(pre_days) == 3 and all(name in x["present"] for x in pre_days)
                cells.append(f'<td class="spacer-col">{full_mark if full else ""}</td>')
            if spacer_before_417_index is not None and i == spacer_before_417_index:
                first_four = days[:4]
                full4 = len(first_four) >= 4 and all(name in x["present"] for x in first_four)
                cells.append(f'<td class="spacer-col">{full_mark if full4 else ""}</td>')
            if name in d["present"]:
                grade_raw = str(d.get("grades", {}).get(name, "")).strip().upper()
                mark = grade_marks.get(grade_raw, check)
                cells.append(f'<td class="ok">{mark}</td>')
                total += 1
            else:
                cells.append('<td class="no"></td>')
            if idx_423 is not None and i == idx_423:
                if spacer_after_423 and idx_420 is not None and idx_421 is not None and idx_422 is not None:
                    four_days = [days[idx_420], days[idx_421], days[idx_422], days[idx_423]]
                    four_ok = all(name in x["present"] for x in four_days)
                    cells.append(f'<td class="spacer-col">{full_mark if four_ok else ""}</td>')
                else:
                    cells.append('<td class="spacer-col"></td>')
            if idx_426 is not None and i == idx_426:
                if spacer_after_426 and idx_424 is not None and idx_425 is not None:
                    triple_424_426 = [days[idx_424], days[idx_425], days[idx_426]]
                    triple_ok_426 = all(name in x["present"] for x in triple_424_426)
                    cells.append(
                        f'<td class="spacer-col">{full_mark if triple_ok_426 else ""}</td>'
                    )
                else:
                    cells.append('<td class="spacer-col"></td>')
        if spacer_after_419 and idx_417 is not None and idx_418 is not None and idx_419 is not None:
            triple_days = [days[idx_417], days[idx_418], days[idx_419]]
            triple_ok = all(name in x["present"] for x in triple_days)
            cells.append(f'<td class="spacer-col">{full_mark if triple_ok else ""}</td>')
        total_cell = str(total) if total > 0 else "–"
        body_rows.append(
            "<tr>"
            f'<td class="num sticky-num">{seq}</td>'
            f'<td class="nm sticky-name">{escape(name)}</td>'
            f'{"".join(cells)}'
            f'<td class="sum">{total_cell}</td>'
            "</tr>"
        )

    footer_parts = ["build_attendance_grid.py"]
    if spacer_before_417_index is not None:
        footer_parts.append("4.16/4.17 间=前四日全勤🚩")
    if spacer_after_419:
        footer_parts.append("4.19 后=4.17～4.19 三连🚩")
    if spacer_after_423:
        footer_parts.append("4.23 后=4.20～4.23 全勤🚩")
    if spacer_after_426:
        footer_parts.append("4.26 后=4.24～4.26 三连🚩")
    footer_parts.append("html2canvas（CDN）")
    footer_text = " · ".join(footer_parts)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>作业打卡表（可截图）</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 10px 8px 20px;
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: #dbeafe;
      color: #0f172a;
    }}
    h1 {{
      font-size: 1rem;
      font-weight: 700;
      text-align: center;
      margin: 0 0 2px;
      color: #1e3a8a;
    }}
    .sub {{
      text-align: center;
      font-size: 0.78rem;
      color: #1e40af;
      margin: 0 0 10px;
    }}
    .hint {{
      text-align: center;
      font-size: 0.68rem;
      color: #475569;
      margin: 0 0 8px;
    }}
    .wrap {{
      overflow: auto;
      max-width: 100%;
      border-radius: 8px;
      border: 2px solid #2563eb;
      background: #eff6ff;
      box-shadow: 0 2px 10px rgba(30, 64, 175, 0.15);
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 12px;
      min-width: max-content;
    }}
    th, td {{
      border: 1px solid #3b82f6;
      padding: 6px 5px;
      text-align: center;
      vertical-align: middle;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #93c5fd;
      color: #1e3a8a;
      font-weight: 700;
      font-size: 11px;
    }}
    thead th.sticky-num {{
      left: 0;
      z-index: 4;
      min-width: 36px;
      width: 36px;
      background: #60a5fa;
      color: #fff;
    }}
    thead th.sticky-name {{
      left: 36px;
      z-index: 4;
      min-width: 76px;
      background: #60a5fa;
      color: #fff;
    }}
    thead th.day-col {{
      min-width: 32px;
      padding-left: 4px;
      padding-right: 4px;
    }}
    th.spacer-col, td.spacer-col {{
      min-width: 24px;
      width: 24px;
      padding: 0 2px;
      background: #dbeafe;
      border-left: 2px solid #2563eb;
      border-right: 2px solid #2563eb;
      text-align: center;
      font-size: 13px;
    }}
    thead th.sum-col {{
      min-width: 40px;
      background: #7dd3fc;
      color: #0c4a6e;
    }}
    tbody tr:nth-child(even) {{
      background: #e0f2fe;
    }}
    tbody tr:nth-child(odd) {{
      background: #f0f9ff;
    }}
    tbody td.num {{
      font-weight: 600;
      color: #1e40af;
    }}
    tbody td.nm {{
      font-weight: 600;
      text-align: center;
      white-space: nowrap;
      color: #0f172a;
    }}
    tbody td.sticky-num {{
      position: sticky;
      left: 0;
      z-index: 1;
      background: inherit;
    }}
    tbody td.sticky-name {{
      position: sticky;
      left: 36px;
      z-index: 1;
      background: inherit;
      box-shadow: 2px 0 4px rgba(30, 64, 175, 0.08);
    }}
    tbody tr:nth-child(even) td.sticky-num,
    tbody tr:nth-child(even) td.sticky-name {{
      background: #e0f2fe;
    }}
    tbody tr:nth-child(odd) td.sticky-num,
    tbody tr:nth-child(odd) td.sticky-name {{
      background: #f0f9ff;
    }}
    td.ok {{
      font-size: 16px;
      line-height: 1;
      padding: 4px 2px;
    }}
    td.no {{ color: transparent; }}
    td.sum {{
      font-weight: 700;
      color: #1e3a8a;
      background: #bae6fd !important;
    }}
    tfoot .stats-row td {{
      border-top: 2px solid #1d4ed8;
      font-weight: 700;
      font-size: 12px;
      color: #0c4a6e;
      background: #7dd3fc;
    }}
    tfoot .stats-cell {{
      background: #0284c7 !important;
      color: #fff !important;
    }}
    tfoot td.sticky-num,
    tfoot td.sticky-name {{
      position: sticky;
      z-index: 1;
      background: #0284c7 !important;
      box-shadow: 2px 0 4px rgba(8, 47, 73, 0.2);
    }}
    tfoot td.sticky-num {{ left: 0; }}
    tfoot td.sticky-name {{ left: 36px; }}
    tfoot .stats-count {{
      font-variant-numeric: tabular-nums;
    }}
    tfoot td.tfoot-sum-empty {{
      background: #7dd3fc;
    }}
    .toolbar {{
      display: flex;
      justify-content: center;
      gap: 10px;
      margin: 0 0 12px;
      flex-wrap: wrap;
    }}
    .toolbar button {{
      font-family: inherit;
      font-size: 0.88rem;
      font-weight: 600;
      padding: 10px 20px;
      border: none;
      border-radius: 10px;
      background: linear-gradient(180deg, #3b82f6, #2563eb);
      color: #fff;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
    }}
    .toolbar button:hover {{
      filter: brightness(1.05);
    }}
    .toolbar button:disabled {{
      opacity: 0.65;
      cursor: wait;
    }}
    #capture-root {{
      background: #dbeafe;
      padding: 4px 0 2px;
    }}
    @media print {{
      html, body {{
        width: max-content;
        min-width: max-content;
        margin: 0;
        padding: 0;
        background: #dbeafe;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
      .toolbar,
      .footer {{
        display: none !important;
      }}
      #capture-root {{
        width: max-content;
        min-width: max-content;
        padding: 0;
      }}
      .wrap {{
        overflow: visible !important;
        max-width: none !important;
        width: max-content;
        box-shadow: none;
      }}
      table {{
        width: max-content;
      }}
      thead th,
      .sticky-num,
      .sticky-name {{
        position: static !important;
        left: auto !important;
        top: auto !important;
        z-index: auto !important;
        box-shadow: none !important;
      }}
    }}
    .footer {{
      text-align: center;
      font-size: 0.65rem;
      color: #64748b;
      margin-top: 8px;
    }}
  </style>
</head>
<body>
  <div class="toolbar">
    <button type="button" id="btn-long-png" title="下载整张表为一张 PNG（需联网加载生成库）">生成长图 PNG</button>
  </div>
  <div id="capture-root" data-filename="{escape(fname)}">
    <h1>作业打卡表</h1>
    <p class="sub">{escape(period_subtitle)} · 共 {len(days)} 次记录</p>
    <p class="hint">序号 · 姓名 · 各日打卡（A+🏅 / A🥈 / B🥉）</p>
    <div class="wrap" id="table-wrap">
      <table>
        <thead>
          <tr>
            <th scope="col" class="sticky-num">序号</th>
            <th scope="col" class="sticky-name">姓名</th>
            {day_th_row}
            <th scope="col" class="sum-col">累计</th>
          </tr>
        </thead>
        <tbody>
          {"".join(body_rows)}
        </tbody>
      </table>
    </div>
  </div>
  <p class="footer">{escape(footer_text)}</p>
  <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js" crossorigin="anonymous"></script>
  <script>
  (function () {{
    var btn = document.getElementById("btn-long-png");
    var root = document.getElementById("capture-root");
    if (!btn || !root) return;

    function stripSticky(doc) {{
      doc.querySelectorAll("thead th, .sticky-num, .sticky-name").forEach(function (el) {{
        el.style.position = "static";
        el.style.left = "auto";
        el.style.top = "auto";
        el.style.zIndex = "auto";
        el.style.boxShadow = "none";
      }});
      var w = doc.getElementById("table-wrap");
      if (w) {{
        w.style.overflow = "visible";
        w.style.maxWidth = "none";
      }}
    }}

    btn.addEventListener("click", function () {{
      if (typeof html2canvas !== "function") {{
        alert("未加载 html2canvas，请检查网络后刷新页面；或使用 Chrome 开发者工具 → Capture full size screenshot。");
        return;
      }}
      btn.disabled = true;
      var label = btn.textContent;
      btn.textContent = "生成中…";
      window.scrollTo(0, 0);

      var fname = root.getAttribute("data-filename") || "作业打卡表.png";

      html2canvas(root, {{
        scale: Math.min(2, (typeof window.devicePixelRatio === "number" ? window.devicePixelRatio : 2)),
        useCORS: true,
        allowTaint: false,
        backgroundColor: "#dbeafe",
        logging: false,
        onclone: function (clonedDoc) {{ stripSticky(clonedDoc); }}
      }}).then(function (canvas) {{
        canvas.toBlob(function (blob) {{
          if (!blob) {{
            alert("导出失败：无法生成图片数据。");
            btn.disabled = false;
            btn.textContent = label;
            return;
          }}
          var url = URL.createObjectURL(blob);
          var a = document.createElement("a");
          a.href = url;
          a.download = fname;
          a.rel = "noopener";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          btn.disabled = false;
          btn.textContent = label;
        }}, "image/png");
      }}).catch(function (err) {{
        console.error(err);
        alert("生成长图失败：" + (err && err.message ? err.message : String(err)));
        btn.disabled = false;
        btn.textContent = label;
      }});
    }});
  }})();
  </script>
</body>
</html>
"""


def main() -> None:
    roster_rows = load_roster_rows()
    days = load_days()
    if not roster_rows:
        raise SystemExit("roster empty")
    roster_names = sort_roster_names_by_pinyin(roster_rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_html(roster_names, days), encoding="utf-8")
    print(f"Wrote {OUT} ({len(roster_names)} students × {len(days)} days, 按拼音排序)")


if __name__ == "__main__":
    main()
