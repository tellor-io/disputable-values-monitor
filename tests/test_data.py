"""Tests for getting & parsing NewReport events."""
import logging
from unittest.mock import patch

import pytest
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from telliot_feeds.queries.price.spot_price import SpotPrice

from tellor_disputables.data import get_contract
from tellor_disputables.data import get_contract_info
from tellor_disputables.data import get_events
from tellor_disputables.data import get_legacy_request_pair_info
from tellor_disputables.data import get_node_url
from tellor_disputables.data import get_query_from_data
from tellor_disputables.data import get_tx_receipt
from tellor_disputables.data import get_web3
from tellor_disputables.data import is_disputable
from tellor_disputables.data import log_loop
from tellor_disputables.data import parse_new_report_event


@pytest.mark.asyncio
async def test_is_disputable(caplog):
    """test check for disputability for a float value"""
    # ETH/USD
    query_id = "83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
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
    assert "Unable to process receipt for transaction 0x12345" in caplog.text or "not found" in caplog.text


@pytest.mark.asyncio
async def test_parse_new_report_event():

    cfg = TelliotConfig()
    cfg.main.chain_id = 5
    tx_hash = "0xb3e4fb09e3dcc7abc0f30181c5dc9ba7253d694de17d88c37c2bd4069f0eebdc"

    for endpoint in cfg.endpoints.find(chain_id=5):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        5, "Goerli", "Infura", "https://goerli.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)

    new_report = await parse_new_report_event(cfg, tx_hash, 0.50)

    assert new_report

    assert new_report.chain_id == 5
    assert new_report.tx_hash == tx_hash
    assert "etherscan" in new_report.link

    cfg.endpoints.endpoints.remove(endpoint)


@pytest.mark.asyncio
async def test_get_events():

    cfg = TelliotConfig()

    events = await get_events(cfg)

    assert len(events) > 0


def test_get_contract_iofo():

    addr, abi = get_contract_info(5)

    assert addr
    assert addr == "0xB3B662644F8d3138df63D2F43068ea621e2981f9"  # tellor 360 address
    assert abi

    addr, abi = get_contract_info(1234567)
    assert not addr
    assert not abi


@pytest.mark.asyncio
async def test_different_conf_thresholds():
    """test if a value is dispuable under different confindence thresholds"""

    # ETH/USD
    query_id = "83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
    val = 666
    threshold = 0.05

    # Is disputable
    disputable = await is_disputable(val, query_id, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    threshold = 0.50
    # Is now not disputable
    disputable = await is_disputable(val, query_id, threshold)
    assert isinstance(disputable, bool)
    assert not disputable


@pytest.mark.asyncio
async def test_query_id_filter(caplog):

    caplog.set_level(logging.INFO)

    cfg = TelliotConfig()
    cfg.main.chain_id = 1

    for endpoint in cfg.endpoints.find(chain_id=1):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        1, "Mainnet", "Infura", "https://mainnet.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)

    tx_hash = "0xbf71154020b6e96c6c5db54ab97c40db3b73cf80ddda235b5204cf6d63ef5da7"

    # set up a report with an incorrect but plausible query id
    btc_usd_query_id = "a6f013ee236804827b77696d350e9f0ac3e879328f2a3021d473a0b778ad78ac"

    confidence_threshold = 0.50

    # try to parse it
    res = await parse_new_report_event(cfg, tx_hash, confidence_threshold, btc_usd_query_id)

    # parser should return None
    assert not res
    assert "skipping undesired NewReport event" in caplog.text

    cfg.endpoints.endpoints.remove(endpoint)
