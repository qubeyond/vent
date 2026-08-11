import httpx
import pytest

from app.api.deps import (
    get_db,
    get_entry_processor,
    get_entry_service,
    get_retag_processor,
    get_update_correction_processor,
)
from app.core.security import hash_password
from app.domain.llm_client import LLMError
from app.infra.db.models import UserModel
from app.infra.db.repositories import SqlAlchemyEntryRepository, SqlAlchemyTagRepository
from app.infra.db.unit_of_work import SqlAlchemyUnitOfWork
from app.main import app
from app.services.entry_service import EntryService
from app.services.tagging_service import TaggingService
from tests.test_entry_service import _unused_correction, make_result, make_service


@pytest.fixture
async def client(session):
    async def override_get_db():
        yield session

    async def override_get_entry_service():
        return make_service(session, make_result("тест"))

    def override_get_entry_processor():
        async def _process(entry_id, correct_text: bool) -> None:
            service = make_service(session, make_result("тест"))
            await service.process_entry(entry_id, correct_text)

        return _process

    def override_get_retag_processor():
        async def _process(entry_id) -> None:
            service = make_service(session, make_result("тест"))
            await service.process_retag(entry_id)

        return _process

    def override_get_update_correction_processor():
        async def _process(entry_id) -> None:
            service = make_service(session, make_result("тест"))
            await service.process_update_correction(entry_id)

        return _process

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_entry_service] = override_get_entry_service
    app.dependency_overrides[get_entry_processor] = override_get_entry_processor
    app.dependency_overrides[get_retag_processor] = override_get_retag_processor
    app.dependency_overrides[get_update_correction_processor] = (
        override_get_update_correction_processor
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user(session):
    model = UserModel(username="alice", password_hash=hash_password("s3cret"))
    session.add(model)
    await session.flush()
    return model


async def test_login_success(client, user):
    response = await client.post(
        "/api/auth/login", json={"username": "alice", "password": "s3cret"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password(client, user):
    response = await client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert response.status_code == 401


async def test_entries_requires_auth(client):
    response = await client.get("/api/entries")
    assert response.status_code == 401


@pytest.fixture
async def auth_headers(client, user):
    login = await client.post("/api/auth/login", json={"username": "alice", "password": "s3cret"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_list_entry(client, auth_headers):
    created = await client.post("/api/entries", json={"text": "заметка"}, headers=auth_headers)
    assert created.status_code == 201
    assert created.json()["raw_text"] == "заметка"
    assert created.json()["status"] == "processing"

    entry_id = created.json()["id"]
    fetched = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert fetched.json()["status"] == "ready"
    assert len(fetched.json()["tags"]) > 0

    listed = await client.get("/api/entries", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


async def test_get_entry_not_found(client, auth_headers):
    response = await client.get(
        "/api/entries/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404


async def test_get_update_delete_entry_roundtrip(client, auth_headers):
    created = await client.post("/api/entries", json={"text": "исходник"}, headers=auth_headers)
    entry_id = created.json()["id"]

    fetched = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["raw_text"] == "исходник"

    updated = await client.patch(
        f"/api/entries/{entry_id}", json={"text": "исправлено"}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["raw_text"] == "исправлено"

    deleted = await client.delete(f"/api/entries/{entry_id}", headers=auth_headers)
    assert deleted.status_code == 204

    after_delete = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert after_delete.status_code == 404


async def test_entry_detail_endpoints_require_auth(client):
    entry_id = "00000000-0000-0000-0000-000000000000"
    assert (await client.get(f"/api/entries/{entry_id}")).status_code == 401
    assert (await client.patch(f"/api/entries/{entry_id}", json={"text": "x"})).status_code == 401
    assert (await client.delete(f"/api/entries/{entry_id}")).status_code == 401


async def test_retag_entry_happy_path(client, auth_headers):
    created = await client.post("/api/entries", json={"text": "заметка"}, headers=auth_headers)
    entry_id = created.json()["id"]

    response = await client.post(f"/api/entries/{entry_id}/retag", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == entry_id

    fetched = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert fetched.json()["status"] == "ready"
    assert fetched.json()["processing_error"] is None


async def test_retag_entry_not_found(client, auth_headers):
    response = await client.post(
        "/api/entries/00000000-0000-0000-0000-000000000000/retag", headers=auth_headers
    )
    assert response.status_code == 404


async def test_retag_entry_surfaces_llm_failure_via_processing_error(
    client, auth_headers, session
):
    created = await client.post("/api/entries", json={"text": "заметка"}, headers=auth_headers)
    entry_id = created.json()["id"]

    class RaisingLLMClient:
        async def complete(self, messages, *, json_mode: bool = False) -> str:
            raise LLMError("роутер недоступен")

    def override_failing_retag_processor():
        async def _process(entry_id) -> None:
            service = EntryService(
                SqlAlchemyEntryRepository(session),
                SqlAlchemyTagRepository(session),
                TaggingService(RaisingLLMClient()),
                _unused_correction(),
                SqlAlchemyUnitOfWork(session),
            )
            await service.process_retag(entry_id)

        return _process

    app.dependency_overrides[get_retag_processor] = override_failing_retag_processor
    response = await client.post(f"/api/entries/{entry_id}/retag", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    fetched = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert fetched.json()["status"] == "ready"
    assert "роутер недоступен" in fetched.json()["processing_error"]


async def test_update_entry_with_correction_goes_through_processing(client, auth_headers):
    created = await client.post("/api/entries", json={"text": "заметка"}, headers=auth_headers)
    entry_id = created.json()["id"]

    response = await client.patch(
        f"/api/entries/{entry_id}",
        json={"text": "текст на правку", "correct_text": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processing"

    fetched = await client.get(f"/api/entries/{entry_id}", headers=auth_headers)
    assert fetched.json()["status"] == "ready"
