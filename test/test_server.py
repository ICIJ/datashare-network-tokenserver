import pytest

from tokenserver.test.server import UvicornTestServer


@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_server():
    local_server = UvicornTestServer('tokenserver.main:app', port=23456)
    await local_server.up()
    await local_server.down()
    await local_server.up()
    await local_server.down()
