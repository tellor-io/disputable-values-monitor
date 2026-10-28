"""tests for dispute logic of auto-disputer"""

import os
import time
from unittest import mock

import pytest
from chained_accounts import ChainedAccount
from telliot_core.apps.core import TelliotConfig
from telliot_core.model.endpoints import RPCEndpoint
from telliot_core.utils.response import ResponseStatus
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed

from disputable_values_monitor import EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT
from disputable_values_monitor.config import AutoDisputerConfig
from disputable_values_monitor.data import Metrics
from disputable_values_monitor.data import MonitoredFeed
from disputable_values_monitor.data import Thresholds
from disputable_values_monitor.data import parse_new_report_event
from disputable_values_monitor.disputer import _submit_tx_with_retries
from disputable_values_monitor.disputer import dispute
from disputable_values_monitor.disputer import get_dispute_fee
from disputable_values_monitor.utils import NewReport


@pytest.mark.asyncio
async def test_not_meant_to_dispute(caplog, disputer_account):
    """test when dispute() is called but a dispute is not meant to be sent"""

    report = NewReport(
        "0xabc123",
        1679425719,  # this eth block does not have a tellor value on the eth/usd query id
        1337,
        "etherscan.io/",
        "SpotPrice",
        15.5,
        "eth",
        "usd",
        "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992",  # eth/usd query id
        disputable=True,
    )

    cfg = TelliotConfig()
    disp_config = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    report.query_id = "hi how are you"

    await dispute(cfg, disp_config, account=disputer_account, new_report=report)

    assert (
        "Found disputable new report on chain_id 1337 outside selected Monitored Feeds, skipping dispute" in caplog.text
    )


@pytest.mark.asyncio
async def test_dispute_on_empty_block(setup, caplog: pytest.LogCaptureFixture, disputer_account: ChainedAccount):
    """
    test typical dispute with a timestamp that doesn't contain a value.
    it will revert on chain
    """

    cfg = setup
    disp_config = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    report = NewReport(
        "0xabc123",
        1679425719,  # this eth block does not have a tellor value on the eth/usd query id
        1337,
        "etherscan.io/",
        "SpotPrice",
        15.5,
        "eth",
        "usd",
        "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992",  # eth/usd query id
        disputable=True,
    )

    await dispute(cfg, disp_config, disputer_account, report)

    expected_success_logs = ["balance", "Dispute Fee", "no value exists at given timestamp"]

    for i in expected_success_logs:
        assert i in caplog.text

    # missing query id

    mock_approve_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))
    mock_dispute_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))

    report.query_id = ""

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disp_config, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text

    # query id is inactive
    report.query_id = "0x7af670d5ad732a520e49b33749a97d58de18c234d5b0834415fb19647e03a2cb"  # abc/usd

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disp_config, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text


@pytest.mark.asyncio
async def test_dispute_on_disputable_block(setup, caplog: pytest.LogCaptureFixture, disputer_account: ChainedAccount):
    """
    test typical dispute with a timestamp that contains a value.
    it will submit to chain
    """

    cfg = setup
    disp_config = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    report = NewReport(
        "0xabc123",
        1679497091,
        1337,
        "etherscan.io/",
        "SpotPrice",
        15.5,
        "eth",
        "usd",
        "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992",  # eth/usd query id
        disputable=True,
    )

    await dispute(cfg, disp_config, disputer_account, report)

    expected_success_logs = [
        "Equality threshold selected",
        "balance",
        "Dispute Fee",
        "Approval Tx Hash:",
    ]

    for i in expected_success_logs:
        assert i in caplog.text

    # missing query id
    mock_approve_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))
    mock_dispute_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))

    report.query_id = ""

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disp_config, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text

    # query id is inactive
    report.query_id = "0x7af670d5ad732a520e49b33749a97d58de18c234d5b0834415fb19647e03a2cb"  # abc/usd

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disp_config, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text


@pytest.mark.asyncio
async def test_dispute_using_sample_log(
    setup, caplog: pytest.LogCaptureFixture, eth_usd_report_log, disputer_account: ChainedAccount
):
    """
    Send a dispute using a sample log fixture after parsing a new report event.
    The log is mocked to be disputable
    """

    cfg = setup
    disp_config = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    thresholds = Thresholds(
        metric=Metrics.Percentage, alrt_amount=0.25, disp_amount=0.50  # Alert threshold  # Dispute threshold
    )
    monitored_feeds = [MonitoredFeed(eth_usd_median_feed, thresholds)]

    mock_telliot_val = 1
    mock_approve_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))
    mock_dispute_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))

    for endpoint in cfg.endpoints.find(chain_id=1):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(1, "Goerli", "Infura", os.getenv("NODE_URL"), "etherscan.io")
    cfg.endpoints.endpoints.append(endpoint)

    with mock.patch(
        "disputable_values_monitor.data.general_fetch_new_datapoint", return_value=(mock_telliot_val, int(time.time()))
    ):
        new_report = await parse_new_report_event(
            cfg, eth_usd_report_log, monitored_feeds=monitored_feeds, confidence_threshold=0.1
        )

    assert new_report.disputable

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disp_config, disputer_account, new_report)

    expected_logs = [
        "balance",
        "Dispute Fee",
        "Approval Tx Hash",
        "reverted with reason string 'no value exists at given timestamp'",
    ]

    for i in expected_logs:
        assert i in caplog.text


