import pytest
from aioredis import Redis
from sscred import AbeParam, AbeSigner

from tokenserver.redis_session_store import RedisSessionStore


@pytest.fixture
def store():
    redis = Redis(host='redis')
    store = RedisSessionStore(redis, ttl_sec=5)
    return store


@pytest.mark.asyncio
async def test_store_put_get(store):
    commitments = create_commitments(3)
    await store.put('test:uid', commitments)
    assert commitments == await store.get('test:uid')


@pytest.mark.asyncio
async def test_store_remove(store):
    await store.put('test:uid', create_commitments(3))

    assert 1 == await store.remove('test:uid')
    assert await store.get('test:uid') is None


@pytest.mark.asyncio
async def test_store_getdel(store):
    commitments = create_commitments(3)
    await store.put('test:uid', commitments)

    assert commitments == await store.getdel('test:uid')
    assert await store.getdel('test:uid') is None


def create_commitments(number: int):
    params = AbeParam()
    skey, pkey = params.generate_new_key_pair()
    signer = AbeSigner(skey, pkey, disable_acl=True)
    commitments = []
    commitments_internal = []
    for _i in range(number):
        com, intern = signer.commit()
        commitments.append(com)
        commitments_internal.append(intern)
    return commitments_internal
