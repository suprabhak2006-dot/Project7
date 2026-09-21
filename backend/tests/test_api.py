import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "DeepTrace AI" in data["service"]

@pytest.mark.asyncio
async def test_auth_registration_and_login(client: AsyncClient):
    # 1. Register investigator
    reg_resp = await client.post(
        "/api/auth/register",
        json={
            "name": "Detective Miller",
            "email": "miller@police.gov",
            "password": "SecurePassword2026!",
            "role": "INVESTIGATOR"
        }
    )
    assert reg_resp.status_code in (201, 400) # 400 if already created

    # 2. Login
    login_resp = await client.post(
        "/api/auth/login",
        json={
            "email": "miller@police.gov",
            "password": "SecurePassword2026!"
        }
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    token = data["access_token"]

    # 3. Access protected /api/auth/me
    me_resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "miller@police.gov"

    # 4. Access model status
    models_resp = await client.get(
        "/api/models/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert models_resp.status_code == 200
    assert "models" in models_resp.json()
