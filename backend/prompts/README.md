# Backend Prompts 目錄說明

`backend/prompts/` 集中管理 AI 能力所使用的 prompt template、輸入說明與 prompt 組裝 helper。此目錄的目標是讓模型規則與文字組裝有明確歸屬，避免 prompt 分散在 chain、service 或 route 之中。

## 責任範圍

本目錄應負責以下內容：

1. prompt 固定規則
2. 模型任務描述與輸出格式要求
3. few-shot 或範例文字
4. 將動態資料整理成 prompt 文字的 helper

以下內容不應放在本目錄：

1. graph 節點流程控制
2. 商業流程判斷
3. 工具註冊與 handler 呼叫
4. repository / database 查詢

## 相鄰目錄邊界

1. `chains/` 負責決定何時呼叫模型與流程如何分支。
2. `services/` 負責業務上要執行什麼行為。
3. `prompts/` 負責模型在某一步看到什麼規則與文字內容。

## 撰寫原則

1. 固定規則與輸出格式應集中在本目錄。
2. 需要將多筆資料整理成可讀 prompt 時，可在本目錄實作 builder helper。
3. helper 應只處理「如何描述給模型」，不處理商業決策。
4. prompt 格式變動時，應同步檢查相關解析器、契約與 consumer。
