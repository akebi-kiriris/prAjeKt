#!/usr/bin/env python
"""初始化資料庫 - 直接建立所有表格"""

import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_DIR))

# 本地初始化預設使用 SQLite，若外部已指定 DATABASE_URL 則沿用
os.environ.setdefault("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'instance' / 'prajekt.db'}")
from app import create_app
from models import db

def init_database():
    """直接建立資料庫表格"""
    app = create_app()
    with app.app_context():
        print("正在建立資料庫表格...")
        try:
            db.create_all()
            print("✅ 資料庫初始化成功！")
            return True
        except Exception as e:
            print(f"❌ 資料庫初始化失敗: {e}")
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
