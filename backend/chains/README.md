# Backend Chains 目錄說明

`backend/chains/` 負責 AI 與 agent 的流程控制，包含 LangGraph state、節點執行、graph 接線，以及部分 LLM chain 的流程編排。

## 責任範圍

本目錄應負責以下內容：

1. agent 狀態如何在節點間流動
2. 工具執行順序與錯誤路由
3. LLM / chain 的流程編排
4. graph 的 entry point 與 conditional edge

以下內容不應放在本目錄：

1. 具體資料庫讀寫
2. 大量核心商業邏輯
3. 前端互動細節

## 相鄰目錄邊界

1. 若問題是流程分支、tool 選擇或錯誤後續處理，優先看本目錄。
2. 若問題是某個能力真正如何建立資料或更新狀態，應回到 `backend/services/`。
3. 若問題是工具 schema 或 envelope 邊界，應先檢查 `backend/contracts/`。
4. 若問題是 prompt 內容與模型規則，應檢查 `backend/prompts/`。

## 維護原則

1. chain 應聚焦在流程控制，不重複實作 service 已有邏輯。
2. 節點間狀態欄位與轉移規則應保持清楚、可追蹤。
3. 當流程依賴契約或 prompt 改動時，應同步檢查相鄰目錄。
