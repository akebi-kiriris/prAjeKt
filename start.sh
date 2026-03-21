#!/bin/bash
set -e

echo "🚀 LearnLink 應用啟動..."
echo "📍 當前環境: $FLASK_ENV"

# 後端設定
cd backend

echo "📦 安裝後端依賴..."
pip install --no-cache-dir -r requirements.txt

echo "🗄️  初始化資料庫..."
python init_db.py

echo "✅ 後端準備就緒"
cd ..

# 啟動後端（前台運行，讓 Railway 管理進程）
echo "🎯 啟動 Flask + Socket.IO 後端..."
cd backend
python app.py
