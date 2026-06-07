# backend/services/contracts

這層負責定義 service 與 agent tool 的資料契約，重點是讓輸入輸出有明確 schema，而不是任意 `dict`.

## 主要檔案

- `task_contracts.py`: 任務相關 request schema 與欄位驗證
- `timeline_contracts.py`: 專案 / 衝突檢查等 schema 與欄位驗證
- `tool_inputs.py`: agent tools 的輸入 model
- `tool_outputs.py`: agent tools 成功輸出 model
- `tool_envelopes.py`: agent tools 成功 / 失敗外層包裝

## 這層應該負責什麼

- 欄位型別定義
- 必填 / 選填規則
- 格式檢查與正規化
- agent tool 的穩定 I/O 契約

## 不應該放什麼

- 真正的商業邏輯
- 資料庫查詢
- HTTP route 邏輯
- LangGraph 節點流程控制

## 撰寫原則

- 優先用 Pydantic model 明確定義欄位
- 需要拒絕未知欄位時，使用 `ConfigDict(extra="forbid")`
- 單欄位格式修正或清洗可放 validator
- 跨欄位關係驗證可放 model validator

## 修改判斷

- 使用者輸入該收哪些欄位、欄位格式怎麼驗證：改這裡
- 工具成功回傳的 `data` 結構要怎麼固定：改這裡
- 若只是 service 內部計算流程改變，但對外契約沒變，通常不用動這層
