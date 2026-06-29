from flask import Flask
import pytest
from werkzeug.security import generate_password_hash

from models import db
from models.task import Task
from models.timeline import Timeline
from models.user import User


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def user_factory():
    def _create_user(
        email: str,
        username: str,
        *,
        name: str = "Service Test User",
        password: str = "hashed-password",
        commit: bool = True,
    ) -> User:
        user = User(
            name=name,
            username=username,
            email=email,
            password=password,
        )
        db.session.add(user)
        if commit:
            db.session.commit()
        return user

    return _create_user


@pytest.fixture()
def timeline_factory():
    def _create_timeline(
        owner_id: int,
        *,
        name: str = "Test Timeline",
        start_date=None,
        end_date=None,
        remark: str | None = None,
        commit: bool = True,
    ) -> Timeline:
        timeline = Timeline(
            user_id=owner_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            remark=remark,
        )
        db.session.add(timeline)
        if commit:
            db.session.commit()
        return timeline

    return _create_timeline


@pytest.fixture()
def task_factory():
    def _create_task(
        user_id: int,
        *,
        name: str = "Test Task",
        timeline_id: int | None = None,
        priority: int = 2,
        status: str = "pending",
        start_date=None,
        end_date=None,
        task_remark: str | None = None,
        is_work: int = 0,
        commit: bool = True,
    ) -> Task:
        task = Task(
            user_id=user_id,
            name=name,
            timeline_id=timeline_id,
            priority=priority,
            status=status,
            start_date=start_date,
            end_date=end_date,
            task_remark=task_remark,
            isWork=is_work,
        )
        db.session.add(task)
        if commit:
            db.session.commit()
        return task

    return _create_task


@pytest.fixture()
def auth_user_factory():
    def _create_user(
        *,
        email: str,
        password: str,
        username: str,
        name: str = "Blueprint Test User",
        commit: bool = True,
    ) -> User:
        user = User(
            name=name,
            username=username,
            email=email,
            password=generate_password_hash(password),
        )
        db.session.add(user)
        if commit:
            db.session.commit()
        return user

    return _create_user
