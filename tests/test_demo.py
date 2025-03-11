import os

import pytest
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.core import TelliotConfig
from telliot_core.gas.legacy_gas import fetch_gas_price
from web3 import Web3

from disputable_values_monitor.data import get_contract


@pytest.mark.skip("for demo only")
@pytest.mark.asyncio
async def test_demo(setup: TelliotConfig):

    account_name = "disputer-test-acct"

    if not find_accounts(account_name, 1337):
        ChainedAccount.add(account_name, 1337, os.getenv("PRIVATE_KEY"), "")

    disputer = find_accounts(account_name, 1337)[0]

    cfg = setup

    cfg.main.chain_id = 80001

    oracle = get_contract(cfg, disputer, "tellor360-oracle")
    token = get_contract(cfg, disputer, "trb-token")
    oracle.connect()
    token.connect()

    oracle_address = Web3.to_checksum_address(oracle.address)

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


@pytest.mark.skip("for demo only")
@pytest.mark.asyncio
async def test_evm_call_demo(setup: TelliotConfig):
    """for testing evm call checks"""
    account_name = "disputer-test-acct"

    if not find_accounts(account_name, 1337):
        ChainedAccount.add(account_name, 1337, os.getenv("PRIVATE_KEY"), "")

    disputer = find_accounts(account_name, 1337)[0]

    cfg = setup

    cfg.main.chain_id = 80001

    oracle = get_contract(cfg, disputer, "tellor360-oracle")
    token = get_contract(cfg, disputer, "trb-token")
    oracle.connect()
    token.connect()

    oracle_address = Web3.to_checksum_address(oracle.address)

    gas_price = await fetch_gas_price()
    stake_amount, status = await oracle.read(func_name="getStakeAmount")
    tx_receipt, status = await token.write(
        func_name="approve", spender=oracle_address, amount=stake_amount, gas_limit=60000, legacy_gas_price=gas_price
    )
    tx_receipt, status = await oracle.write(
        func_name="depositStake", _amount=stake_amount, gas_limit=700000, legacy_gas_price=gas_price
    )

    # this is the EVMCall feed example from the query catalog
    query_id = "0xd7472d51b2cd65a9c6b81da09854efdeeeff8afcda1a2934566f54b731a922f3"
    query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000745564d43616c6c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000100000000000000000000000088df592f8eb5d7bd38bfef7deb0fbc02cf3778a00000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000418160ddd00000000000000000000000000000000000000000000000000000000"  # noqa: E501
    nonce = 0
    value = b"123"  # noqa: E501

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
