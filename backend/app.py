from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from datetime import timedelta

from models import db
migrate = None
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # 設定
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    # 使用 SQLite 開發資料庫
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "instance", "learnlink.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_ENCODE_ISSUER'] = None
    app.config['JWT_DECODE_ISSUER'] = None
    app.config['JWT_ENCODE_AUDIENCE'] = None
    app.config['JWT_DECODE_AUDIENCE'] = None
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    
    # CORS 設定
    CORS(app, 
         origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'])
    
    # 初始化擴充
    db.init_app(app)
    global migrate
    migrate = Migrate(app, db)
    jwt.init_app(app)
    
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
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(todos_bp, url_prefix='/api/todos')
    app.register_blueprint(messages_bp, url_prefix='/api/messages')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')
    app.register_blueprint(groups_bp, url_prefix='/api/groups')
    app.register_blueprint(timelines_bp, url_prefix='/api/timelines')
    
    # 健康檢查
    @app.route('/api/health')
    def health():
        return {'status': 'ok'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
