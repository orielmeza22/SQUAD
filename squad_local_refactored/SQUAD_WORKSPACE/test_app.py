import pytest
from app import app

@pytest.mark.asyncio
async def test_read_root():
    response = await app.get('/')
    assert response.status_code == 200