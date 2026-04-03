#!/bin/bash
set -e

# 移到後端目錄
cd "$(dirname "$0")/backend"

echo "🚀 prajekt 應用啟動..."
echo "📍 當前環境: $FLASK_ENV"
echo "📂 工作目錄: $(pwd)"

# 確保依賴安裝（Railway 下可能需要重新安裝）
echo "📦 確保後端依賴..."
pip install --no-cache-dir -r requirements.txt

# 套用資料庫 Migration（PostgreSQL 主線）
echo "🗄️  套用資料庫 Migration..."
python -m flask --app app.py db upgrade

echo "✅ 後端準備就緒"

# 啟動 Flask + Socket.IO 應用
echo "🎯 啟動 Flask + Socket.IO 後端..."

# 生產環境使用 gunicorn + eventlet，開發環境直接運行
if [ "$FLASK_ENV" = "production" ]; then
  echo "📡 生產模式: 使用 gunicorn + eventlet..."
  exec gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT --access-logfile - app:app
else
  echo "🔧 開發模式: 使用 Werkzeug..."
  exec python app.py
fi
