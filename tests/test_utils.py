"""Test helper functions."""
import os
from unittest import mock

from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig

from src.disputable_values_monitor import EXAMPLE_NEW_REPORT_EVENT
from src.disputable_values_monitor import EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT
from src.disputable_values_monitor.utils import are_all_attributes_none
from src.disputable_values_monitor.utils import disputable_str
from src.disputable_values_monitor.utils import get_logger
from src.disputable_values_monitor.utils import get_tx_explorer_url
from src.disputable_values_monitor.utils import select_account


def test_get_tx_explorer_url():
    """Test generation of the block explorer URL for a tx."""
    tx_hash = EXAMPLE_NEW_REPORT_EVENT["transactionHash"].hex()
    chain_id = 1
    cfg = TelliotConfig()
    cfg.main.chain_id = chain_id

    tx_url = get_tx_explorer_url(tx_hash, cfg=cfg)
    assert isinstance(tx_url, str)


def test_disputable_str():
    """Test disputable report is flagged on the dashboard."""
    disputable = True
    query_id = EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0]["args"]["_queryId"]
    disp_str = disputable_str(disputable, query_id)
    assert isinstance(disp_str, str)
    assert disp_str == "yes ❗📲"

    disputable1 = False
    disp_str1 = disputable_str(disputable1, query_id)
    assert isinstance(disp_str1, str)
    assert disp_str1 == "no ✔️"


def test_logger():
    """Test logger working."""
    logger = get_logger(__name__)

    logger.error("test message that writes to log.txt")

    with open("log.txt", "r") as f:
        contents = f.readlines()[-1]

    assert "test message that writes to log.txt" in contents


def test_select_account():
    """test that accounts are not neccesary for running the DVM"""

    cfg = TelliotConfig()

    if not find_accounts("disputer-test-acct"):
        ChainedAccount.add("disputer-test-acct", [1, 5, 4, 1337, 80001, 80002, 11155111], os.getenv("PRIVATE_KEY"), "")

    with mock.patch("click.confirm", return_value=True):
        account = select_account(cfg, None)

    assert not account


class TestObject:
    def __init__(self, attr1=None, attr2=None, attr3=None):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3


def test_all_attributes_none():
    obj = TestObject()
    assert are_all_attributes_none(obj)


def test_some_attributes_not_none():
    obj = TestObject(None, "not none", None)
    assert not are_all_attributes_none(obj)


def test_no_object():
    assert not are_all_attributes_none("obj")
