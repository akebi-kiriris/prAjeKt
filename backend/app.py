from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
import os
from datetime import timedelta
from dotenv import load_dotenv

# 載入 .env 文件中的環境變量（本地優先）
# 優先級：.env.local（本地開發覆寫）> .env（雲端 PostgreSQL）
if os.path.exists('.env.local'):
    # override=True 避免 Flask reloader 或外部殘留環境變數覆蓋本地設定
    load_dotenv('.env.local', override=True)  # 本地開發環境（可為 PostgreSQL / SQLite）
    print("✅ 使用 .env.local（本地開發覆寫）", flush=True)
else:
    # 保留外部環境變數優先權（例如部署平台注入設定）
    load_dotenv('.env', override=False)        # 雲端生產環境（PostgreSQL）
    print("⚠️ 使用 .env（雲端 PostgreSQL）", flush=True)

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
    
    # 設定 debug 模式（讓 @before_request 日誌能輸出）
    is_production = os.getenv('FLASK_ENV') == 'production'
    app.debug = not is_production
    
    # 設定
    app.config['SECRET_KEY'] = _resolve_secret('SECRET_KEY', 'dev-secret-key-change-in-production')
    # 使用 SQLite 開發資料庫
    basedir = os.path.abspath(os.path.dirname(__file__))
    raw_db_url = os.getenv('DATABASE_URL', 'sqlite:///instance/prajekt.db')
    db_url = raw_db_url

    # 將相對 SQLite 路徑正規化為絕對路徑，避免工作目錄改變導致無法開啟 DB。
    if isinstance(raw_db_url, str) and raw_db_url.startswith('sqlite:///'):
        sqlite_path = raw_db_url.replace('sqlite:///', '', 1)
        if sqlite_path != ':memory:' and not os.path.isabs(sqlite_path):
            sqlite_abs_path = os.path.abspath(os.path.join(basedir, sqlite_path))
            os.makedirs(os.path.dirname(sqlite_abs_path), exist_ok=True)
            db_url = f"sqlite:///{sqlite_abs_path}"

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    print(f"📊 DATABASE_URL: {db_url}", flush=True)  # 調試：確認使用的數據庫
    if db_url.startswith('sqlite:///'):
        sqlite_relative_path = db_url.replace('sqlite:///', '', 1)
        sqlite_abs_path = os.path.abspath(sqlite_relative_path)
        print(f"📁 SQLITE_PATH(abs): {sqlite_abs_path}", flush=True)
        print(f"📁 SQLITE_EXISTS: {os.path.exists(sqlite_abs_path)}", flush=True)
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
                           Notification, ActivityLog, GroupAISnapshot)
    
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

    @app.before_request
    def _debug_log_api_request():
        if app.debug:
            if request.path.startswith('/api'):
                origin = request.headers.get('Origin', '-')
                auth_header = 'JWT' if request.headers.get('Authorization') else 'NO_AUTH'
                import sys
                sys.stdout.flush()  # 强制刷新 stdout
                print(
                    f"➡️ {request.method} {request.path} | Auth={auth_header} | Origin={origin}",
                    flush=True,
                )
                sys.stdout.flush()
    
    @app.after_request
    def _debug_log_api_response(response):
        if app.debug:
            if request.path.startswith('/api'):
                import sys
                sys.stdout.flush()
                print(
                    f"⬅️ {request.method} {request.path} | Status={response.status_code}",
                    flush=True,
                )
                sys.stdout.flush()
        return response
    
    # 健康檢查
    @app.route('/api/health')
    def health():
        payload = {'status': 'ok'}
        if app.debug:
            active_db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            db_info = {'url': active_db_url}
            if isinstance(active_db_url, str) and active_db_url.startswith('sqlite:///'):
                sqlite_relative_path = active_db_url.replace('sqlite:///', '', 1)
                sqlite_abs_path = os.path.abspath(sqlite_relative_path)
                db_info.update({
                    'type': 'sqlite',
                    'relative_path': sqlite_relative_path,
                    'absolute_path': sqlite_abs_path,
                    'exists': os.path.exists(sqlite_abs_path),
                })
            payload['database'] = db_info
            payload['debug'] = {
                'cwd': os.getcwd(),
                'flask_env': os.getenv('FLASK_ENV', ''),
            }
        return payload
    
    print(f"🔍 create_app() 完成 | app.debug={app.debug} | FLASK_ENV={os.getenv('FLASK_ENV')}", flush=True)
    
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
        use_reloader=False,  # 禁用 reloader，避免日誌被吃掉
        allow_unsafe_werkzeug=True  # 必要: 允許 Werkzeug 在 Flask-SocketIO 中運行
    )
