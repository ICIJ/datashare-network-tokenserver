import pytest
from starlette.testclient import TestClient


@pytest.fixture
def client():
    from tokenserver.main import app
    with TestClient(app) as cli:
        yield cli


@pytest.mark.skip("fix configuration")
def test_start_server_without_skey():
    with pytest.raises(KeyError):
        from tokenserver.main import app
        with TestClient(app) as _:
            pass