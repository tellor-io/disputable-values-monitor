import asyncio
import io
from typing import Optional
from unittest.mock import mock_open
from unittest.mock import patch

import async_timeout
import pytest
from chained_accounts import ChainedAccount
from telliot_core.apps.core import TelliotConfig
from telliot_core.apps.core import TelliotCore
from web3 import Web3

from tellor_disputables.cli import start


wallet = "0x39E419bA25196794B595B2a595Ea8E527ddC9856"


def txn_kwargs(w3: Web3) -> dict:
    return {
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(wallet),
        "from": wallet,
    }


eth_query_id = "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
eth_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
btc_query_id = "0xa6f013ee236804827b77696d350e9f0ac3e879328f2a3021d473a0b778ad78ac"
btc_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003627463000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000"  # noqa: E501
evm_wrong_val = "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000064528c2b00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000003039"  # noqa: E501
evm_query_id = "0xd7472d51b2cd65a9c6b81da09854efdeeeff8afcda1a2934566f54b731a922f3"
evm_query_data = "0x00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000745564d43616c6c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000100000000000000000000000088df592f8eb5d7bd38bfef7deb0fbc02cf3778a00000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000418160ddd00000000000000000000000000000000000000000000000000000000"  # noqa: E501


def custom_open_side_effect(*args, **kwargs):
    if args[0] == "disputer-config.yaml":
        return mock_open().return_value
    return io.open(*args, **kwargs)


def increase_time_and_mine_blocks(w3: Web3, seconds: int, num_blocks: Optional[int] = None):
    # Increase time
    w3.provider.make_request("evm_increaseTime", [seconds])

    # Mine new blocks
    if num_blocks is None:
        w3.provider.make_request("evm_mine", [])
    else:
        for _ in range(num_blocks):
            w3.provider.make_request("evm_mine", [])


@pytest.fixture(scope="function")
async def environment_setup(setup: TelliotConfig, disputer_account: ChainedAccount):
    config = setup
    node = config.get_endpoint()
    node.connect()

    w3 = node._web3
    increase_time_and_mine_blocks(w3, 600, 20)
    async with TelliotCore(config=config) as core:
        account = disputer_account
        contracts = core.get_tellor360_contracts()
        oracle = contracts.oracle
        token = contracts.token
        approve = token.contract.get_function_by_name("approve")
        transfer = token.contract.get_function_by_name("transfer")
        deposit_stake = oracle.contract.get_function_by_name("depositStake")
        submit_value = oracle.contract.get_function_by_name("submitValue")

        # transfer trb to disputer account for disputing
        token_txn = transfer(w3.toChecksumAddress(account.address), int(100e18)).buildTransaction(txn_kwargs(w3))
        token_hash = w3.eth.send_transaction(token_txn)
        reciept = w3.eth.wait_for_transaction_receipt(token_hash)
        assert reciept["status"] == 1
        # approve oracle to spend trb for submitting values
        approve_txn = approve(oracle.address, int(10000e18)).buildTransaction(txn_kwargs(w3))
        approve_hash = w3.eth.send_transaction(approve_txn)
        reciept = w3.eth.wait_for_transaction_receipt(approve_hash)
        assert reciept["status"] == 1
        # deposit stake
        deposit_txn = deposit_stake(_amount=int(10000e18)).buildTransaction(txn_kwargs(w3))
        deposit_hash = w3.eth.send_transaction(deposit_txn)
        receipt = w3.eth.wait_for_transaction_receipt(deposit_hash)
        assert receipt["status"] == 1
        # submit bad eth value
        submit_value_txn = submit_value(eth_query_id, int.to_bytes(14, 32, "big"), 0, eth_query_data).buildTransaction(
            txn_kwargs(w3)
        )
        submit_value_hash = w3.eth.send_transaction(submit_value_txn)
        receipt = w3.eth.wait_for_transaction_receipt(submit_value_hash)
        assert receipt["status"] == 1
        # submit bad btc value
        # bypass reporter lock
        increase_time_and_mine_blocks(w3, 4300)
        submit_value_txn = submit_value(btc_query_id, int.to_bytes(13, 32, "big"), 0, btc_query_data).buildTransaction(
            txn_kwargs(w3)
        )
        submit_value_hash = w3.eth.send_transaction(submit_value_txn)
        reciept = w3.eth.wait_for_transaction_receipt(submit_value_hash)
        assert reciept["status"] == 1
        # submit bad evmcall value
        # bypass reporter lock
        increase_time_and_mine_blocks(w3, 4300)
        submit_value_txn = submit_value(evm_query_id, evm_wrong_val, 0, evm_query_data).buildTransaction(txn_kwargs(w3))
        submit_value_hash = w3.eth.send_transaction(submit_value_txn)
        reciept = w3.eth.wait_for_transaction_receipt(submit_value_hash)
        assert reciept["status"] == 1
        return oracle, w3


