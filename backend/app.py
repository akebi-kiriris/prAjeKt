from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import os
from datetime import timedelta
from dotenv import load_dotenv

# 載入 .env 文件中的環境變量
load_dotenv()

from models import db
migrate = None
jwt = JWTManager()
socketio = SocketIO(async_mode='threading')


def _resolve_secret(env_key: str, fallback: str) -> str:
    value = os.getenv(env_key, fallback)
    is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('APP_ENV') == 'production'
    if is_production and value == fallback:
        raise RuntimeError(f'{env_key} 必須在生產環境中設定，不能使用預設值')
    return value

def create_app():
    app = Flask(__name__)
    cors_origins = ['http://localhost:5173', 'http://127.0.0.1:5173', 'https://prajekt-kiriris.web.app']
    
    # 設定
    app.config['SECRET_KEY'] = _resolve_secret('SECRET_KEY', 'dev-secret-key-change-in-production')
    # 使用 SQLite 開發資料庫
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "instance", "prajekt.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = _resolve_secret('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ENCODE_ISSUER'] = None
    app.config['JWT_DECODE_ISSUER'] = None
    app.config['JWT_ENCODE_AUDIENCE'] = None
    app.config['JWT_DECODE_AUDIENCE'] = None
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # CORS 設定
    CORS(app, 
            origins=cors_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'])
    
    # 初始化擴充
    db.init_app(app)
    global migrate
    migrate = Migrate(app, db)
    jwt.init_app(app)
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
    )
    
    # 導入所有模型（確保 Flask-Migrate 能偵測到）
    with app.app_context():
        from models import (User, Group, GroupMember, Message, MessageRead, 
                           Task, TaskFile, Timeline, Todo, 
                           TaskComment, TaskUser, TimelineUser,
                           Notification, ActivityLog)
    
    # 註冊 blueprints
    from blueprints.auth import auth_bp
    from blueprints.tasks import tasks_bp
    from blueprints.todos import todos_bp
    from blueprints.messages import messages_bp
    from blueprints.profile import profile_bp
    from blueprints.groups import groups_bp
    from blueprints.timelines import timelines_bp
    from blueprints.trash import trash_bp
    from blueprints.notifications import notifications_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(todos_bp, url_prefix='/api/todos')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    app.register_blueprint(timelines_bp, url_prefix='/api/timelines')
    app.register_blueprint(trash_bp, url_prefix='/api/trash')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    from realtime import register_socket_events
    register_socket_events(socketio)
    
    # 健康檢查
    @app.route('/api/health')
    def health():
        return {'status': 'ok'}
    
    return app

# WSGI 應用程序實例 (供 gunicorn 導入) | Instance for gunicorn
# 注意: 在 gunicorn 導入此模塊時不會執行 if __name__ == '__main__' 區塊
app = create_app()

if __name__ == '__main__':
    # Railway 會通過 PORT 環變動態分配端口，本地開發預設 5000
    port = int(os.getenv('PORT', 5000))
    is_production = os.getenv('FLASK_ENV') == 'production'
    # 生產環境: gunicorn 啟動 (見 start.sh)
    # 開發環境: 直接使用 socketio.run，但需要 allow_unsafe_werkzeug=True
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=not is_production,
        allow_unsafe_werkzeug=True  # 必要: 允許 Werkzeug 在 Flask-SocketIO 中運行
    )
