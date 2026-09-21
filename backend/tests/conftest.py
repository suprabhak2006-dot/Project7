import os
import pytest
import pytest_asyncio
import numpy as np
import cv2
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.core.config import settings
from backend.app.db.session import Base, get_db
from backend.app.main import app
from backend.app.db.init_db import init_db

# Use test SQLite in memory/file
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def synthetic_face_image():
    # 320x320 BGR image with simulated face features
    img = np.full((320, 320, 3), 180, dtype=np.uint8)
    # Eyes
    cv2.circle(img, (110, 120), 15, (50, 50, 50), -1)
    cv2.circle(img, (210, 120), 15, (50, 50, 50), -1)
    # Nose
    cv2.circle(img, (160, 170), 10, (80, 80, 80), -1)
    # Mouth
    cv2.ellipse(img, (160, 220), (45, 18), 0, 0, 180, (40, 40, 40), -1)
    return img
