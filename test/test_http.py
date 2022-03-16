import os

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from sscred.blind_signature import AbeParam, AbeUser, SignerCommitMessage, SignerResponseMessage
from sscred.pack import packb, unpackb
from starlette.testclient import TestClient

from tokenserver.main import app


@pytest.fixture
def pkey():
    params = AbeParam()
    skey, pkey = params.generate_new_key_pair()
    os.environ['TOKEN_SERVER_SKEY'] = packb(skey).hex()
    return pkey


@pytest.fixture
def client():
    with TestClient(app) as cli:
        yield cli


def test_get_public_key(pkey, client):
    response = client.get("/publickey")
    assert response.status_code == 200
    assert response.headers.get("content-type") == 'application/x-msgpack'
    assert response.content == packb(pkey)


def test_start_server_without_skey():
    if os.environ.get('TOKEN_SERVER_SKEY'):
        del os.environ['TOKEN_SERVER_SKEY']
    with pytest.raises(EnvironmentError):
        with TestClient(app) as client:
            assert os.environ.get('TOKEN_SERVER_SKEY') is None
            client.get("/publickey")


def test_token_generation(pkey, client):
    response = client.post("/commitments?number=3&uid=foo")
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
    response = client.post("/pretokens?uid=foo", data=payload)

    assert response.status_code == 200
    assert response.headers.get("content-type") == 'application/x-msgpack'
    tokens = unpackb(response.content)
    assert isinstance(tokens, list)
    assert len(tokens) == 3
    assert isinstance(tokens[0], SignerResponseMessage)


def test_call_commitments_without_uid(pkey, client):
    response = client.post("/commitments?number=3")
    assert response.status_code == 400


def test_call_tokens_without_invalid_payload(pkey, client):
    response = client.post("/pretokens?uid=foo", data=b'unused payload')
    assert response.status_code == 409


def test_call_tokens_without_uid(pkey, client):
    response = client.post("/pretokens", data=b'unused payload')
    assert response.status_code == 400