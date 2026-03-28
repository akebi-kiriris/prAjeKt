import pytest
from flask_jwt_extended import JWTManager

from blueprints.auth import auth_bp
from blueprints.groups import groups_bp
from blueprints.messages import messages_bp
from blueprints.notifications import notifications_bp
from blueprints.profile import profile_bp
from blueprints.tasks import tasks_bp
from blueprints.timelines import timelines_bp
from blueprints.todos import todos_bp
from blueprints.trash import trash_bp


@pytest.fixture()
def api_app(app):
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]

    JWTManager(app)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(timelines_bp, url_prefix="/api/timelines")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")
    app.register_blueprint(todos_bp, url_prefix="/api/todos")
    app.register_blueprint(groups_bp, url_prefix="/api/groups")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(trash_bp, url_prefix="/api/trash")

    return app


@pytest.fixture()
def client(api_app):
    return api_app.test_client()
