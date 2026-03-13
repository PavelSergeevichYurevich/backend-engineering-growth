from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from lesson0203.db import get_session
from lesson0203.main import app
from lesson0203.models import Account, Base


@pytest.fixture
def test_db():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    db_session = TestSessionLocal()
    db_session.add_all(
        [
            Account(id=1, balance=Decimal("1000.00"), currency="RUB"),
            Account(id=2, balance=Decimal("100.00"), currency="RUB"),
        ]
    )
    db_session.commit()

    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_session] = override_get_db
    with TestClient(app=app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
