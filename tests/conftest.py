import pytest
from tellor_disputables.data import get_web3


@pytest.fixture
def check_web3_configured() -> None:
    try:
        _ = get_web3(chain_id=1)
    except ValueError as e:
        pytest.skip(str(e))
