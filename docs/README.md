# Docs 索引與目錄規範

這份文件的目的，是把 `docs/` 的結構定下來，並把原本散在根層的大部分文件先收進分類目錄。
之後新增文件時，就有一致的落點；舊文件若還要再調整，也能在這個骨架上慢慢整理。

---

## 目前問題

現在 `docs/` 裡的文件大致可用，但有幾個明顯問題：

1. 根層文件過多，主題混雜
2. Phase 規劃、架構說明、操作手冊、學習筆記都放在同一層
3. 有些文件是正式專案文檔，有些其實是個人學習或暫存筆記
4. 新文件如果沒有固定落點，之後會越堆越亂

所以這輪做的事情分成兩部分：

1. 建立分類目錄
2. 建立索引與放置規則
3. 先把大部分根層文件搬進分類目錄
4. 補主要入口文件的路徑引用

---

## 建議目錄結構

```text
docs/
├── README.md                 # docs 索引與規範
├── changelog/                # 歷史改動日誌
├── workflows/                # AI workflow / tool workflow 範例
├── future/                   # 未來可做的改進草稿與 backlog 提案
├── phases/                   # 分階段規劃、詳解、總整理
├── architecture/             # 架構、分層、資料流、設計說明
├── runbooks/                 # 部署、遷移、排障、操作手冊
├── reference/                # API、錯誤碼、payload 契約、環境參考
├── guides/                   # 開發流程、Git/CI/CD、文件流程規範
├── learning/                 # 個人學習筆記、課程整理、面試複習
├── assets/                   # 圖片、附件等非 markdown 資源
└── .obsidian/                # Obsidian 本地設定（保留）
```

---

## 各目錄用途

### `docs/phases/`

放真正屬於專案主線的 phase 文件，例如：

1. `Phase8_5_service複雜度收斂與Pydantic契約計畫_2026-05-27.md`
2. `Phase9_5_模型提案式Plan與Replan強制二次確認規劃_2026-06-02.md`
3. `Phase9_Agent系統設計與實作全紀錄_2026-06-04.md`

適合放：

1. phase 規劃
2. phase 詳解
3. phase 收斂總結
4. 某一階段的補測/修復計畫

---

### `docs/architecture/`

放比較偏「系統設計與責任邊界」的文件，例如：

1. 後端分層與交易邊界
2. RAG 架構流程
3. Agent 系統設計
4. 資料庫設計

適合放：

1. 模組責任
2. 資料流
3. 分層規則
4. 長期有效的設計說明

---

### `docs/future/`

放「已經有方向，但還不打算立即實作」的改進草稿與 backlog 提案，例如：

1. Agent prompt / planner 拆分方向
2. 某個功能的下一版重構提案
3. 某個流程未來可觀測性、評測、成本優化想法
4. 臨時想到但還不想打進 phase 主線的改善清單

適合放：

1. 未來改進方向
2. backlog 類提案
3. prompt / workflow 優化草稿
4. 後續待驗證的設計想法

---

### `docs/runbooks/`

放「實際操作手冊」與「出問題時怎麼排查」的文件，例如：

1. 本地開發環境建置
2. PostgreSQL 遷移流程
3. Deployment safety
4. collation mismatch 排查

適合放：

1. 部署
2. migration
3. troubleshooting
4. 手動操作步驟

---

### `docs/reference/`

放高頻查表型文件，例如：

1. `reference/api_endpoints.md`
2. `reference/API_錯誤碼表.md`
3. `reference/payload-contracts.md`
4. `reference/env_and_ports.md`

適合放：

1. API 端點
2. 錯誤碼
3. payload/schema 契約
4. 環境變數與 port 對照

---

### `docs/guides/`

放開發流程與協作規範，例如：

1. `CI_CD_最小流程.md`
2. `Git提交流程規範_給我自己的最小版.md`
3. `文件更新與發布流程.md`

適合放：

1. Git 流程
2. CI/CD 流程
3. 文件同步規則
4. 提交/發布規範

---

### `docs/learning/`

放個人學習筆記與面試準備，不直接視為專案正式文檔，例如：

1. HF Agents / MCP / LangGraph 學習筆記
2. TypeScript / CSS / SQL / Socket.IO 筆記
3. 面試複習清單

這一類文件保留很有價值，但不應和正式 phase 文檔混在根層。

---

### `docs/assets/`

放圖片、附件與非 markdown 資源，例如：

