# /tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from service.main import app # Импортируем твое FastAPI приложение

# Здесь можно настроить отдельную тестовую базу,
# но для простоты мы будем использовать ту же, но в транзакциях,
# которые всегда откатываются.

@pytest.fixture(scope="module")
def test_client():
    """Создает тестовый клиент для API."""
    with TestClient(app) as client:
        yield client