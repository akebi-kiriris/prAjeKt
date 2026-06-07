# Phase 9.1：Type Hint 基線收斂（MVP 規劃）

> 日期：2026-05-28  
> 階段定位：Phase 9 第一階段（先把型別邊界補齊）  
> 對齊說明：本文件只覆蓋 9.1；Tool Calling / LangGraph Agent 併入 Phase 9 後續子階段

---

## 目標

1. 完成後端核心模組 type hints 基線，降低維護成本。
2. 建立可持續擴展的型別別名與契約放置規範。
3. 為 9.2 Docstring、9.3 Tool Calling 做型別前置。

---

## 非目標（9.1 先不做）

1. 不做 Tool Registry 與 tool schema 契約化實作（移至 9.3）。
2. 不做 LangGraph graph 節點與 agent runtime 實作（移至 9.3/9.4）。
3. 不做跨服務拆分與平台化（非 Phase 9.1 範圍）。

---

## 實作順序（固定）

1. **核心模組型別盤點**
2. **Type Hint 補齊與型別別名收斂**
3. **靜態檢查基線（局部 mypy/pyright）**
4. **最小驗收與文件同步**

---

## 工作拆解

### Step 1：核心模組型別盤點（優先）

目標：先把「邊界」型別補齊，不追求一次覆蓋所有舊碼。

1. 盤點下列模組的 public function/class 邊界是否缺型別：
   - `backend/repositories/`
   - `backend/services/transactions.py`
   - `backend/blueprints/validation.py`
   - `backend/services/task_service.py`（核心入口）
   - `backend/services/timeline_service.py`（核心入口）
2. 建立型別缺口清單（可用 TODO 區塊或文件清單）。

完成定義：
1. 以上模組 public 邊界都有型別或明確註記待補。
2. 可清楚列出本波納入範圍與延後範圍。

---

### Step 2：Type Hint 補齊與型別別名收斂

目標：避免同型別重複宣告，並讓 service/repository 介面可推導。

1. 為常見輸入/輸出建立型別別名（如 `JSONDict`、`TaskPayloadLike`）。
2. 補齊 service 核心入口函式：
   - 參數型別
   - 回傳型別
   - 可能拋出的 domain error 型別
3. 補齊 repository helper 的回傳型別，減少 `Any` 擴散。

完成定義：
1. `task_service.py` / `timeline_service.py` 的核心入口函式具完整 type hints。
2. 新增型別別名後，重複型別字串明顯下降。

---

### Step 3：靜態檢查基線（局部）

目標：先讓核心範圍通過靜態檢查，不追求全專案一次到位。

1. 為 Phase 9.1 設定局部檢查範圍（上述模組）。
2. 修正高價值型別問題：
   - Optional 未處理
   - dict/list 元素型別缺失
   - 不必要 `Any`
3. 保留無法立即收斂項目，標記於 follow-up。

完成定義：
1. 局部檢查範圍可穩定執行並可重現。
2. 型別告警數量有明確下降紀錄。

---

### Step 4：最小驗收與文件同步

目標：確保 9.1 交付可驗證，且與主計畫文件一致。

1. 補一組型別相關 smoke 檢查命令（局部）。
2. 更新 `重構計畫.md` / `進度追蹤.md` 的 9.1 狀態與範圍。
3. 在文件註明 9.2、9.3 的邊界，避免 9.1 scope 漂移。

完成定義：
1. 9.1 交付可由型別檢查與文件對照驗證。
2. 9.2/9.3 的後續工作項清楚可追蹤。

---

## 建議里程碑（9.1）

1. M1：核心模組型別缺口盤點完成。
2. M2：service/repository 主要 public API 補齊 type hints。
3. M3：局部靜態檢查基線可重現。

---

## 風險與對策

1. 風險：一次型別化範圍過大，進度卡住。  
   對策：只鎖定 AI 核心路徑與 public boundary。

2. 風險：一次想覆蓋全專案，導致反覆修補。  
   對策：嚴守 9.1 範圍，只做核心路徑。

3. 風險：與 Phase 9 其餘子項邊界不清，scope 漂移。  
   對策：9.1 只做型別，Tool/LangGraph 明確延後。

---

## 後續銜接

1. 9.2：Docstring 規範化（行為契約 + 邊界）。
2. 9.3：Tool Calling 契約化（schema、registry、smoke test）。
3. 9.4（可選）：LangGraph Agent MVP 串接。
