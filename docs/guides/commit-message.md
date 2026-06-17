docs: 完成 Phase 10.4 與 10.5 契約文件整理

這次提交收尾 Phase 10.4 與 Phase 10.5，主軸是把前一輪契約收斂後的文件入口、OpenAPI 維護流程與主要模組閱讀路線整理清楚。這輪沒有修改 runtime code，重點是讓後續 10.6 清理鬆動點時，有穩定的參照文件與模組導覽可以回頭查。

---

一、Phase 10.4 契約文件與 OpenAPI 維護整理

- 新增：
  - `docs/phases/Phase10_4_契約文件與輸出層準備規劃_2026-06-17.md`
  - `docs/reference/Phase10_4_契約文件與OpenAPI維護整理_2026-06-18.md`

- 本輪整理重點：
  - 建立閱讀版契約狀態矩陣，將主要 API / 流程標記為：
    - `stable`
    - `partial`
    - `dynamic`
    - `binary`
    - `legacy-flexible`
  - 補齊主要模組的契約狀態索引：
    - `auth / profile`
    - `tasks`
    - `timelines`
    - `knowledge`
    - `groups / messages / notifications`
    - `todos / trash`
    - `copilot / agent`
    - `health`
  - 明確定義文件維護原則：
    - 文件是閱讀與維護入口，不取代 `backend/contracts/`
    - 主要 API 變更時，同步檢查 backend contract、frontend type / service / consumer、OpenAPI 輸出與 focused tests
    - dynamic / binary / legacy-flexible 區塊只標記現況，不硬包成假穩定 schema
  - 固定 OpenAPI 維護流程：
    - runtime 入口：`/api/openapi.json`
    - Swagger UI：`/api/docs`
    - 靜態匯出：`docs/reference/openapi.json`
    - 匯出指令：在 `backend/` 執行 `.\venv\Scripts\python.exe scripts\export_openapi.py`
    - focused test：在 `backend/` 執行 `.\venv\Scripts\python.exe -m pytest tests\services\test_response_contracts.py -q`

---

二、Phase 10.5 模組別主線導覽

- 新增：
  - `docs/phases/Phase10_5_模組別主線導覽規劃_2026-06-18.md`
  - `docs/reference/Phase10_5_模組別主線導覽整理_2026-06-18.md`

- 本輪整理重點：
  - 建立主要模組的閱讀路線，讓後續維護時能快速找到 frontend、backend、contract、service 與 tests 入口：
    - `tasks`
    - `timelines`
    - `knowledge`
    - `groups / messages / notifications`
    - `copilot / agent`
  - 補上輕量導覽：
    - `auth / profile`
    - `todos / trash`
  - 逐條整理各模組的主要檔案責任：
    - frontend view / component
    - frontend store / service / type
    - backend blueprint / contract / service
    - backend tests / frontend tests
  - 補出「目前最容易迷路的區塊」總表：
    - Timeline detail
    - timeline AI / RAG
    - Knowledge scope
    - group snapshot
    - message REST / socket serializer
    - copilot plan / execute
    - tool result
    - binary response
  - 補出 10.6 候選檢查點，將可能需要實作清理的鬆動點集中交接，不在 10.5 直接修程式

---

三、追蹤文件同步

- 調整：
  - `docs/重構計畫.md`
  - `docs/進度追蹤.md`

- 同步內容：
  - 將 Phase 10.4 checklist 標記為完成
  - 將 Phase 10.5 checklist 標記為完成
  - 補上 2026/06/18 Phase 10.4 完成紀錄
  - 補上 2026/06/18 Phase 10.5 完成紀錄
  - 將 Phase 10 下一步更新為可進入 10.6 殘留鬆動點清理，或先發布 10.4~10.5 文件 PR

---

四、驗證

- Phase 10.4：
  - OpenAPI 靜態匯出：PASS
  - 匯出後 `docs/reference/openapi.json` 無額外 diff
  - OpenAPI focused pytest：`6 passed`
  - 備註：測試期間僅出現 `.pytest_cache` 權限 warning，不影響結果

- Phase 10.5：
  - docs-only 更新
  - 未修改 runtime code
  - 未跑測試

---

五、補充

- 這次提交刻意只處理文件、索引、導覽與狀態同步，不提前進入 10.6 的實作清理
- `copilot / agent` dynamic payload、binary response、legacy-flexible list shape 等區塊已集中標記為後續檢查點
- 後續若進入 10.6，可以直接從 10.5 整理出的候選檢查點開始挑選最有價值的清理項目
