# 参考：文件与字段

## 路径（相对仓库根）

| 路径 | 说明 |
|------|------|
| `roster.csv` | `rank`, `name`；打卡表只认 `name` |
| `attendance/YYYY-MM-DD.json` | 单日数据 |
| `build_attendance_grid.py` | 聚合 JSON → 生成 HTML |
| `attendance/分享_体育作业打卡.html` | 输出；需联网时可用 html2canvas 导出 PNG |

依赖：`pypinyin`（脚本排序与生成表）。

## JSON 常用字段

| 字段 | 说明 |
|------|------|
| `date` | `YYYY-MM-DD` |
| `activity` | 展示用标题，如「4月19日数学作业」 |
| `present` | 花名册姓名列表（规范名） |
| `absent` | 当日未打卡花名册姓名 |
| `roster_count` | 花名册总人数（当前多为 52） |
| `roster_present_count` | 建议与 `len(present)` 一致 |
| `app_completed_count` | App 显示「已完成」人数，可与花名册人数不同 |
| `unmatched_in_app` | 尚未映射到花名册的 app 昵称/行 |
| `mapping_notes` | 别名与业务备注（审计用） |

## HTML 表（由脚本生成）

- 日期列：`present` 含该生则 🏆。
- 4.16 与 4.17 之间空白列：前 **四个日期列**（数据中为 4.13～4.16）均打卡则 🚩。
- 4.19 列后空白列：**4.17、4.18、4.19** 三天均打卡则 🚩。

具体列位置与历史兼容逻辑以 `build_attendance_grid.py` 源码为准。
