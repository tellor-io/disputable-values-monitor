"""Tests for getting & parsing NewReport events."""
import logging
from unittest.mock import patch

import pytest
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from telliot_feeds.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.queries.price.spot_price import SpotPrice

from tellor_disputables.data import get_contract
from tellor_disputables.data import get_contract_info
from tellor_disputables.data import get_events
from tellor_disputables.data import get_legacy_request_pair_info
from tellor_disputables.data import get_query_from_data
from tellor_disputables.data import get_tx_receipt
from tellor_disputables.data import get_web3
from tellor_disputables.data import is_disputable
from tellor_disputables.data import log_loop
from tellor_disputables.data import NewReport
from tellor_disputables.data import parse_new_report_event


@pytest.mark.asyncio
async def test_is_disputable(caplog):
    """test check for disputability for a float value"""
    val = 1000.0
    threshold = 0.05

    # ETH/USD
    current_feed = eth_usd_median_feed

    # Is disputable
    disputable = await is_disputable(val, current_feed, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    # No reported value
    disputable = await is_disputable(reported_val=None, current_feed=current_feed, conf_threshold=threshold)
    assert disputable is None
    assert "Need reported value to check disputability" in caplog.text

    # Unable to fetch price
    with patch("tellor_disputables.data.general_fetch_new_datapoint", return_value=(None, None)):
        disputable = await is_disputable(val, current_feed, threshold)
        assert disputable is None
        assert "Unable to fetch new datapoint from feed" in caplog.text


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

    tx_hash = "0xb3e4fb09e3dcc7abc0f30181c5dc9ba7253d694de17d88c37c2bd4069f0eebdc"

    cfg = TelliotConfig()
    cfg.main.chain_id = 5

    for endpoint in cfg.endpoints.find(chain_id=5):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        5, "Goerli", "Infura", "https://goerli.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)

    new_report = await parse_new_report_event(cfg, tx_hash, 0.50)

    cfg.endpoints.endpoints.remove(endpoint)

    assert new_report

    assert new_report.chain_id == 5
    assert new_report.tx_hash == tx_hash
    assert "etherscan" in new_report.link


@pytest.mark.asyncio
async def test_get_events():

    cfg = TelliotConfig()

    events = await get_events(cfg)

    assert len(events) > 0


def test_get_contract_info():

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
    feed = eth_usd_median_feed
    val = 666
    threshold = 0.05

    # Is disputable
    disputable = await is_disputable(val, feed, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    threshold = 0.99
    # Is now not disputable
    disputable = await is_disputable(val, feed, threshold)
    assert isinstance(disputable, bool)
    assert not disputable


@pytest.mark.asyncio
async def test_feed_filter(caplog):
    """test that, if the user wants to monitor only one feed, all other feeds are ignored and skipped"""

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

    # we are monitoring a different feed
    feed = btc_usd_median_feed

    confidence_threshold = 0.50

    # try to parse it
    res = await parse_new_report_event(cfg, tx_hash, confidence_threshold, feed)

    # parser should return None
    assert not res
    assert "skipping undesired NewReport event" in caplog.text

    cfg.endpoints.endpoints.remove(endpoint)


@pytest.mark.asyncio
async def test_parse_oracle_address_submission():

    update_oracle_address_query_id = "0xcf0c5863be1cf3b948a9ff43290f931399765d051a60c3b23a4e098148b1f707"

    class TellorOracleAddress:

        query_id: str = update_oracle_address_query_id

    cfg = TelliotConfig()
    cfg.main.chain_id = 1

    for endpoint in cfg.endpoints.find(chain_id=1):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        1, "Mainnet", "Infura", "https://mainnet.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)

    tx_hash = "0xa5cac44128bbe2c195ed9dbc2412e8fb2e97b960a9aeb49c2ac111d35603579a"
    etherscan_link = "etherscan.io/tx/0xa5cac44128bbe2c195ed9dbc2412e8fb2e97b960a9aeb49c2ac111d35603579a"
    feed = None
    see_all_values = False

    with (
        patch("tellor_disputables.data.get_query_from_data", return_value=TellorOracleAddress()),
        patch("tellor_disputables.data.get_query_type", return_value="TellorOracleAddress"),
        patch("tellor_disputables.data.get_query_id", return_value=update_oracle_address_query_id),
        patch(
            "tellor_disputables.data.decode_reported_value", return_value="0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"
        ),
    ):
        new_report: NewReport = await parse_new_report_event(
            cfg=cfg, tx_hash=tx_hash, confidence_threshold=0.05, feed=feed, see_all_values=see_all_values
        )  # threshold is ignored

    cfg.endpoints.endpoints.remove(endpoint)

    assert new_report.asset is None
    assert new_report.chain_id == 1
    assert new_report.currency is None
    assert new_report.disputable is None
    assert new_report.link == etherscan_link
    assert new_report.query_id == update_oracle_address_query_id
    assert new_report.tx_hash == tx_hash
    assert new_report.query_type == "TellorOracleAddress"
    assert new_report.value == "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"
    assert "VERY IMPORTANT DATA SUBMISSION" in new_report.status_str
