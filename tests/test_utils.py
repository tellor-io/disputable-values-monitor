import pytest

from src.tellor_disputables.utils import get_tx_explorer_url
from src.tellor_disputables.utils import disputable_str
from src.tellor_disputables import EXAMPLE_NEW_REPORT_EVENT
from src.tellor_disputables import EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT


def test_get_tx_explorer_url():
    tx_hash = EXAMPLE_NEW_REPORT_EVENT['transactionHash'].hex()
    chain_id = 1

    tx_url = get_tx_explorer_url(tx_hash, chain_id)
    assert isinstance(tx_url, str)



def test_disputable_str():
    disputable = True
    query_id = EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT[0]['args']['_queryId']
    disp_str = disputable_str(disputable, query_id)
    assert isinstance(disp_str, str)
    assert disp_str == "yes ❗📲"

    disputable1 = False
    disp_str1 = disputable_str(disputable1, query_id)
    assert isinstance(disp_str1, str)
    assert disp_str1 == "no ✔️"





