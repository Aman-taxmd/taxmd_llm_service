import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_chat_validation_error_when_empty_messages():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/v1/chat", json={"messages": []})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
