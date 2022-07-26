import asyncio
import json
import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from test.server import UvicornTestServer
import itsdangerous
from sscred.blind_signature import AbeUser, SignerCommitMessage, SignerResponseMessage
from sscred.pack import packb, unpackb
from starlette.config import environ
import pytest_asyncio
from base64 import b64encode
from redis.asyncio import Redis

from tokenserver.main import setup_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
def pkey():
    return unpackb(bytes.fromhex(environ['TOKEN_SERVER_SKEY'])).public_key()


@pytest_asyncio.fixture
async def auth_user():
    test_redis = Redis.from_url('redis://redis:6379')
    await test_redis.set('my_session_id', packb({"user": {"username": "johndoe", "hashed_password": "fakehashedsecret", "disabled": False}}))
    yield
    await test_redis.delete('my_session_id')
    await test_redis.close()


@pytest_asyncio.fixture
async def with_server():
    token_server = UvicornTestServer(setup_app(), port=12345)
    await token_server.up()
    yield
    await token_server.down()


def sign_cookie(cookie_value: str) -> bytes:
    data = b64encode(json.dumps({'_cssid': cookie_value}).encode())
    signer = itsdangerous.TimestampSigner("secret")
    return signer.sign(data)


@pytest.mark.asyncio
async def test_call_tokens_with_invalid_payload(with_server, auth_user):
    async with httpx.AsyncClient() as ac:
        response = await ac.post("http://localhost:12345/pretokens?uid=foo", data=b'unused payload', cookies={'_session': sign_cookie('my_session_id').decode()})
        assert response.status_code == 409


@pytest.mark.asyncio
async def test_call_commitments_without_session(with_server):
    async with httpx.AsyncClient() as ac:
        response = await ac.post("http://localhost:12345/commitments?number=3")
        assert response.status_code == 302


@pytest.mark.asyncio
async def test_call_tokens_without_session(with_server):
    async with httpx.AsyncClient() as ac:
        response = await ac.post("http://localhost:12345/pretokens", data=b'unused payload')
        assert response.status_code == 302


@pytest.mark.asyncio
async def test_token_generation(pkey, with_server, auth_user):
    async with httpx.AsyncClient() as ac:
        response = await ac.post("http://localhost:12345/commitments?number=3&uid=foo", cookies={'_session': sign_cookie('my_session_id').decode()})
        assert response.status_code == 200
        assert response.headers.get("content-type") == 'application/x-msgpack'

        commitments = unpackb(response.content)
        assert isinstance(commitments, list)
        assert len(commitments) == 3
        assert isinstance(commitments[0], SignerCommitMessage)

        user = AbeUser(pkey)
        pre_tokens = []
        pre_tokens_internal = []
        for com in commitments:
            ephemeral_secret_key = Ed25519PrivateKey.generate()
            ephemeral_public_key_raw = ephemeral_secret_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            pre_token, pre_token_internal = user.compute_blind_challenge(com, ephemeral_public_key_raw)
            pre_tokens.append(pre_token)
            pre_tokens_internal.append(pre_token_internal)

        payload = packb(pre_tokens)
        response = await ac.post("http://localhost:12345/pretokens?uid=foo", data=payload)

        assert response.status_code == 200
        assert response.headers.get("content-type") == 'application/x-msgpack'
        tokens = unpackb(response.content)
        assert isinstance(tokens, list)
        assert len(tokens) == 3
        assert isinstance(tokens[0], SignerResponseMessage)

