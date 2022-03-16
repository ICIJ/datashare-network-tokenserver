import os
from typing import Any, Optional

from aioredis import Redis

from starlette.exceptions import HTTPException
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.requests import Request

from sscred.blind_signature import AbePublicKey, AbePrivateKey, AbeSigner
from sscred.pack import packb, unpackb

from .redis_session_store import RedisSessionStore

ENVIRON_SECRET_KEY = "TOKEN_SERVER_SKEY"
REDIS_STORE: Optional[RedisSessionStore] = None

SECRET_KEY: Optional[AbePrivateKey] = None
PUBLIC_KEY: Optional[AbePublicKey] = None


def init_server_keys():
    global SECRET_KEY
    global PUBLIC_KEY
    skey = os.environ.get(ENVIRON_SECRET_KEY, None)
    if skey is None:
        raise EnvironmentError(f"{ENVIRON_SECRET_KEY} environment variable is not defined")
    SECRET_KEY = unpackb(bytes.fromhex(skey))
    PUBLIC_KEY = SECRET_KEY.public_key()


def init_store():
    global REDIS_STORE
    url = os.environ.get("TOKEN_SERVER_REDIS_URL", "redis://redis:6379")
    ttl = int(os.environ.get("TOKEN_SERVER_REDIS_TTL", "30"))
    redis = Redis.from_url(url)
    REDIS_STORE = RedisSessionStore(redis, ttl)


async def close_redis():
    await REDIS_STORE.close()


async def public_key(_):
    return Response(media_type="application/x-msgpack", content=packb(PUBLIC_KEY))


async def commitments(req: Request):
    number = int(req.query_params.get('number'))
    uid = raise_if_none(req.query_params.get('uid'), 400)
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)

    coms = []
    coms_internal = []
    for _i in range(number):
        com, intern = signer.commit()
        coms.append(com)
        coms_internal.append(intern)

    await REDIS_STORE.put(uid, coms_internal)

    return Response(media_type="application/x-msgpack", content=packb(coms))


async def tokens(req: Request):
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)
    uid = raise_if_none(req.query_params.get('uid'), 400)
    commitments_internal = raise_if_none(await REDIS_STORE.getdel(uid), 409)
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
    Route('/pretokens', tokens, methods=['POST']),
]

app = Starlette(debug=True, routes=routes, on_startup=[init_server_keys, init_store], on_shutdown=[close_redis])
