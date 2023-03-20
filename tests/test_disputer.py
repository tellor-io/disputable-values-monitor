"""tests for dispute logic of auto-disputer"""

import time
from unittest import mock
import pytest
from telliot_core.apps.core import TelliotConfig
from tellor_disputables.disputer import dispute
from tellor_disputables.utils import NewReport


@pytest.mark.asyncio
async def test_dispute(disputer_account):

    cfg = TelliotConfig()

    cfg.main.chain_id = 1337

    report = NewReport(
            "0xabc123",
            1679274323,
            1337,
            "etherscan.io/abc",
            "SpotPrice",
            15.5,
            "eth",
            "usd",
            "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992", # eth/usd query id
            True,
            "status ",
        )
    await dispute(cfg, disputer_account, report)
