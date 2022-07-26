from typing import Any, Optional

from redis.asyncio import Redis

from authlib.integrations.httpx_client import AsyncOAuth2Client
from httpx import URL
from starlette import datastructures
from starlette.config import Config
from starlette.datastructures import Secret

from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import Response, RedirectResponse
from starlette.requests import Request

from sscred.blind_signature import AbePublicKey, AbePrivateKey, AbeSigner
from sscred.pack import packb, unpackb
from starlette_session import SessionMiddleware
from starlette_session.backends import AioRedisSessionBackend, BackendType


config = Config(".env")
SECRET_KEY: AbePrivateKey = config("TOKEN_SERVER_SKEY", cast=lambda x: unpackb(bytes.fromhex(x)))
NB_TOKENS: int = config("TOKEN_SERVER_DEFAULT_NB_TOKENS", cast=int, default=10)
PUBLIC_KEY: AbePublicKey = SECRET_KEY.public_key()
REDIS_URL: URL = URL(str(config("TOKEN_SERVER_REDIS_URL", cast=datastructures.URL, default='redis://redis:6379')))
REDIS_TTL: int = config("TOKEN_SERVER_REDIS_TTL", cast=int, default=30)
COOKIE_SKEY: Secret = config("TOKEN_SERVER_COOKIE_SKEY", cast=Secret)
COOKIE_NAME: Secret = config("TOKEN_SERVER_COOKIE_NAME", default='_session')

OAUTH2_AUTHORIZE_URL = config("TOKEN_SERVER_OAUTH2_AUTHORIZE_URL", default="/oauth/authorize")
OAUTH2_TOKEN_URL = config("TOKEN_SERVER_OAUTH2_TOKEN_URL", default="/oauth/token")
OAUTH2_USER_URL = config("TOKEN_SERVER_OAUTH2_USER_URL", default="/api/me.json")
OAUTH2_SERVER_URL: URL = URL(str(config("TOKEN_SERVER_OAUTH2_SERVER_URL", cast=datastructures.URL)))
OAUTH2_CLIENT_ID = config('TOKEN_SERVER_OAUTH2_CLIENT_ID', cast=str)
OAUTH2_CLIENT_SECRET = config('TOKEN_SERVER_OAUTH2_CLIENT_SECRET', cast=Secret)


class JSONAioRedisSessionBackend(AioRedisSessionBackend):
    """Customized AioRedis session backend, which store the data in JSON."""
    async def set(
            self, key: str, value: dict, exp: Optional[int] = None
    ) -> Optional[str]:  # pragma: no cover
        return await self.redis.set(key, packb(value), exp)

    async def get(self, key: str) -> Optional[dict]:
        value = await self.redis.get(key)
        return unpackb(value) if value else None


async def public_key(_):
    return Response(media_type="application/x-msgpack", content=packb(PUBLIC_KEY))


async def commitments(request: Request):
    user = _get_user(request)
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)
    nb_tokens = user.get('nb_tokens', NB_TOKENS)
    coms = []
    coms_internal = []
    for _i in range(nb_tokens):
        com, intern = signer.commit()
        coms.append(com)
        coms_internal.append(intern)

    request.session[user.get('username')] = coms_internal

    return Response(media_type="application/x-msgpack", content=packb(coms))


async def tokens(request: Request):
    user = _get_user(request)
    signer = AbeSigner(SECRET_KEY, PUBLIC_KEY, disable_acl=True)
    commitments_internal = request.session.pop(user.get('username'), None)

    if commitments_internal is None:
        return Response(status_code=409)

    blind_tokens = list()
    for pre_token, internal in zip(unpackb(await request.body()), commitments_internal):
        blind_tokens.append(signer.respond(pre_token, internal))
    return Response(media_type="application/x-msgpack", content=packb(blind_tokens))


def _get_user(request: Request) -> dict:
    user_dict = request.session.get('user')
    if user_dict is None:
        raise HTTPException(status_code=302, headers={'Location': request.url_for('login')})
    return user_dict


async def login(request: Request):
    oauth_client = create_oauth_client(request)
    url, _state = oauth_client.create_authorization_url(f'{str(OAUTH2_SERVER_URL)}{OAUTH2_AUTHORIZE_URL}')
    return RedirectResponse(status_code=302, url=url)


async def callback(request: Request):
    oauth_client = create_oauth_client(request)
    await oauth_client.fetch_token(OAUTH2_TOKEN_URL, authorization_response=str(request.url))
    resp = await oauth_client.get(OAUTH2_USER_URL)
    request.session['user'] = resp.json()
    return Response()


def create_oauth_client(request):
    return AsyncOAuth2Client(
        OAUTH2_CLIENT_ID,
        OAUTH2_CLIENT_SECRET,
        redirect_uri=request.url_for('callback'),
        base_url=OAUTH2_SERVER_URL
    )


def raise_if_none(arg: Any, code: int):
    if arg is None:
        raise HTTPException(status_code=code)
    return arg


async def error_handler(request: Request, exc: HTTPException):
    return Response(status_code=exc.status_code)


routes = [
    Route('/auth/login', login, methods=['GET']),
    Route('/auth/callback', callback, methods=['GET']),
    Route('/publickey', public_key, methods=['GET']),
    Route('/commitments', commitments, methods=['POST']),
    Route('/pretokens', tokens, methods=['POST']),
]


def setup_app():
    redis = Redis.from_url(str(REDIS_URL))

    async def on_startup():
        await redis.initialize()

    async def on_shutdown():
        await redis.close()

    middlewares = [
        Middleware(SessionMiddleware,
                   secret_key=COOKIE_SKEY,
                   cookie_name="_session",
                   backend_type=BackendType.aioRedis,
                   custom_session_backend=JSONAioRedisSessionBackend(redis)
                   )
    ]

    return Starlette(
        debug=True,
        routes=routes,
        middleware=middlewares,
        on_shutdown=[on_shutdown],
        on_startup=[on_startup]
    )


app = setup_app()
