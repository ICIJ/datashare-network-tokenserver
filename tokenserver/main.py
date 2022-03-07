import os
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request

from sscred.blind_signature import AbeParam, AbePublicKey, AbePrivateKey, AbeSigner
from sscred.pack import packb, unpackb

ENVIRON_SECRET_KEY = "TOKEN_SERVER_SKEY"
memory_repository = dict()


async def public_key(_):
    secret_key: AbePrivateKey = unpackb(bytes.fromhex(os.environ.get(ENVIRON_SECRET_KEY)))
    public_key = secret_key.public_key()
    return Response(media_type="application/x-msgpack", content=packb(public_key))


async def commitments(req: Request):
    number = int(req.query_params.get('number'))
    uid = req.query_params.get('uid')
    secret_key: AbePrivateKey = unpackb(bytes.fromhex(os.environ.get(ENVIRON_SECRET_KEY)))
    signer = AbeSigner(secret_key, secret_key.public_key(), disable_acl=True)

    commitments = []
    commitments_internal = []
    for _i in range(number):
        com, intern = signer.commit()
        commitments.append(com)
        commitments_internal.append(intern)

    memory_repository[uid] = commitments_internal

    return Response(media_type="application/x-msgpack", content=packb(commitments))


async def tokens(req: Request):
    secret_key: AbePrivateKey = unpackb(bytes.fromhex(os.environ.get(ENVIRON_SECRET_KEY)))
    signer = AbeSigner(secret_key, secret_key.public_key(), disable_acl=True)
    commitments_internal = memory_repository.pop(req.query_params.get('uid'))
    blind_tokens = list()
    for pre_token, internal in zip(unpackb(await req.body()), commitments_internal):
        blind_tokens.append(signer.respond(pre_token, internal))
    return Response(media_type="application/x-msgpack", content=packb(blind_tokens))

routes = [
    Route('/publickey', public_key),
    Route('/commitments', commitments, methods=['POST']),
    Route('/tokens', tokens, methods=['POST']),
]

app = Starlette(debug=True, routes=routes)