1. `headshot.jpg`
2. 未來若有架構圖、流程圖截圖、示意圖，也建議放這裡

---

## 根目錄文件原則

目前專案根目錄建議只保留：

1. `README.md`
2. 平台/部署設定：`docker-compose.yml`、`firebase.json`、`.firebaserc`、`railway.json`、`Procfile`
3. 啟動入口：`mcp_server.py`、`start.sh`
4. Root 依賴清單：`requirements.txt`

其他正式 Markdown 文件原則上都放在 `docs/` 內維護，避免出現 root 與 `docs/` 雙份內容漂移。
本地 Windows 啟動腳本統一收在 `scripts/dev/`，圖片與附件統一收在 `docs/assets/`。

---

## 新文件放置規則

從現在開始，新增文件可先遵守下面規則：

1. **Phase 規劃 / 階段總結**
   - 放 `docs/phases/`

2. **長期架構說明 / 設計紀錄**
   - 放 `docs/architecture/`

3. **部署 / 遷移 / 排障 / 啟動手冊**
   - 放 `docs/runbooks/`

4. **未來想做但暫不實作的提案 / backlog**
   - 放 `docs/future/`

5. **API / 錯誤碼 / payload / env**
   - 放 `docs/reference/`

6. **Git / CI/CD / 文件流程**
   - 放 `docs/guides/`

7. **學習筆記 / 面試整理 / 雜記**
   - 放 `docs/learning/`

8. **圖片 / 資源**
   - 放 `docs/assets/`

---

## 已完成的第一輪搬移

目前已完成的搬移方向如下：

### 已搬到 `docs/reference/`

1. `reference/api_endpoints.md`
2. `reference/API_錯誤碼表.md`
3. `reference/payload-contracts.md`
4. `reference/env_and_ports.md`

### 已搬到 `docs/guides/`

1. `CI_CD_最小流程.md`
2. `Git提交流程規範_給我自己的最小版.md`
3. `Git_指令完全指南.md`
4. `文件更新與發布流程.md`
5. `commit-message.md`
6. `commit_message_zh.md`

### 已搬到 `docs/runbooks/`

1. `完整啟動指南.md`
2. `quickstart.md`
3. `本地開發測試部署_Runbook.md`
3. `DEPLOYMENT_SAFETY_2026-04-04.md`
4. `Phase5_1_PostgreSQL遷移流程.md`
5. `Phase5_2_Railway後端部署.md`
6. `Phase5_3_Firebase前端部署.md`
7. `Phase6_0_開發資料庫遷移流程.md`
8. `phase6-local-setup.md`
9. `Phase7_3_collation_mismatch_runbook.md`

### 已搬到 `docs/phases/`

1. 所有 `Phase*.md`
2. 所有 `phase*.md`

### 已搬到 `docs/architecture/`

1. `資料庫設計.md`
2. 多份後端抽象 / 分層 / transaction / 體檢 / 收斂報告
3. `WebSocket_群組即時聊天計畫.md`
4. `專案封箱與下一步建議.md`
5. `plan-taskPayloadDecoupling.prompt.md`
6. `架構與責任邊界.md`

### 已搬到 `docs/reference/`

1. `API_契約與錯誤處理.md`

### 已搬到 `docs/learning/`

1. 大部分學習筆記、面試複習、雜記、測試筆記、履歷/學習整理

### 已搬到 `docs/assets/`

1. `headshot.jpg`
2. `prajekt.db`
3. `吳育嘉 履歷.html`

---

## 下一批建議整理名單

這一批之後如果還要再收斂，可以優先處理：

1. `workflows/` 底下是否再細分 `ai/`、`agent/`
2. `learning/` 是否再拆成：
   - `frontend/`
   - `backend/`
   - `ai/`
   - `career/`
3. `architecture/` 是否再拆成：
   - `backend/`
   - `ai/`
   - `data/`
4. 是否建立 `docs/archive/`，專門放舊版但仍想保留的歷史文件

---

## 這輪整理原則

這輪已做到：

1. 建立新目錄骨架
2. 補 `docs/README.md` 當總索引與規範
3. 將大部分根層文件搬進分類目錄
4. 修正主索引與部分 phase 文件的舊路徑

這輪先不做：

1. 全 repo 所有純文字引用路徑全面重寫
2. Obsidian 內部連結整理
3. 第二層子資料夾再細拆

這樣比較穩，也比較符合目前專案仍在持續開發中的節奏。
