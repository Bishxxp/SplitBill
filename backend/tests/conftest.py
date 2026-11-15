import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.dependencies import get_db
from app.main import app
from app.models import Group, GroupMember, User

# 1. Configure test database
test_url = make_url(settings.database_url).set(database="splitbill_test")

if test_url.database != "splitbill_test":
    raise RuntimeError("Unsafe test database configuration")

test_engine = create_engine(
    test_url,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


# 2. Reset test data
def reset_database():
    with test_engine.begin() as connection:
        connection.execute(
            text("""
                TRUNCATE TABLE
                    expense_shares,
                    expenses,
                    group_members,
                    groups,
                    users
                RESTART IDENTITY CASCADE
            """)
        )


# 3. Insert seed data
def seed_test_data():
    with TestSessionLocal.begin() as db:
        users = {name: User(username=name) for name in ["alice", "bob", "carol", "dan"]}

        db.add_all(users.values())
        db.flush()

        trip = Group(name="Chiang Mai trip")
        lunch = Group(name="Office lunch")

        db.add_all([trip, lunch])
        db.flush()

        db.add_all(
            [
                GroupMember(
                    group_id=trip.id,
                    user_id=users[name].id,
                )
                for name in ["alice", "bob", "carol"]
            ]
        )

        db.add_all(
            [
                GroupMember(
                    group_id=lunch.id,
                    user_id=users[name].id,
                )
                for name in ["bob", "dan"]
            ]
        )


# 4. Override database dependency
def override_get_db():
    with TestSessionLocal() as db:
        yield db


# 5. Create reusable test fixture
@pytest.fixture
def client():
    reset_database()
    seed_test_data()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        reset_database()


@pytest.fixture
def db_session():
    with TestSessionLocal() as session:
        yield session
