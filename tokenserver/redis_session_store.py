from typing import List

from redis.asyncio.client import Redis
from sscred import SignerCommitmentInternalParameters, packb, unpackb


class RedisSessionStore:
    def __init__(self, redis: Redis, ttl_sec: int) -> None:
        self.ttl_sec = ttl_sec
        self.redis = redis

    async def put(self, uid: str, internal_commitments: List[SignerCommitmentInternalParameters]) -> None:
        pipe = await self.redis.pipeline()
        await pipe.set(uid, packb(internal_commitments))
        await pipe.expire(uid, self.ttl_sec)
        await pipe.execute()

    async def get(self, uid) -> List[SignerCommitmentInternalParameters]:
        content = await self.redis.get(uid)
        return unpackb(content) if content is not None else None

    async def remove(self, uid) -> int:
        return await self.redis.delete(uid)
