# Phase 5 AI 技術路線與學習計畫

> 建立日期：2026/03/16
> 用途：作為 PrAjeKt Phase 5 的討論底稿（技術選型、實作工具、學習節奏、深度目標）

---

## 1) 目標定位（先定義這一輪要贏在哪）

Phase 4 已聚焦 WebSocket 即時能力；Phase 5 建議聚焦「AI 產品化能力」。

本階段目標：
- 把 AI 從「功能」升級為「可持續迭代的系統」。
- 建立可以展示、可量化、可部署的成果（不只 demo）。
- 為後續部署整合鋪路（含 PostgreSQL、監控、安全、回滾）。

**本期決策（已確認）：**
- 產品主線只做 A / B（n8n+MCP、Prompt+CoT）。
- C 之後不硬塞進 PrAjeKt 主線，以「學習支線 Lab」方式推進。

---

## 2) Phase 5 推薦主題（依產品價值排序）

### A. n8n + MCP 工作流整合（優先級 P0）

價值：最快看到產出，能直接落地到 PrAjeKt。

可做功能：
- 任務逾期提醒自動化（排程 -> 查詢 -> 推播）。
- 每日/每週摘要（彙整專案進度 -> 生成人話報告 -> 發送）。
- AI 任務拆解 pipeline（輸入需求 -> 生成任務 -> 人審核 -> 入庫）。

推薦工具：
- n8n（workflow 編排）
- MCP server（統一工具介面）
- Redis（排程/快取，可選）

實作方式：
- 先做 2 條 workflow（提醒 + 週報）
- 每條都補「失敗重試、告警、審計 log」

---

### B. Prompt Engineering + CoT 推理品質提升（優先級 P0）

價值：立刻提升 AI 回答穩定度與可控性。

可做功能：
- 任務生成提示模板（角色、約束、輸出 schema）。
- 多輪提問策略（釐清上下文 -> 再生成）。
- 推理結果自評（是否缺欄位、是否可執行）。

推薦工具：
- OpenAI / Azure OpenAI / Gemini API
- Pydantic 或 JSON Schema（結構化輸出）
- Promptfoo 或自建評測腳本

實作方式：
- 建立 prompt 版本管理（v1/v2/v3）
- 用固定測例集比較輸出品質（正確率、可執行率）

---

### C. 微調與部署（LoRA/QLoRA）(優先級 P1)

價值：進入真正 AI 工程能力，履歷加分明顯。

可做功能：
- 「專案管理語境」微調（任務拆解、優先級判斷、風險描述）。
- 微調模型對比 base model（勝率、格式合規率）。

推薦工具：
- Hugging Face Transformers + PEFT
- Unsloth / Axolotl（降低訓練門檻）
- vLLM / TGI（推理部署）
- Gradio / Streamlit（快速 demo）

實作方式：
- 先小資料集做 LoRA baseline
- 做 A/B 測試再決定是否擴資料

---

### D. Agent Security（含越獄攻擊基礎）(優先級 P1)

價值：只要做 Agent，安全就是必要課。

可做功能：
- Prompt Injection 測試集
- 工具呼叫權限白名單
- 風險動作二次確認（human-in-the-loop）

推薦工具：
- OWASP LLM Top 10（基準）
- Garak / 自建紅隊腳本
- Policy engine（規則判斷）

實作方式：
- 每個 workflow 補 threat model
- 定義「拒答策略 + 降級策略 + 人工接管」

---

### E. 多模態（文件/截圖 -> 任務）(優先級 P2)

價值：產品體驗升級感強。

可做功能：
- 上傳會議截圖/PDF，自動抽行動項。
- 附件摘要 + 風險點提取。

推薦工具：
- Gemini 1.5+/2.x、GPT-4.1/4o、Claude 3.5+
- OCR（Tesseract/Azure Vision，可選）

實作方式：
- 先做「單文件解析 -> 任務草稿」
- 再做「多文件融合摘要」

---

### F. GUI Agent（操作自動化）(優先級 P2)

價值：很吸睛，但工程與安全成本較高。

推薦工具：
- Playwright（穩定）
- Browser-use/自建 agent loop

實作方式：
- 僅限低風險操作（查詢、草稿）
- 禁止直接做高風險寫入操作

---

## 3) 雙軌策略：主線交付 + 學習支線

### 3.1 主線（只影響 PrAjeKt 產品）
- A. n8n + MCP 工作流整合
- B. Prompt Engineering + CoT

主線原則：
- 只做可直接提升專案價值的功能。
- 每兩週必須有可 demo 的成果。
- 不引入高維運成本元件（先避免自訓模型上線）。

### 3.2 學習支線（你想學的 C+ 題目）
- C. 微調與部署
- D. Agent Security / 越獄攻擊
- E. 多模態
- F. GUI Agent
- 研究向：知識編輯、模型水印、隱寫、數學推理蒸餾

