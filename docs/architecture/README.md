# Architecture 目錄說明

`docs/architecture/` 存放長期有效的系統設計、責任邊界、資料流、分層原則與技術決策。這裡回答「系統為什麼這樣分」與「責任應該放在哪裡」。

## 責任範圍

1. 前後端分層、backend layer、service / repository / contract 邊界。
2. 資料模型、資料流、權限邊界與跨模組關係。
3. 長期設計原則與重要技術決策紀錄。
4. 會影響多個 Phase 的架構性說明。

## 相鄰目錄邊界

1. 階段執行計畫放 `docs/phases/`。
2. API、payload、錯誤碼與 OpenAPI 查表放 `docs/reference/`。
3. 可照步驟操作的流程放 `docs/runbooks/`。
4. 暫緩構想或尚未驗證的方向放 `docs/future/`。

## 維護原則

1. architecture 文件應避免變成流水帳。
2. 若描述的是當前實作狀態，需能指向主要程式入口或 reference 文件。
3. 若描述的是未來方向，應標明是提案、決策或已落地狀態。
4. 當實作邊界改變時，優先更新仍會被後續開發引用的架構文件。
