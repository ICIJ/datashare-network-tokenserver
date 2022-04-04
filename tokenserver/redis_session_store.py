from typing import List
from aioredis import Redis
from sscred import SignerCommitmentInternalState, packb, unpackb


class RedisSessionStore:
    def __init__(self, redis: Redis, ttl_sec: int) -> None:
        self.ttl_sec = ttl_sec
        self.redis = redis

    async def put(self, uid: str, internal_commitments: List[SignerCommitmentInternalState]) -> None:
        pipe = await self.redis.pipeline()
        await pipe.set(uid, packb(internal_commitments))
        await pipe.expire(uid, self.ttl_sec)
        await pipe.execute()

    async def get(self, uid) -> List[SignerCommitmentInternalState]:
        content = await self.redis.get(uid)
        return unpackb(content) if content is not None else None

    async def remove(self, uid) -> int:
        return await self.redis.delete(uid)

    async def getdel(self, uid) -> List[SignerCommitmentInternalState]:
        pipe = await self.redis.pipeline()
        await pipe.get(uid)
        await pipe.delete(uid)
        content = (await pipe.execute())[0]
        return unpackb(content) if content else None

    async def close(self):
        await self.redis.close()