@pytest.mark.asyncio
async def test_get_dispute_fee():
    ok = ResponseStatus(ok=True)
    base_fee = 1_000_000_000_000_000_000
    stake = 3_000_000_000_000_000_000

    async def governance_read(*args, **kwargs):
        func_name = kwargs.get("func_name", args[0] if args else "")
        if func_name == "getDisputeFee":
            return base_fee, ok
        if func_name == "getVoteRounds":
            return [1], ok
        if func_name == "getOpenDisputesOnId":
            return 2, ok
        raise AssertionError(f"unexpected read: {func_name}")

    governance = mock.MagicMock()
    governance.read = mock.AsyncMock(side_effect=governance_read)
    oracle = mock.MagicMock()
    oracle.read = mock.AsyncMock(return_value=(stake, ok))

    def fake_get_contract(cfg, name, account):
        return governance if name == "tellor-governance" else oracle

    report = NewReport(
        "0xabc123",
        1679497091,
        1337,
        "etherscan.io/",
        "SpotPrice",
        15.5,
        "eth",
        "usd",
        "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992",  # eth/usd query id
        disputable=True,
    )

    with mock.patch("disputable_values_monitor.disputer.get_contract", side_effect=fake_get_contract):
        dispute_fee = await get_dispute_fee(TelliotConfig(), report)

    # one open dispute on the id doubles the base fee, capped below the stake
    assert dispute_fee == 2_000_000_000_000_000_000


def _fee_mock_governance(reads: dict, seen: dict):
    ok = ResponseStatus(ok=True)

    async def governance_read(*args, **kwargs):
        func_name = kwargs.get("func_name", args[0] if args else "")
        seen[func_name] = kwargs
        if func_name in reads:
            return reads[func_name], ok
        raise AssertionError(f"unexpected read: {func_name}")

    governance = mock.MagicMock()
    governance.read = mock.AsyncMock(side_effect=governance_read)
    return governance


def _fee_report():
    return NewReport(
        "0xabc123",
        1793202096,
        11155111,
        "sepolia.etherscan.io/",
        "SpotPrice",
        69.0,
        "eth",
        "usd",
        "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992",  # eth/usd query id
        disputable=True,
    )


@pytest.mark.asyncio
async def test_get_dispute_fee_uses_identifier_hash_and_open_dispute_cap():
    """Sepolia regression: governance keys rounds by keccak(queryId, timestamp),
    and with >4 (open disputes + this one) the fee is the full stake."""

    base_fee = 10_000_000_000_000_000_000
    stake = 100_000_000_000_000_000_000

    report = _fee_report()
    seen: dict = {}
    governance = _fee_mock_governance(
        {"getDisputeFee": base_fee, "getVoteRounds": [], "getOpenDisputesOnId": 5},
        seen,
    )
    oracle = mock.MagicMock()
    oracle.read = mock.AsyncMock(return_value=(stake, ResponseStatus(ok=True)))

    def fake_get_contract(cfg, name, account):
        return governance if name == "tellor-governance" else oracle

    with mock.patch("disputable_values_monitor.disputer.get_contract", side_effect=fake_get_contract):
        dispute_fee = await get_dispute_fee(TelliotConfig(), report)

    # vote rounds are looked up by the identifier hash, not the raw query id
    from web3 import Web3

    expected_hash = Web3.solidity_keccak(
        ["bytes32", "uint256"],
        [bytes.fromhex(report.query_id[2:]), report.submission_timestamp],
    )
    assert seen["getVoteRounds"]["_hash"] == expected_hash

    # 5 open disputes + this round > 4, so the fee is capped at the full stake,
    # far above the flat base fee the old code reported
    assert dispute_fee == stake


@pytest.mark.asyncio
async def test_get_dispute_fee_first_round_doubles_per_open_dispute():
    """First dispute on a report with 1 open dispute on the id pays 2x base fee
    (governance increments the open count before charging)."""

    base_fee = 1_000_000_000_000_000_000
    stake = 10_000_000_000_000_000_000

    seen: dict = {}
    governance = _fee_mock_governance(
        {"getDisputeFee": base_fee, "getVoteRounds": [], "getOpenDisputesOnId": 1},
        seen,
    )
    oracle = mock.MagicMock()
    oracle.read = mock.AsyncMock(return_value=(stake, ResponseStatus(ok=True)))

    def fake_get_contract(cfg, name, account):
        return governance if name == "tellor-governance" else oracle

    with mock.patch("disputable_values_monitor.disputer.get_contract", side_effect=fake_get_contract):
        dispute_fee = await get_dispute_fee(TelliotConfig(), _fee_report())

    assert dispute_fee == 2 * base_fee


@pytest.mark.asyncio
async def test_submit_tx_with_retries_transient_failure(caplog):
    """A failed write with no receipt (send/confirm hiccup) is retried."""

    ok = ResponseStatus(ok=True)
    fail = ResponseStatus(ok=False, error="Connection aborted")
    receipt = mock.MagicMock()

    send = mock.AsyncMock(side_effect=[(None, fail), (None, fail), (receipt, ok)])

    tx_receipt, status = await _submit_tx_with_retries(send, label="Dispute", chain_id=11155111, delay=0)

    assert status.ok
    assert tx_receipt is receipt
    assert send.await_count == 3
    assert "not sent/confirmed (attempt 1/3)" in caplog.text


@pytest.mark.asyncio
async def test_submit_tx_with_retries_no_retry_on_revert():
    """A mined revert (receipt present, status failed) is never re-broadcast."""

    revert_receipt = mock.MagicMock()
    reverted = ResponseStatus(ok=False, error="beginDispute transaction reverted.")

    send = mock.AsyncMock(return_value=(revert_receipt, reverted))

    tx_receipt, status = await _submit_tx_with_retries(send, label="Dispute", chain_id=11155111, delay=0)

    assert not status.ok
    assert tx_receipt is revert_receipt
    assert send.await_count == 1
