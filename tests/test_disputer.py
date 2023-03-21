"""tests for dispute logic of auto-disputer"""

import os
import time
from unittest import mock
from chained_accounts import ChainedAccount
import pytest
from telliot_core.apps.core import TelliotConfig
from tellor_disputables import EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT
from tellor_disputables.data import Metrics, MonitoredFeed, Threshold, get_contract_info, parse_new_report_event
from tellor_disputables.disputer import dispute
from tellor_disputables.utils import NewReport

from telliot_core.directory import contract_directory, ContractInfo

from telliot_core.utils.response import ResponseStatus

from telliot_core.model.endpoints import RPCEndpoint

from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed


@pytest.mark.asyncio
async def test_dispute_on_empty_block(caplog, disputer_account: ChainedAccount):
    """
    test typical dispute with a timestamp that doesn't contain a value.
    it will revert on chain
    """

    token_contract_info = contract_directory.find(name="trb-token", chain_id=1)[0]
    governance_contract_info = contract_directory.find(name="tellor-governance", chain_id=1)[0]

    forked_token = ContractInfo("trb-token-fork", "Ganache", {1337: token_contract_info.address[1]}, token_contract_info.abi_file)
    forked_governance = ContractInfo("tellor-governance-fork", "Ganache", {1337: governance_contract_info.address[1]}, governance_contract_info.abi_file)

    contract_directory.add_entry(forked_token)
    contract_directory.add_entry(forked_governance)

    cfg = TelliotConfig()
    cfg.main.chain_id = 1337
    cfg.endpoints.endpoints.append(RPCEndpoint(1337, url="http://localhost:8545"))

    report = NewReport(
            "0xabc123",
            1679425719, #this eth block does not have a tellor value on the eth/usd query id
            1337,
            "etherscan.io/",
            "SpotPrice",
            15.5,
            "eth",
            "usd",
            "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992", # eth/usd query id
            True,
            "status ",
        )
    
    await dispute(cfg, disputer_account, report)

    expected_success_logs = ["balance", "Dispute Fee", "would violate contract logic, skipping"]

    for i in expected_success_logs:
        assert i in caplog.text

    # missing query id
    report.query_id = None

    mock_approve_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))
    mock_dispute_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))


    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text

    report.query_id = ""

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text

    # query id is inactive
    report.query_id = "0x7af670d5ad732a520e49b33749a97d58de18c234d5b0834415fb19647e03a2cb" # abc/usd

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disputer_account, report)

    for i in expected_success_logs:
        assert i in caplog.text
        
@pytest.mark.asyncio
async def test_dispute_using_sample_log(caplog, log, disputer_account):
    """
    Send a dispute using a sample log fixture after parsing a new report event.
    The log is mocked to be disputable
    """

    threshold = Threshold(Metrics.Percentage, 0.50)
    monitored_feeds = [MonitoredFeed(eth_usd_median_feed, threshold)]

    mock_telliot_val = 1
    tx_hash = "0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4"
    mock_approve_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))
    mock_dispute_tx = (EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0], ResponseStatus(ok=True))

    cfg = TelliotConfig()
    cfg.main.chain_id = 5

    for endpoint in cfg.endpoints.find(chain_id=5):
        cfg.endpoints.endpoints.remove(endpoint)

    endpoint = RPCEndpoint(5, "Goerli", "Infura", os.getenv("NODE_URL"), "etherscan.io")
    cfg.endpoints.endpoints.append(endpoint)

    with mock.patch("tellor_disputables.data.general_fetch_new_datapoint", return_value=(mock_telliot_val, int(time.time()))):
        new_report = await parse_new_report_event(cfg, log, monitored_feeds)

    assert new_report.disputable

    with mock.patch("telliot_core.contract.contract.Contract.write", side_effect=[mock_approve_tx, mock_dispute_tx]):
        await dispute(cfg, disputer_account, new_report)

    expected_logs = ["balance", "Dispute Fee", "balance is below dispute fee"]

    for i in expected_logs:
        assert i in caplog.text


@pytest.mark.asyncio
async def test_response_to_bad_report():

    """
    stake reporter
    submit report
    """