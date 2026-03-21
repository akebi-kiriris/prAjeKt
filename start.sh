#!/bin/bash
set -e

# 移到後端目錄
cd "$(dirname "$0")/backend"

echo "🚀 LearnLink 應用啟動..."
echo "📍 當前環境: $FLASK_ENV"
echo "📂 工作目錄: $(pwd)"

# 確保依賴安裝（Railway 下可能需要重新安裝）
echo "📦 確保後端依賴..."
pip install --no-cache-dir -r requirements.txt

# 初始化資料庫（如果需要）
if [ ! -f ".db_init_done" ]; then
  echo "🗄️  初始化資料庫..."
  python init_db.py
  touch .db_init_done
fi

echo "✅ 後端準備就緒"

# 啟動 Flask + Socket.IO 應用（使用 Gunicorn + eventlet 作為生產伺服器）
echo "🎯 啟動 Flask + Socket.IO 後端（Gunicorn + eventlet）..."
exec gunicorn --worker-class eventlet -w 1 --bind "0.0.0.0:${PORT:-5000}" "app:create_app()"
