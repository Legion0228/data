---
name: math-homework-attendance
description: >-
  Maintains class math homework check-ins: edits per-day JSON under attendance/,
  maps app lines to roster.csv names, runs build_attendance_grid.py to refresh
  分享_体育作业打卡.html. Use when the user mentions 数学作业打卡, 作业打卡表,
  attendance JSON, 花名册对齐, 分享_体育作业打卡.html, build_attendance_grid,
  打卡人数, or daily homework completion in this repository.
---

# 数学作业打卡

## Quick start

1. **两阶段录入**：先只录 `present/absent`（人数与花名册对齐），再录 `grades`（A+/A/B）。
2. 编辑 `attendance/YYYY-MM-DD.json`：`present` 只放 **花名册规范姓名**，并整表重算 `absent`。
3. 别名写进 `mapping_notes`；未确定昵称先放 `unmatched_in_app`，用户确认映射后再并入并清空。
4. 等级录入时禁止猜测：看不清的条目先标记待确认，不得自行推断 A/A+。
5. 复核通过后再执行：`python3 build_attendance_grid.py`。
6. 向用户报告：HTML 打卡人数（`len(present)`）与（如有）`app_completed_count` 差异。
7. 默认只返回生成后的 HTML 路径/本地链接，方便用户自己打开打印或点“生成长图 PNG”；不要生成或返回视频、长图截图，除非用户明确要求。

## 防失误强制流程（严格执行）

1. **截图要求**：优先使用完整大图；若等级列不清晰，要求补发分段放大图。
2. **先名单后等级**：名单（谁打卡）与等级（A+/A/B）分两步处理，不混在一步完成。
3. **禁止默认推断**：未看清 `+` 号时不得把 `A` 当 `A+`，也不得反向推断。
4. **写入前自检**：输出 `A+`/`A`/`B` 三组名单与人数，先给用户确认后再最终落盘（或至少在同次操作中二次核对）。
5. **关键边界复核**：对分界处（A+→A、A→B）逐行二次检查。
6. **变更后核对**：重新生成 HTML 后，抽查 2-3 名学生图标是否与 JSON 一致。

## Task checklist（复制并逐项打勾）

```
- [ ] 已确认日期与对应 JSON 文件
- [ ] 名单与等级分两步处理（先 present/absent，后 grades）
- [ ] present 中姓名与 roster.csv 的 name 完全一致
- [ ] absent = 花名册 \ present（人数之和 = roster 总人数）
- [ ] grades 已做 A+/A/B 分组核对（无猜测条目）
- [ ] mapping_notes / unmatched_in_app 已更新
- [ ] 已运行 build_attendance_grid.py
- [ ] 已抽查 HTML 图标与 JSON 一致
- [ ] 已说明 HTML 人数与（如有）App 人数
- [ ] 已返回 HTML 路径/本地链接（默认不返回视频或长图截图）
```

## 不要做

- 手写 HTML 表体；显示规则以 `build_attendance_grid.py` 为准。
- 为未映射昵称增加表格行；等映射或保留在 `unmatched_in_app`。
- 在看不清截图时直接推断 A/A+/B。
- 用户未明确要求时，不要录制视频或导出长图截图；这会拖慢响应。

## Additional resources

- 字段与脚本行为细节：[reference.md](reference.md)
- 示例对话与映射示例：[examples.md](examples.md)
