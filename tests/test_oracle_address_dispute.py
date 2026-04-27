"""Tests for TellorOracleAddress auto-dispute logic."""
import eth_abi
import pytest
from hexbytes import HexBytes
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_feeds.queries.tellor.tellor_oracle_address import TellorOracleAddress
from web3 import Web3
from web3.datastructures import AttributeDict

from disputable_values_monitor.data import parse_new_report_event


EXPECTED_ORACLE = "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0"
WRONG_ORACLE = "0x000000000000000000000000000000000000dEaD"

NEW_REPORT_TOPIC = HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95")


def _build_oracle_address_log(reported_address: str) -> AttributeDict:
    """Build a NewReport log fixture for a TellorOracleAddress query."""
    query = TellorOracleAddress()
    query_data = query.query_data
    query_id = query.query_id
    value = eth_abi.encode(["address"], [reported_address])
    data = eth_abi.encode(["bytes", "uint256", "bytes"], [value, 0, query_data])

    return AttributeDict(
        {
            "address": "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0",
            "topics": [
                NEW_REPORT_TOPIC,
                HexBytes(query_id),
                HexBytes("0x000000000000000000000000000000000000000000000000000000006387ddcf"),
                HexBytes("0x0000000000000000000000000021053b73a20cb418d0458f543ac3e46d24137e"),
            ],
            "data": "0x" + data.hex(),
            "blockNumber": 16085880,
            "transactionHash": HexBytes("0x" + "ab" * 32),
            "transactionIndex": 0,
            "blockHash": HexBytes("0x" + "cd" * 32),
            "logIndex": 0,
            "removed": False,
        }
    )


def _build_cfg() -> TelliotConfig:
    """Build a TelliotConfig with a pre-populated Web3 on the mainnet endpoint.

    parse_new_report_event only uses w3.codec for log decoding, and Web3()
    exposes a codec without contacting a node. Pre-setting `_web3` makes
    `endpoint.connect()` return early without any network calls.
    """
    cfg = TelliotConfig()
    cfg.main.chain_id = 1
    endpoint = cfg.endpoints.find(chain_id=1)[0]
    endpoint.url = "http://127.0.0.1:1"
    endpoint._web3 = Web3()
    return cfg


@pytest.mark.asyncio
async def test_tellor_oracle_address_disputable_when_mismatch():
    """A TellorOracleAddress report differing from the configured one is disputable."""
    log = _build_oracle_address_log(WRONG_ORACLE)
    cfg = _build_cfg()

    new_report = await parse_new_report_event(
        cfg=cfg,
        log=log,
        confidence_threshold=0.0,
        monitored_feeds=[],
        oracle_address=EXPECTED_ORACLE,
    )

    assert new_report is not None
    assert new_report.query_type == "TellorOracleAddress"
    assert new_report.disputable is True


@pytest.mark.asyncio
async def test_tellor_oracle_address_not_disputable_when_match():
    """A TellorOracleAddress report matching the configured one is not disputable."""
    log = _build_oracle_address_log(EXPECTED_ORACLE)
    cfg = _build_cfg()

    new_report = await parse_new_report_event(
        cfg=cfg,
        log=log,
        confidence_threshold=0.0,
        monitored_feeds=[],
        oracle_address=EXPECTED_ORACLE,
    )

    assert new_report is not None
    assert new_report.query_type == "TellorOracleAddress"
    assert new_report.disputable is False


@pytest.mark.asyncio
async def test_tellor_oracle_address_not_disputable_case_insensitive_match():
    """Address comparison is case-insensitive (handles checksum vs lowercase)."""
    log = _build_oracle_address_log(EXPECTED_ORACLE)
    cfg = _build_cfg()

    new_report = await parse_new_report_event(
        cfg=cfg,
        log=log,
        confidence_threshold=0.0,
        monitored_feeds=[],
        oracle_address=EXPECTED_ORACLE.lower(),
    )

    assert new_report is not None
    assert new_report.disputable is False


@pytest.mark.asyncio
async def test_tellor_oracle_address_no_config_returns_alert_only():
    """Without oracle_address configured, the report is alert-only (disputable=None)."""
    log = _build_oracle_address_log(WRONG_ORACLE)
    cfg = _build_cfg()

    new_report = await parse_new_report_event(
        cfg=cfg,
        log=log,
        confidence_threshold=0.0,
        monitored_feeds=[],
    )

    assert new_report is not None
    assert new_report.query_type == "TellorOracleAddress"
    assert new_report.disputable is None
