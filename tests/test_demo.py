import asyncio
import os
from chained_accounts import ChainedAccount, find_accounts
import pytest
from telliot_core.apps.core import TelliotConfig
from telliot_core.gas.legacy_gas import fetch_gas_price

from web3 import Web3
from tellor_disputables.data import get_contract

@pytest.mark.skip("for demo only")
@pytest.mark.asyncio
async def test_demo(setup: TelliotConfig, disputer_account: ChainedAccount):

    account_name = "disputer-test-acct"

    if not find_accounts(account_name, 1337):
        ChainedAccount.add(account_name, 1337, os.getenv("PRIVATE_KEY"), "")

    disputer = find_accounts(account_name, 1337)[0]

    cfg = setup
    
    cfg.main.chain_id = 80001
    
    oracle = get_contract(cfg, disputer_account, "tellor360-oracle")
    token = get_contract(cfg, disputer_account, "trb-token")
    oracle.connect()
    token.connect()

    oracle_address = Web3.toChecksumAddress(oracle.address)

    gas_price = await fetch_gas_price()
    stake_amount, status = await oracle.read(func_name="getStakeAmount")
    tx_receipt, status = await token.write(
        func_name="approve", spender=oracle_address, amount=stake_amount, gas_limit=60000, legacy_gas_price=gas_price
    )
    tx_receipt, status = await oracle.write(
        func_name="depositStake", _amount=stake_amount, gas_limit=700000, legacy_gas_price=gas_price
    )

    query_id = "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
    query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
    nonce = 0
    value = b"0"

    tx_receipt, status = await oracle.write(
        func_name="submitValue",
        _queryId=query_id,
        _queryData=query_data,
        _nonce=nonce,
        _value=value,
        gas_limit=400000,
        legacy_gas_price=gas_price,
    )

    assert status.ok