import warnings

import pytest
import pytest_asyncio
from twilio.base.exceptions import TwilioException

from tellor_disputables.alerts import get_twilio_client

from brownie import accounts
from brownie import Autopay
from brownie import chain
from brownie import multicall as brownie_multicall
from brownie import QueryDataStorage
from brownie import StakingToken
from brownie import TellorFlex
from brownie import TellorFlex360
from brownie import TellorXMasterMock
from brownie import TellorXOracleMock


@pytest.fixture
def check_twilio_configured() -> None:
    try:
        _ = get_twilio_client()
    except TwilioException as e:
        warnings.warn(str(e), stacklevel=2)
        pytest.skip(str(e))

#TODO copy fixtures over, and create governance contract fixture

@pytest.fixture(scope="function", autouse=True)
def mock_token_contract():
    """mock token to use for staking"""
    return accounts[0].deploy(StakingToken)

@pytest.fixture(scope="function")
def tellorflex_360_contract(mock_token_contract):
    account_fake = accounts.add("023861e2ceee1ea600e43cbd203e9e01ea2ed059ee3326155453a1ed3b1113a9")
    return account_fake.deploy(
        TellorFlex360,
        mock_token_contract.address,
        1,
        1,
        1,
        "0x5c13cd9c97dbb98f2429c101a2a8150e6c7a0ddaff6124ee176a3a411067ded0",
    )


@pytest_asyncio.fixture(scope="function")
async def tellor_360(mumbai_test_cfg, tellorflex_360_contract, mock_autopay_contract, mock_token_contract):
    async with TelliotCore(config=mumbai_test_cfg) as core:
        txn_kwargs = {"gas_limit": 3500000, "legacy_gas_price": 1}
        account = core.get_account()

        tellor360 = core.get_tellor360_contracts()
        tellor360.oracle.address = tellorflex_360_contract.address
        tellor360.oracle.abi = tellorflex_360_contract.abi
        tellor360.autopay.address = mock_autopay_contract.address
        tellor360.autopay.abi = mock_autopay_contract.abi
        tellor360.token.address = mock_token_contract.address

        tellor360.oracle.connect()
        tellor360.token.connect()
        tellor360.autopay.connect()

        # mint token and send to reporter address
        mock_token_contract.mint(account.address, 100000e18)

        # approve token to be spent by autopay contract
        mock_token_contract.approve(mock_autopay_contract.address, 100000e18, {"from": account.address})

        # send eth from brownie address to reporter address for txn fees
        accounts[1].transfer(account.address, "1 ether")

        # init governance address
        await tellor360.oracle.write("init", _governanceAddress=accounts[0].address, **txn_kwargs)

        return tellor360, account