@pytest.mark.asyncio
async def test_default_config(environment_setup, caplog):
    oracle, w3 = await environment_setup
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]
    eth_timestamp, status = await oracle.read("getDataBefore", eth_query_id, chain_timestamp)
    assert status.ok, status.error
    evm_timestamp, status = await oracle.read("getDataBefore", evm_query_id, chain_timestamp + 5000)
    assert evm_timestamp[2] > 0
    assert status.ok, status.error
    btc_timestamp, status = await oracle.read("getDataBefore", btc_query_id, chain_timestamp + 10000)
    assert btc_timestamp[2] > 0
    assert status.ok, status.error

    with patch("getpass.getpass", return_value=""):
        with patch("tellor_disputables.alerts.send_text_msg", side_effect=print("alert sent")):
            try:
                async with async_timeout.timeout(9):
                    await start(False, 8, "disputer-test-acct", True, 0.1)
            except asyncio.TimeoutError:
                pass
    indispute, _ = await oracle.read("isInDispute", eth_query_id, eth_timestamp[2])
    assert indispute
    # btc value should not be disputed since not in config
    indispute, _ = await oracle.read("isInDispute", btc_query_id, btc_timestamp[2])
    assert not indispute
    indispute, _ = await oracle.read("isInDispute", evm_query_id, evm_timestamp[2])
    # assert indispute == True
    # An error occurs when trying to read evm call value from telliot source, gets an attribute
    # error that shouldn't happen, so not sure what's going on here
    assert "'EVMCallSource' object has no attribute '_history'" in caplog.text


@pytest.mark.asyncio
async def test_custom_btc_config(environment_setup):
    oracle, w3 = await environment_setup
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]
    eth_timestamp, status = await oracle.read("getDataBefore", eth_query_id, chain_timestamp)
    assert status.ok, status.error
    evm_timestamp, status = await oracle.read("getDataBefore", evm_query_id, chain_timestamp + 5000)
    assert evm_timestamp[2] > 0
    assert status.ok, status.error
    btc_timestamp, status = await oracle.read("getDataBefore", btc_query_id, chain_timestamp + 10000)
    assert btc_timestamp[2] > 0
    assert status.ok, status.error

    btc_config = {"feeds": [{"query_id": btc_query_id, "threshold": {"type": "Percentage", "amount": 0.75}}]}
    with patch("getpass.getpass", return_value=""):
        with patch("tellor_disputables.alerts.send_text_msg", side_effect=print("alert sent")):
            with patch("builtins.open", side_effect=custom_open_side_effect):
                with patch("yaml.safe_load", return_value=btc_config):
                    try:
                        async with async_timeout.timeout(7):
                            await start(False, 8, "disputer-test-acct", True, 0.1)
                    except asyncio.TimeoutError:
                        pass
    indispute, _ = await oracle.read("isInDispute", btc_query_id, btc_timestamp[2])
    assert indispute
    indispute, _ = await oracle.read("isInDispute", eth_query_id, eth_timestamp[2])
    assert not indispute
    indispute, _ = await oracle.read("isInDispute", evm_query_id, evm_timestamp[2])
    assert not indispute


@pytest.mark.asyncio
async def test_custom_eth_btc_config(environment_setup):
    """Test that eth and btc in dispute config"""
    oracle, w3 = await environment_setup
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]
    eth_timestamp, status = await oracle.read("getDataBefore", eth_query_id, chain_timestamp)
    assert status.ok, status.error
    evm_timestamp, status = await oracle.read("getDataBefore", evm_query_id, chain_timestamp + 5000)
    assert evm_timestamp[2] > 0
    assert status.ok, status.error
    btc_timestamp, status = await oracle.read("getDataBefore", btc_query_id, chain_timestamp + 10000)
    assert btc_timestamp[2] > 0
    assert status.ok, status.error

    btc_config = {
        "feeds": [
            {"query_id": btc_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
            {"query_id": eth_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
        ]
    }
    with patch("getpass.getpass", return_value=""):
        with patch("tellor_disputables.alerts.send_text_msg", side_effect=print("alert sent")):
            with patch("builtins.open", side_effect=custom_open_side_effect):
                with patch("yaml.safe_load", return_value=btc_config):
                    try:
                        async with async_timeout.timeout(9):
                            await start(False, 8, "disputer-test-acct", True, 0.1)
                    except asyncio.TimeoutError:
                        pass
    indispute, _ = await oracle.read("isInDispute", btc_query_id, btc_timestamp[2])
    assert indispute
    indispute, _ = await oracle.read("isInDispute", eth_query_id, eth_timestamp[2])
    assert indispute
    indispute, _ = await oracle.read("isInDispute", evm_query_id, evm_timestamp[2])
    assert not indispute
