import os
from typing import Any, Optional

from starlette.exceptions import HTTPException
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request

from sscred.blind_signature import AbeParam, AbePublicKey, AbePrivateKey, AbeSigner
from sscred.pack import packb, unpackb

ENVIRON_SECRET_KEY = "TOKEN_SERVER_SKEY"
memory_repository = dict()

SECRET_KEY: Optional[AbePrivateKey] = None
PUBLIC_KEY: Optional[AbePublicKey] = None


def on_startup():
    global SECRET_KEY
    global PUBLIC_KEY
    skey = os.environ.get(ENVIRON_SECRET_KEY, None)
    if skey is None:
        raise EnvironmentError(f"{ENVIRON_SECRET_KEY} environment variable is not defined")
    SECRET_KEY = unpackb(bytes.fromhex(skey))
    PUBLIC_KEY = SECRET_KEY.public_key()


async def public_key(_):
    return Response(media_type="application/x-msgpack", content=packb(PUBLIC_KEY))


async def commitments(req: Request):
    number = int(req.query_params.get('number'))
    uid = raise_if_none(req.query_params.get('uid'), 400)
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)

    commitments = []
    commitments_internal = []
    for _i in range(number):
        com, intern = signer.commit()
        commitments.append(com)
        commitments_internal.append(intern)

    memory_repository[uid] = commitments_internal

    return Response(media_type="application/x-msgpack", content=packb(commitments))


async def tokens(req: Request):
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)
    uid = raise_if_none(req.query_params.get('uid'), 400)
    commitments_internal = raise_if_none(memory_repository.pop(uid, None), 409)
    blind_tokens = list()
    for pre_token, internal in zip(unpackb(await req.body()), commitments_internal):
        blind_tokens.append(signer.respond(pre_token, internal))
    return Response(media_type="application/x-msgpack", content=packb(blind_tokens))


def raise_if_none(arg: Any, code: int):
    if arg is None:
        raise HTTPException(status_code=code)
    return arg


routes = [
    Route('/publickey', public_key),
    Route('/commitments', commitments, methods=['POST']),
    Route('/tokens', tokens, methods=['POST']),
]

app = Starlette(debug=True, routes=routes, on_startup=[on_startup])