支線原則：
- 一律先在獨立 Lab 做 PoC，不直接進主專案。
- 驗證通過後再評估是否回流產品。
- 每個 Lab 只做 1 個可量化目標（避免太散）。

---

## 3.3 C 之後「想學又不想污染主線」的做法

建議建立獨立目錄：
- `labs/phase5-ai/finetune-lora/`
- `labs/phase5-ai/agent-security/`
- `labs/phase5-ai/multimodal/`

每個 Lab 固定四個檔：
- `README.md`：目標與背景
- `runbook.md`：執行步驟
- `eval.md`：評測指標與結果
- `report.md`：結論（是否回流主專案）

回流門檻（符合才回主線）：
- 品質達標（例如格式合規率 >= 95%）
- 成本可接受（每次請求可估算）
- 有安全保護（最少含 prompt injection 防護）
- 能維運（有日誌、故障時可回退）

---

## 4) 12 週學習與實作計畫（A/B 主線 + C+ 支線）

### 第 1-2 週：A 主線啟動（n8n + MCP）
- 完成 Phase 4 WebSocket 收尾（群組訊息/通知即時化）
- n8n 上線 1 條 workflow（逾期提醒）
- 產出：可重跑流程、可追蹤日誌

### 第 3-4 週：B 主線啟動（Prompt + CoT）
- 建立任務生成 prompt 模板庫
- 建立 30-50 筆評測樣本
- 產出：v1/v2 對比報告（格式合規率、可執行率）

### 第 5-6 週：A/B 擴充 + C 支線起跑
- 把常用能力包成 MCP tools（查任務、寫任務、查專案）
- 串進 n8n workflow
- 支線開始 LoRA 小型實驗（不進主線）
- 產出：至少 3 個可用 tools + 1 份 LoRA baseline 報告

### 第 7-8 週：D 支線（安全）
- 設計越獄與注入測試集
- 對主線 A/B 補上防護規則
- 產出：安全測試報告 + 修補清單

### 第 9-10 週：E/F 支線（多模態或 GUI Agent 二選一）
- 多模態：附件解析成任務草稿
- 或 GUI Agent：低風險自動化流程
- 產出：PoC demo + 成本/風險評估

### 第 11-12 週：收斂與回流決策
- 比較所有支線實驗的 ROI
- 決定 1 項回流 Phase 6 或部署階段
- 產出：技術決策紀錄（ADR）

---

## 5) 深度分級（避免學太散）

### Level 1（能做）
- 會調 API、會寫 prompt、會串 workflow
- 有可跑 demo

### Level 2（能優化）
- 會做評測、A/B、成本與延遲權衡
- 有品質指標（準確率/失敗率/latency）

### Level 3（能工程化）
- 會做安全、可觀測性、版本化、回滾
- 可上線並可維運

建議目標：
- 12 週內達到「2 個 Level 2 + 1 個 Level 3」

---

## 6) PrAjeKt 可落地的 5 個 AI 功能提案

1. 智能週報生成器
- 輸入：專案與任務資料
- 輸出：本週進度、風險、下週建議

2. 任務拆解副駕駛
- 輸入：需求描述
- 輸出：任務清單、優先級、估時、依賴

3. 會議紀錄 -> 任務草稿
- 輸入：文字/PDF/截圖
- 輸出：可審核任務草稿

4. 智能風險預警
- 根據延期、阻塞關鍵詞、自動偵測高風險任務

5. 智能 SOP 建議
- 根據任務類型推薦處理流程與檢查清單

---

## 7) 建議技術棧（Phase 5 版本）

核心：
- LLM API：OpenAI / Azure OpenAI / Gemini（擇一主力 + 一個備援）
- Workflow：n8n
- Agent tools：MCP
- Eval：prompt 評測腳本 + 指標看板

進階：
- Fine-tuning：Transformers + PEFT
- Inference：vLLM
- Observability：OpenTelemetry + Grafana / Langfuse（可選）

---

## 8) 驗收指標（每個子題至少對齊一個）

- 產出品質：格式合規率 >= 95%
- 任務可執行率：>= 80%
- 回應延遲：P95 < 5s（線上模式）
- 成本：單次請求成本可追蹤且可預估
- 安全：關鍵攻擊測例攔截率 >= 90%

---

## 9) 討論決策欄（每次會議更新）

- [ ] 主力模型供應商
- [ ] n8n 部署方式（cloud/self-host）
- [ ] MCP tool 邊界（可讀/可寫）
- [ ] 微調資料來源與隱私規範
- [ ] 安全測試範圍與通過門檻

---

## 10) 下一步（建議本週完成）

1. 鎖定主線 A/B 的第一個里程碑（提醒 workflow + 任務生成 prompt v1）
2. 建立 `labs/phase5-ai/`，把 C 之後主題都先放在 Lab，不直接改主專案
3. 先開兩份評測：`prompt-eval`（主線）與 `lab-eval`（支線）
4. 設定固定節奏：每週主線 demo、雙週支線分享
