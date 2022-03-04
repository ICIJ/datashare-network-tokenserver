import os

from starlette.testclient import TestClient
from sscred.blind_signature import AbeParam, AbePublicKey, AbePrivateKey
from sscred.pack import packb

from tokenserver.main import app


def test_get_public_key():
    client = TestClient(app)
    params = AbeParam()
    skey, pkey = params.generate_new_key_pair()
    os.environ['TOKEN_SERVER_SKEY'] = packb(skey).hex()

    response = client.get("/publickey")
    assert response.status_code == 200
    assert response.headers.get("content-type") == 'application/x-msgpack'
    assert response.content == packb(pkey)
