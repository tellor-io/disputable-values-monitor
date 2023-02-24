"""Tests for getting & parsing NewReport events."""
import logging
from unittest.mock import patch

import pytest
from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.feeds.btc_usd_feed import btc_usd_median_feed
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.price.spot_price import SpotPrice
from web3 import Web3
from web3.datastructures import AttributeDict

from tellor_disputables.data import get_contract_info
from tellor_disputables.data import get_events
from tellor_disputables.data import get_query_from_data
from tellor_disputables.data import NewReport
from tellor_disputables.data import parse_new_report_event
from tellor_disputables.disputer import Metrics
from tellor_disputables.disputer import MonitoredFeed
from tellor_disputables.disputer import Threshold


@pytest.fixture
def log():
    return AttributeDict(
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
async def test_parse_new_report_event(log):

    threshold = Threshold(Metrics.Percentage, 0.50)
    monitored_feed = MonitoredFeed(eth_usd_median_feed, threshold)

    cfg = TelliotConfig()
    cfg.main.chain_id = 5

    for endpoint in cfg.endpoints.find(chain_id=5):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(
        5, "Goerli", "Infura", "https://goerli.infura.io/v3/db7ce830b1224efe93ae3240f7aaa764", "etherscan.io"
    )
    cfg.endpoints.endpoints.append(endpoint)
    new_report = await parse_new_report_event(cfg, log, monitored_feed)

    cfg.endpoints.endpoints.remove(endpoint)

    assert new_report

    assert new_report.chain_id == 5
    assert new_report.tx_hash == log.transactionHash.hex()
    assert "etherscan" in new_report.link


@pytest.mark.asyncio
async def test_get_events():

    cfg = TelliotConfig()

    events = await get_events(cfg, "tellor360-oracle", [], 7)

    assert len(events) > 0


def test_get_contract_info():

    addr, abi = get_contract_info(5, "tellor360")

    assert addr
    assert addr == "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"  # tellor 360 address
    assert abi

    addr, abi = get_contract_info(1234567, "tellor")
    assert not addr
    assert not abi


@pytest.mark.asyncio
async def test_feed_filter(caplog, log):
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

    # we are monitoring a different feed
    monitored_feed = MonitoredFeed(btc_usd_median_feed, Threshold(Metrics.Percentage, 0.50))
    # try to parse it
    res = await parse_new_report_event(cfg, monitored_feed=monitored_feed, log=log)

    # parser should return None
    assert not res
    assert "skipping undesired NewReport event" in caplog.text

    cfg.endpoints.endpoints.remove(endpoint)


@pytest.mark.asyncio
async def test_parse_oracle_address_submission():

    update_oracle_address_query_id = "0xcf0c5863be1cf3b948a9ff43290f931399765d051a60c3b23a4e098148b1f707"

    log = AttributeDict(
        {
            "address": "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0",
            "topics": [
                HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"),
                HexBytes(update_oracle_address_query_id),
                HexBytes("0x0000000000000000000000000000000000000000000000000000000063caf0f7"),
                HexBytes("0x00000000000000000000000050a86759d495ecfa7c301071d6b0bdd4bd664ab0"),
            ],
            "data": "0x0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000d9157453e2668b2fc45b7a803d3fef3642430cc000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000001354656c6c6f724f7261636c654164647265737300000000000000000000000000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            "blockNumber": 16450223,
            "transactionHash": HexBytes("0xa5cac44128bbe2c195ed9dbc2412e8fb2e97b960a9aeb49c2ac111d35603579a"),
            "transactionIndex": 16,
            "blockHash": HexBytes("0xcf720f24b1793eb4d58c6137535e6512b7e62794d1ef4db61eff9dc7c67ef03b"),
            "logIndex": 63,
            "removed": False,
        }
    )

    class TellorOracleAddress(AbiQuery):

        query_id: str = update_oracle_address_query_id

        @property
        def value_type(self) -> ValueType:
            """Data type returned for a TellorOracleAddress query.

            - `address`: the address of the Tellor oracle
            - `packed`: false
            """

            return ValueType(abi_type="address", packed=False)

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
    ):
        new_report: NewReport = await parse_new_report_event(
            cfg=cfg, log=log, monitored_feed=feed, see_all_values=see_all_values
        )  # threshold is ignored

    cfg.endpoints.endpoints.remove(endpoint)

    assert not new_report.asset
    assert new_report.chain_id == 1
    assert not new_report.currency
    assert new_report.disputable is None
    assert new_report.link == etherscan_link
    assert new_report.query_id == update_oracle_address_query_id
    assert new_report.tx_hash == tx_hash
    assert new_report.query_type == "TellorOracleAddress"
    assert Web3.toChecksumAddress(new_report.value) == "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"
    assert "VERY IMPORTANT DATA SUBMISSION" in new_report.status_str
