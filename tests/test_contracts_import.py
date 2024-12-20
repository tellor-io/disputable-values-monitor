import asyncio
import csv
import io
from contextlib import ExitStack
from typing import Awaitable
from typing import Optional
from unittest.mock import AsyncMock
from unittest.mock import mock_open
from unittest.mock import patch

import async_timeout
import pytest
from chained_accounts import ChainedAccount
from telliot_core.apps.core import TelliotConfig
from telliot_core.apps.core import TelliotCore
from telliot_core.apps.core import Tellor360ContractSet
from telliot_core.tellor.tellor360.autopay import Tellor360AutopayContract
from telliot_core.tellor.tellor360.oracle import Tellor360OracleContract
from telliot_core.tellor.tellorflex.token import TokenContract
from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.feeds import eth_usd_median_feed
from telliot_feeds.feeds import evm_call_feed_example
from telliot_feeds.queries.price.spot_price import SpotPrice
from web3 import Web3

from disputable_values_monitor import data
from disputable_values_monitor.cli import start


@pytest.mark.asyncio
async def test_get_tellor360_contracts() -> dict:
    oracle = Tellor360OracleContract
    autopay = Tellor360AutopayContract
    token = TokenContract
    
    config = TelliotConfig()
    config.main.chain_id = 1
    
    async with TelliotCore(config=config) as core:
        core.endpoint._web3.provider = AsyncMock()
        tellor360_set = core.get_tellor360_contracts()
        
        # Get relevant contract values
        contract_values = {
            'oracle_address': tellor360_set.oracle.address,
            'autopay_address': tellor360_set.autopay.address,
            'token_address': tellor360_set.token.address,
            # Add other specific contract values you need
        }
        
        print(f"Contract values: {contract_values}")
        return contract_values
    
    target_set = "Contract values: {'oracle_address': '0x8cFc184c877154a8F9ffE0fe75649dbe5e2DBEbf', 'autopay_address': '0x3b50dEc3CA3d34d5346228D86D29CF679EAA0Ccb', 'token_address': '0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0'}"
    assert str(contract_values) == target_set, "Contract values do not match the expected target set"

if __name__ == "__main__":
    contract_values = asyncio.run(test_get_tellor360_contracts())
    print(contract_values)
