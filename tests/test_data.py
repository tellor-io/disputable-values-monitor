"""Tests for getting & parsing NewReport events."""
from unittest.mock import patch

import pytest
from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from telliot_feeds.queries.price.spot_price import SpotPrice
from web3.datastructures import AttributeDict

from tellor_disputables.data import get_contract_info
from tellor_disputables.data import get_events
from tellor_disputables.data import get_query_from_data
from tellor_disputables.data import is_disputable
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
async def test_parse_new_report_event():

    cfg = TelliotConfig()
    cfg.main.chain_id = 5

    for endpoint in cfg.endpoints.find(chain_id=5):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        5, "Goerli", "Infura", "https://goerli.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)
    log = AttributeDict(
        {
            "address": "0xB3B662644F8d3138df63D2F43068ea621e2981f9",
            "topics": [
                HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"),
                HexBytes("0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"),
                HexBytes("0x000000000000000000000000000000000000000000000000000000006387ddcf"),
                HexBytes("0x0000000000000000000000000021053b73a20cb418d0458f543ac3e46d24137e"),
            ],
            "data": "0x000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000009e800000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000461f0eabb0b7870000000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            "blockNumber": 16085880,
            "transactionHash": HexBytes("0xbf71154020b6e96c6c5db54ab97c40db3b73cf80ddda235b5204cf6d63ef5da7"),
            "transactionIndex": 16,
            "blockHash": HexBytes("0xcf720f24b1793eb4d58c6137535e6512b7e62794d1ef4db61eff9dc7c67ef03b"),
            "logIndex": 63,
            "removed": False,
        }
    )
    new_report = await parse_new_report_event(cfg, 0.50, log)

    assert new_report

    assert new_report.chain_id == 5
    assert new_report.tx_hash == log.transactionHash.hex()
    assert "etherscan" in new_report.link

    cfg.endpoints.endpoints.remove(endpoint)


@pytest.mark.asyncio
async def test_get_events():

    cfg = TelliotConfig()

    events = await get_events(cfg, "tellor", [], 7)

    assert len(events) > 0


def test_get_contract_info():

    addr, abi = get_contract_info(5, "tellor360")

    assert addr
    assert addr == "0xB3B662644F8d3138df63D2F43068ea621e2981f9"  # tellor 360 address
    assert abi

    addr, abi = get_contract_info(1234567, "tellor")
    assert not addr
    assert not abi


@pytest.mark.asyncio
async def test_different_conf_thresholds():
    """test if a value is dispuable under different confindence thresholds"""

    # ETH/USD
    query_id = "83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
    val = 1000
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
