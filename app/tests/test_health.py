import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_live():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health/live")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "live"
