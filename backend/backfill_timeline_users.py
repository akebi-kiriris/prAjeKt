"""
backfill_timeline_users.py
--------------------------
補填舊資料：凡是 timelines 有記錄但 timeline_users 裡沒有對應 role=0 記錄的，
一律用 timelines.user_id 建立一筆負責人（role=0）。

使用方式（從 backend/ 目錄執行）：
    python backfill_timeline_users.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db
from models.timeline import Timeline
from models.timeline_user import TimelineUser

def run_backfill():
    app = create_app()
    with app.app_context():
        all_timelines = Timeline.query.all()
        inserted = 0
        skipped = 0

        for tl in all_timelines:
            existing = TimelineUser.query.filter_by(
                timeline_id=tl.id,
                user_id=tl.user_id
            ).first()

            if existing:
                skipped += 1
            else:
                db.session.add(TimelineUser(
                    timeline_id=tl.id,
                    user_id=tl.user_id,
                    role=0  # 負責人
                ))
                inserted += 1

        db.session.commit()
        print(f"完成！補填 {inserted} 筆，跳過 {skipped} 筆（已有記錄）。")

if __name__ == '__main__':
    run_backfill()
