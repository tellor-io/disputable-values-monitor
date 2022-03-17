import pytest
from tellor_disputables.data import is_disputable
from tellor_disputables.data import get_infura_node_url


def test_is_disputable():
    # ETH/USD
    query_id = "0000000000000000000000000000000000000000000000000000000000000001"
    val = 1000.0
    threshold = 0.05

    assert is_disputable(val, query_id, threshold)

    # Unsupported query id
    query_id = "gobldygook"
    assert is_disputable(val, query_id, threshold) is None


def test_get_infura_node_url():
    url = get_infura_node_url(137)
    
    assert "https://polygon-mainnet.infura.io/v3/" in url

    with pytest.raises(KeyError):
        _ = get_infura_node_url(12341234)