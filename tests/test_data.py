"""Tests for getting & parsing NewReport events."""
from unittest.mock import patch

import pytest
from telliot_feeds.queries import SpotPrice

from tellor_disputables.data import get_contract, get_contract_info, get_node_url
from tellor_disputables.data import get_legacy_request_pair_info
from tellor_disputables.data import get_query_from_data
from tellor_disputables.data import get_tx_receipt
from tellor_disputables.data import get_web3
from tellor_disputables.data import is_disputable
from tellor_disputables.data import log_loop


@pytest.mark.asyncio
async def test_is_disputable(caplog):
    """test check for disputability for a float value"""
    # ETH/USD
    query_id = "0000000000000000000000000000000000000000000000000000000000000001"
    val = 1000.0
    threshold = 0.05

    # Is disputable
    disputable = await is_disputable(val, query_id, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    # No reported value
    disputable = await is_disputable(reported_val=None, query_id=query_id, conf_threshold=threshold)
    assert disputable is None
    assert "Need reported value to check disputability" in caplog.text

    # Unable to fetch price
    with patch("tellor_disputables.data.general_fetch_new_datapoint", return_value=(None, None)):
        disputable = await is_disputable(val, query_id, threshold)
        assert disputable is None
        assert "Unable to fetch new datapoint from feed" in caplog.text

    # Unsupported query id
    query_id = "gobldygook"
    assert await is_disputable(val, query_id, threshold) is None


def test_get_infura_node_url():
    url = get_node_url()

    assert isinstance(url, str)
    assert url.startswith("http")


def test_get_legacy_request_pair_info():
    asset, currency = get_legacy_request_pair_info(59)

    assert isinstance(asset, str)
    assert isinstance(currency, str)
    assert asset == "ETH"
    assert currency == "JPY"

    with pytest.raises(KeyError):
        _, _ = get_legacy_request_pair_info(101)


def test_get_query_from_data():
    query_data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x03ohm\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x03eth\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    q = get_query_from_data(query_data)

    assert isinstance(q, SpotPrice)
    assert q.asset == "ohm"
    assert q.currency == "eth"


@pytest.mark.asyncio
async def test_rpc_value_errors(check_web3_configured, caplog):

    error_msgs = {
        "{'code': -32000, 'message': 'unknown block'}": "waiting for new blocks",
        "{'code': -32603, 'message': 'request failed or timed out'}": "request for eth event logs failed",
        "something else...": "unknown RPC error gathering eth event logs",
    }

    for i in error_msgs.keys():

        def raise_(*args, **kwargs):
            raise ValueError(i)  # noqa: B023

        with patch("web3.eth.Eth.get_logs", side_effect=raise_):

            w3 = get_web3()

            await log_loop(web3=w3, addr="0x88df592f8eb5d7bd38bfef7deb0fbc02cf3778a0")

            assert error_msgs[i] in caplog.text


def test_get_tx_receipt(check_web3_configured, caplog):
    w3 = get_web3()
    address, abi = get_contract_info(1)
    contract = get_contract(w3, address, abi)
    tx_hash = "0x12345"
    tx_receipt = get_tx_receipt(tx_hash=tx_hash, web3=w3, contract=contract)

    assert tx_receipt is None
    assert (
        "Unable to process receipt for transaction 0x12345" in caplog.text
        or 
        "not found" in caplog.text
    )
