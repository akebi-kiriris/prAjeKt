# Phase 6 RAG 評測紀錄

## 大綱

1. 目的
2. 共用評測規則
3. RAG-A（Task Comment Summary）評測表
4. RAG-B（Group Snapshot）評測表
5. 匯總表模板
6. 目前狀態

---

## 1) 目的

本文件用來記錄 Phase 6 的 RAG 功能評測結果。

- RAG-A：任務留言摘要的品質與穩定性
- RAG-B：群組快照 Digest 的準確度、可追溯性與可執行性

---

## 2) 共用評測規則

每個維度使用 1-5 分：

- 1 分：很差
- 2 分：偏弱
- 3 分：可接受
- 4 分：良好
- 5 分：優秀

核心維度：

- 準確度（Accuracy）：是否忠於原始訊息內容
- 可追溯性（Traceability）：是否可回溯到 message_id 或明確留言
- 可執行性（Actionability）：是否能給出可落地的下一步
- 精簡度（Conciseness）：是否簡潔、避免重複廢話
- 安全性（Safety）：是否杜撰、是否洩漏敏感資訊

建議通過門檻：

- 平均分 >= 4.0
- 任一維度不得低於 3.0

---

## 3) RAG-A（Task Comment Summary）評測表

### 3.1 輸入資訊

| 欄位 | 值 |
|---|---|
| 日期 | YYYY-MM-DD |
| 評測者 | |
| Task ID | |
| 留言數量 | |
| Provider / Model | |

### 3.2 評分

| 維度 | 分數（1-5） | 備註 |
|---|---:|---|
| 準確度 | | |
| 可追溯性 | | |
| 可執行性 | | |
| 精簡度 | | |
| 安全性 | | |

### 3.3 快速檢查

- `decisions` 是否只包含留言中真實決議
- `risks` 是否真實反映阻塞或潛在風險
- `next_actions` 是否具體且可執行，而非泛泛敘述

---

## 4) RAG-B（Group Snapshot）評測表

### 4.1 輸入資訊

| 欄位 | 值 |
|---|---|
| 日期 | YYYY-MM-DD |
| 評測者 | |
| Group ID | |
| Window days | |
| Source message count | |
| Provider / Model | |

### 4.2 評分

| 維度 | 分數（1-5） | 備註 |
|---|---:|---|
| 準確度 | | |
| 可追溯性 | | |
| 可執行性 | | |
| 精簡度 | | |
| 安全性 | | |

### 4.3 Digest 專項檢查

- `digest.overview` 是否抓到真正優先事項
- `digest.todo_for_user` 是否具體、可立即執行
- `digest.watch_out` 是否捕捉到真實阻塞點
- `digest.decisions_brief` 是否短而不重複

---

## 5) 匯總表模板

可用下表整理多輪評測：

| Run ID | 功能 | 準確度 | 可追溯性 | 可執行性 | 精簡度 | 安全性 | 平均 |
|---|---|---:|---:|---:|---:|---:|---:|
| run-001 | RAG-A | | | | | | |
| run-002 | RAG-B | | | | | | |

---

## 6) 目前狀態

- RAG-A 評測模板已就位。
- RAG-B 評測模板已就位。
- 歷史手動評分資料待補。
