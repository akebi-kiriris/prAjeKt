refactor: 整理 README 與 docs 結構並收斂本地啟動腳本

本次提交聚焦專案首頁與文件結構整理，不是功能新增，而是把 repo 入口、docs 落點與本地腳本位置收斂到更一致的狀態，方便後續維護與提交。

---

一、README 與專案入口收斂

- 重寫 `README.md` 開頭結構
  - 改為先介紹專案目的、想解決的問題與核心能力
  - 將首頁內容收斂成較適合對外閱讀的版本
  - 保留技術架構、專案結構、快速啟動與文件入口

- 補強 root 檔案定位
  - README 內明確保留 `docker-compose.yml`、`mcp_server.py`、`requirements.txt` 等 repo-level 入口檔
  - 將平台設定檔與一般文件的角色分開說明

---

二、docs 結構整理

- 將原本散在 root 的正式文件收回 `docs/`
  - `架構與責任邊界.md` → `docs/architecture/架構與責任邊界.md`
  - `API_契約與錯誤處理.md` → `docs/reference/API_契約與錯誤處理.md`
  - `本地開發測試部署_Runbook.md` → `docs/runbooks/本地開發測試部署_Runbook.md`
  - `commit-message.md` / `commit_message_zh.md` → `docs/guides/`

- 移除 root 重複文件
  - `重構計畫.md`
  - `進度追蹤.md`
  - 後續以 `docs/重構計畫.md`、`docs/進度追蹤.md` 為正式版本

- 同步修正文件引用
  - README 與 runbook 改指向新的 `docs/` 路徑
  - Firebase / Railway 相關 runbook 內容校正為目前 repo 的實際設定

---

三、本地腳本與素材位置整理

- 將 Windows 本地啟動腳本移到 `scripts/dev/`
  - `bootstrap_pg_local.bat`
  - `start_all.bat`
  - `start_mcp_inspector.bat`

- 腳本內容同步調整
  - 改為從 `scripts/dev/` 正確回到 repo root 執行
  - README / runbook 內的示例命令同步改為新位置

---

四、ignore 規則整理

- `.gitignore` 改為：
  - `docs/` 正式文件可追蹤
  - 只忽略 `docs/.obsidian/`
  - 只忽略 `docs/assets/`
  - 只忽略 `docs/learning/`，但各目錄 `README.md` 仍可追蹤

- 讓 docs 後續不再因為「整個目錄先 ignore 再局部放行」而難以維護

---

五、補充

- 本輪主要是文件與 repo 結構整理，未新增功能邏輯
- 本輪未重新跑測試；若提交範圍維持文件/腳本整理，通常可接受
- commit 前請留意目前因 ignore 規則調整而浮出的未追蹤 docs，避免誤把整批歷史文件一起加入
