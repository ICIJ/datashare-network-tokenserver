import os
from starlette.routing import Route
from starlette.applications import Starlette
from starlette.responses import Response

from sscred.blind_signature import AbeParam, AbePublicKey, AbePrivateKey
from sscred.pack import packb, unpackb

ENVIRON_SECRET_KEY = "TOKEN_SERVER_SKEY"

async def publickey(_):
    param = AbeParam()
    private_key: AbePrivateKey = unpackb(bytes.fromhex(os.environ.get(ENVIRON_SECRET_KEY)))
    public_key = AbePublicKey(param, private_key)
    return Response(media_type="application/x-msgpack", content=packb(public_key))

routes = [
    Route('/publickey', publickey),
]

app = Starlette(debug=True, routes=routes)
