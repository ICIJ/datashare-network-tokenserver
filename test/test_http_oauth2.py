import asyncio
import pytest
from sscred.pack import packb, unpackb
import pytest_asyncio
from starlette.testclient import TestClient
from starlette.config import environ
import httpx

from tokenserver.main import setup_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope='module')
def pkey():
    return unpackb(bytes.fromhex(environ['TOKEN_SERVER_SKEY'])).public_key()


@pytest.fixture
def client():
    from tokenserver.main import app
    with TestClient(app) as cli:
        yield cli


@pytest_asyncio.fixture
async def startup_and_shutdown_oauth_server():
    from tokenserver.test.server import UvicornTestServer
    id_server = UvicornTestServer('tokenserver.test.server_oauth2:app', port=12346)
    token_server = UvicornTestServer(setup_app(), port=12345)
    await id_server.up()
    await token_server.up()
    yield
    await token_server.down()
    await id_server.down()


@pytest.mark.asyncio
async def test_get_callback_page_should_init_session(startup_and_shutdown_oauth_server):
    async with httpx.AsyncClient() as ac:
        response = await ac.get("http://localhost:12345/auth/login", follow_redirects=True)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type')
        resp_post = await ac.post(f"http://localhost:12346/signin", data={
            'username': 'johndoe',
            "password": 'secret',
        })
        assert resp_post.status_code == 302
        assert resp_post.headers.get("location").startswith("http://localhost:12345/auth/callback")
        response = await ac.get(resp_post.headers.get("location"))
        assert response.status_code == 200

        session = response.cookies.get("_session")
        assert session is not None


@pytest.mark.asyncio
async def test_get_public_key(pkey, client):
    response = client.get("/publickey")
    assert response.status_code == 200
    assert response.headers.get("content-type") == 'application/x-msgpack'
    assert response.content == packb(pkey)


@pytest.mark.asyncio
async def test_get_authenticated_url_should_redirect_to_login_page(client):
    response = client.post("/commitments?number=3", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location").startswith("http://testserver/auth/login")


@pytest.mark.asyncio
async def test_get_login_page_should_redirect_to_identity_manager(client):
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers.get("location").startswith("http://localhost:12346/oauth/authorize?response_type=code&client_id=oauth2_client_id")

