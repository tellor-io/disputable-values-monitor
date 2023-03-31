"""Test helper functions."""
import os
from unittest import mock
from chained_accounts import ChainedAccount, find_accounts
from telliot_core.apps.telliot_config import TelliotConfig

from src.tellor_disputables import EXAMPLE_NEW_REPORT_EVENT
from src.tellor_disputables import EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT
from src.tellor_disputables.utils import disputable_str, select_account
from src.tellor_disputables.utils import get_logger
from src.tellor_disputables.utils import get_tx_explorer_url


def test_get_tx_explorer_url():
    tx_hash = EXAMPLE_NEW_REPORT_EVENT["transactionHash"].hex()
    chain_id = 1
    cfg = TelliotConfig()
    cfg.main.chain_id = chain_id

    tx_url = get_tx_explorer_url(tx_hash, cfg=cfg)
    assert isinstance(tx_url, str)


def test_disputable_str():
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

    logger = get_logger(__name__)

    logger.error("test message that writes to log.txt")

    with open("log.txt", "r") as f:
        contents = f.readlines()[-1]

    assert "test message that writes to log.txt" in contents

def test_select_account():
    """test that accounts are not neccesary for running the DVM"""

    cfg = TelliotConfig()

    if not find_accounts("disputer-test-acct"):
        ChainedAccount.add("disputer-test-acct1", [1, 5, 4, 1337, 80001], os.getenv("PRIVATE_KEY"), "")

    with mock.patch("click.confirm", return_value=False):
        account = select_account(cfg, None)

    assert not account