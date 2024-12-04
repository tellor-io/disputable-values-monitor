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

# during testing there aren't that many blocks so setting offset to 0
data.inital_block_offset = 0
# mainnet wallet used for testing
wallet = "0x39E419bA25196794B595B2a595Ea8E527ddC9856"


def txn_kwargs(w3: Web3) -> dict:
    return {
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(wallet),
        "from": wallet,
    }


eth = SpotPrice("eth", "usd")
btc = SpotPrice("btc", "usd")
eth_query_id, eth_query_data = Web3.toHex(eth.query_id), Web3.toHex(eth.query_data)
btc_query_id, btc_query_data = Web3.toHex(btc.query_id), Web3.toHex(btc.query_data)
evm_query_id, evm_query_data = Web3.toHex(evm_call_feed_example.query.query_id), Web3.toHex(
    evm_call_feed_example.query.query_data
)
evm_wrong_val = evm_call_feed_example.query.value_type.encode((int.to_bytes(12345, 32, "big"), 1683131435)).hex()


def custom_open_side_effect(*args, **kwargs):
    """mocks open function to return a mock file"""
    if args[0] == "disputer-config.yaml":
        return mock_open().return_value
    return io.open(*args, **kwargs)


def increase_time_and_mine_blocks(w3: Web3, seconds: int, num_blocks: Optional[int] = None):
    """advances time as needed for tests"""
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
    # only configure two required endpoints cause tests take too long
    config.endpoints.endpoints = [config.endpoints.find(chain_id=1)[0], config.endpoints.find(chain_id=1337)[0]]
    node = config.get_endpoint()
    node.connect()

    w3 = node._web3
    increase_time_and_mine_blocks(w3, 600, 20)
    async with TelliotCore(config=config) as core:
        contracts = core.get_tellor360_contracts()
        # transfer trb to disputer account for disputing
        transfer_function = contracts.token.contract.get_function_by_name("transfer")
        transfer_txn = transfer_function(w3.toChecksumAddress(disputer_account.address), int(100e18)).buildTransaction(
            txn_kwargs(w3)
        )
        transfer_hash = w3.eth.send_transaction(transfer_txn)
        reciept = w3.eth.wait_for_transaction_receipt(transfer_hash)
        assert reciept["status"] == 1
        return core


@pytest.fixture(scope="function")
async def stake_deposited(environment_setup: TelliotCore):
    """tests depositing stakes for reporting"""
    core = await environment_setup
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    token = contracts.token
    approve = token.contract.get_function_by_name("approve")
    deposit = oracle.contract.get_function_by_name("depositStake")
    # approve oracle to spend trb for submitting values
    approve_txn = approve(oracle.address, int(10000e18)).buildTransaction(txn_kwargs(w3))
    approve_hash = w3.eth.send_transaction(approve_txn)
    reciept = w3.eth.wait_for_transaction_receipt(approve_hash)
    assert reciept["status"] == 1
    # deposit stake
    deposit_txn = deposit(_amount=int(10000e18)).buildTransaction(txn_kwargs(w3))
    deposit_hash = w3.eth.send_transaction(deposit_txn)
    receipt = w3.eth.wait_for_transaction_receipt(deposit_hash)
    assert receipt["status"] == 1
    return core


@pytest.fixture(scope="function")
async def submit_multiple_bad_values(stake_deposited: Awaitable[TelliotCore]):
    """tests submission of multiple bad values by same reporter"""
    core = await stake_deposited
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    submit_value = oracle.contract.get_function_by_name("submitValue")
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
    return core


@pytest.mark.asyncio
async def fetch_timestamp(oracle, query_id, chain_timestamp):
    """fetches a value's timestamp from oracle"""
    try:
        timestamp, status = await oracle.read("getDataBefore", query_id, chain_timestamp)
        assert timestamp is not None and len(timestamp) > 2 and timestamp[2] > 0
        assert status.ok, status.error
    except Exception as e:
        pytest.fail(f"Failed to fetch a valid timestamp: {e}")
    return timestamp


async def check_dispute(oracle, query_id, timestamp):
    """checks if a value is in dispute"""
    indispute, _ = await oracle.read("isInDispute", query_id, timestamp[2])
    return indispute


async def setup_and_start(is_disputing, config, config_patches=None, skip_confirmations=False, password=""):
    # using exit stack makes nested patching easier to read
    with ExitStack() as stack:
        stack.enter_context(patch("getpass.getpass", return_value=""))
        stack.enter_context(
            patch("disputable_values_monitor.discord.send_discord_msg", side_effect=lambda _: print("alert sent"))
        )
        stack.enter_context(patch("disputable_values_monitor.cli.TelliotConfig", new=lambda: config))
        stack.enter_context(patch("telliot_feeds.feeds.evm_call_feed.source.cfg", config))
        stack.enter_context(
            patch(
                "telliot_feeds.sources.ampleforth.ampl_usd_vwap.BitfinexSource.fetch_new_datapoint",
                AsyncMock(side_effect=lambda: (1.0, datetime_now_utc())),
            )
        )

        if config_patches is not None:
            for p in config_patches:
                stack.enter_context(p)

        try:
            async with async_timeout.timeout(9):
                await start(False, 8, "disputer-test-acct", is_disputing, 0.1, 0, skip_confirmations, password)
        except asyncio.TimeoutError:
            pass


# @pytest.mark.skip(reason="default config not used")
@pytest.mark.asyncio
async def test_default_config(submit_multiple_bad_values: Awaitable[TelliotCore]):
    """Test that the default config works as expected"""
    core = await submit_multiple_bad_values
    config = core.config
    oracle = core.get_tellor360_contracts().oracle
    w3 = core.endpoint._web3
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]

    eth_timestamp = await fetch_timestamp(oracle, eth_query_id, chain_timestamp)
    evm_timestamp = await fetch_timestamp(oracle, evm_query_id, chain_timestamp + 5000)
    btc_timestamp = await fetch_timestamp(oracle, btc_query_id, chain_timestamp + 10000)

    await setup_and_start(True, config)
    assert await check_dispute(oracle, btc_query_id, btc_timestamp)
    # in config file
    assert await check_dispute(oracle, eth_query_id, eth_timestamp)
    assert await check_dispute(oracle, evm_query_id, evm_timestamp)


@pytest.mark.asyncio
async def test_custom_btc_config(submit_multiple_bad_values: Awaitable[TelliotCore]):
    """Test that a custom btc config works as expected"""
    core = await submit_multiple_bad_values
    config = core.config
    oracle = core.get_tellor360_contracts().oracle
    w3 = core.endpoint._web3
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]

    eth_timestamp = await fetch_timestamp(oracle, eth_query_id, chain_timestamp)
    evm_timestamp = await fetch_timestamp(oracle, evm_query_id, chain_timestamp + 5000)
    btc_timestamp = await fetch_timestamp(oracle, btc_query_id, chain_timestamp + 10000)

    btc_config = {"feeds": [{"query_id": btc_query_id, "threshold": {"type": "Percentage", "alrt_amount": 0.25, "disp_amount": 0.75}}]}
    config_patches = [
        patch("builtins.open", side_effect=custom_open_side_effect),
        patch("yaml.safe_load", return_value=btc_config),
    ]
    await setup_and_start(True, config, config_patches)

    assert await check_dispute(oracle, btc_query_id, btc_timestamp)
    # not in config file
    assert not await check_dispute(oracle, eth_query_id, eth_timestamp)
    assert not await check_dispute(oracle, evm_query_id, evm_timestamp)


@pytest.mark.asyncio
async def test_custom_eth_btc_config(submit_multiple_bad_values: Awaitable[TelliotCore]):
    """Test that eth and btc in dispute config"""
    core = await submit_multiple_bad_values
    config = core.config
    oracle = core.get_tellor360_contracts().oracle
    w3 = core.endpoint._web3
    chain_timestamp = w3.eth.get_block("latest")["timestamp"]

    eth_timestamp = await fetch_timestamp(oracle, eth_query_id, chain_timestamp)
    evm_timestamp = await fetch_timestamp(oracle, evm_query_id, chain_timestamp + 5000)
    btc_timestamp = await fetch_timestamp(oracle, btc_query_id, chain_timestamp + 10000)

    btc_eth_config = {
        "feeds": [
            {"query_id": btc_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
            {"query_id": eth_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
        ]
    }
    config_patches = [
        patch("builtins.open", side_effect=custom_open_side_effect),
        patch("yaml.safe_load", return_value=btc_eth_config),
    ]
    await setup_and_start(True, config, config_patches)

    assert await check_dispute(oracle, btc_query_id, btc_timestamp)
    assert await check_dispute(oracle, eth_query_id, eth_timestamp)
    # not in config file
    assert not await check_dispute(oracle, evm_query_id, evm_timestamp)


@pytest.mark.asyncio
async def test_get_source_from_data(submit_multiple_bad_values: Awaitable[TelliotCore], caplog):
    """Test when get_source_from_data function returns None"""
    core = await submit_multiple_bad_values
    config = core.config

    config_patches = [
        patch("disputable_values_monitor.data.get_source_from_data", side_effect=lambda _: None),
    ]
    await setup_and_start(True, config, config_patches)
    assert "Unable to form source from queryData of query type EVMCall" in caplog.text


@pytest.mark.asyncio
async def test_evm_type_alert(submit_multiple_bad_values: Awaitable[TelliotCore], caplog):
    """Test when evm type alert is triggered should display message that difference can't be evaluated"""
    core = await submit_multiple_bad_values
    config = core.config
    # dispute config requires at least 1 item
    mock_btc_config = {"feeds": [{"query_id": btc_query_id, "threshold": {"type": "Percentage", "amount": 0.75}}]}
    config_patches = [
        patch("builtins.open", side_effect=custom_open_side_effect),
        patch("yaml.safe_load", return_value=mock_btc_config),
        patch(
            "telliot_feeds.sources.evm_call.EVMCallSource.fetch_new_datapoint",
            AsyncMock(return_value=((int.to_bytes(2479, 32, "big"), 1679569268), 0)),
        ),
    ]
    # not disputing just alerting
    # if evm type is in dispute config it will be checked for equality
    await setup_and_start(False, config, config_patches, skip_confirmations=True, password=None)
    assert "Cannot evaluate percent difference on text/addresses/bytes" in caplog.text


@pytest.mark.asyncio
async def test_custom_spot_type(stake_deposited: Awaitable[TelliotCore]):
    core = await stake_deposited
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    config = core.config
    feed = DATAFEED_BUILDER_MAPPING["AmpleforthCustomSpotPrice"]
    qid = Web3.toHex(feed.query.query_id)
    qdata = Web3.toHex(feed.query.query_data)
    submit_value = oracle.contract.get_function_by_name("submitValue")
    # submit bad ampl value, and check if alert; ampl is a custom type and a SpotPrice type
    submit_value_txn = submit_value(qid, int.to_bytes(1, 32, "big"), 0, qdata).buildTransaction(txn_kwargs(w3))
    submit_value_hash = w3.eth.send_transaction(submit_value_txn)
    receipt = w3.eth.wait_for_transaction_receipt(submit_value_hash)
    assert receipt["status"] == 1

    await setup_and_start(False, config)
    expected = "AmpleforthCustomSpotPrice,N/A,N/A,0.0000,yes ❗📲"

    with open("table.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        matching_rows = [row for row in rows if expected in ",".join(row)]
        result = matching_rows[0] if matching_rows else None
        assert result is not None, "Expected row not found."
        assert expected in ",".join(result), "Expected row not in the response."


@pytest.mark.asyncio
async def test_gas_oracle_type(stake_deposited: Awaitable[TelliotCore]):
    core = await stake_deposited
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    config = core.config
    feed = DATAFEED_BUILDER_MAPPING["GasPriceOracle"]
    feed.query.chainId = 1
    feed.query.timestamp = 1679569268
    qid = Web3.toHex(feed.query.query_id)
    qdata = Web3.toHex(feed.query.query_data)
    val = Web3.toHex(feed.query.value_type.encode(46.613))
    submit_value = oracle.contract.get_function_by_name("submitValue")

    submit_value_txn = submit_value(qid, val, 0, qdata).buildTransaction(txn_kwargs(w3))
    submit_value_hash = w3.eth.send_transaction(submit_value_txn)
    receipt = w3.eth.wait_for_transaction_receipt(submit_value_hash)
    assert receipt["status"] == 1
    config_patches = [
        patch(
            "telliot_feeds.sources.gas_price_oracle.GasPriceOracleSource.fetch_new_datapoint",
            AsyncMock(return_value=(22.5, 1679569268)),
        )
    ]
    await setup_and_start(False, config, config_patches)
    expected = "GasPriceOracle,N/A,N/A,46.6130,yes ❗📲"

    with open("table.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        matching_rows = [row for row in rows if expected in ",".join(row)]
        result = matching_rows[0] if matching_rows else None
        assert result is not None, "Expected row not found."
        assert expected in ",".join(result), "Expected row not in the response."


@pytest.mark.asyncio
async def test_evmcall_right_value_wrong_timestamp(submit_multiple_bad_values: Awaitable[TelliotCore]):
    """Test when evm call response has the same value response but different timestamp"""
    core = await submit_multiple_bad_values
    config = core.config
    # evm value that has same value but different block timestamp
    evm_val = (int.to_bytes(12345, 32, "big"), 0)
    config_patches = [
        patch(
            "telliot_feeds.sources.evm_call.EVMCallSource.fetch_new_datapoint",
            AsyncMock(return_value=(evm_val, 0)),
        ),
    ]
    await setup_and_start(True, config, config_patches)
    expected = "EVMCall,N/A,N/A,(b'\\x0...1435),no ✔️,1337"

    with open("table.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
        matching_rows = [row for row in rows if expected in ",".join(row)]
        result = matching_rows[0] if matching_rows else None
        assert result is not None, "Expected row not found."
        assert expected in ",".join(result), "Expected row not in the response."


value = 3400


class FakeDataSource(DataSource[float]):
    async def fetch_new_datapoint(self) -> OptionalDataPoint[float]:
        return value, datetime_now_utc()


@pytest.mark.asyncio
async def test_spot_short_value(stake_deposited: Awaitable[TelliotCore], capsys):

    core = await stake_deposited
    core.config.endpoints.endpoints = [core.config.endpoints.find(chain_id=1337)[0]]
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    submit_value = oracle.contract.get_function_by_name("submitValue")
    # submit fake eth value
    submit_value_txn = submit_value(
        eth_query_id, int.to_bytes(int(value * 1e18), 20, "big"), 0, eth_query_data
    ).buildTransaction(txn_kwargs(w3))
    submit_value_hash = w3.eth.send_transaction(submit_value_txn)
    receipt = w3.eth.wait_for_transaction_receipt(submit_value_hash)
    assert receipt["status"] == 1

    eth_usd_median_feed.source = FakeDataSource()
    eth_config = {
        "feeds": [
            {"query_id": eth_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
        ]
    }
    config_patches = [
        patch("builtins.open", side_effect=custom_open_side_effect),
        patch("yaml.safe_load", return_value=eth_config),
        patch("disputable_values_monitor.data.get_feed_from_catalog", return_value=eth_usd_median_feed),
        patch(
            "disputable_values_monitor.data.send_discord_msg",
            side_effect=lambda _: print("Spot price value length is not 32 bytes"),
        ),
    ]
    await setup_and_start(False, core.config, config_patches)
    assert "Spot price value length is not 32 bytes" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_spot_long_value(stake_deposited: Awaitable[TelliotCore], capsys):

    core = await stake_deposited
    core.config.endpoints.endpoints = [core.config.endpoints.find(chain_id=1337)[0]]
    contracts = core.get_tellor360_contracts()
    w3 = core.endpoint._web3
    oracle = contracts.oracle
    submit_value = oracle.contract.get_function_by_name("submitValue")
    # submit fake eth value
    submit_value_txn = submit_value(
        eth_query_id, int.to_bytes(int(value * 1e18), 33, "big"), 0, eth_query_data
    ).buildTransaction(txn_kwargs(w3))
    submit_value_hash = w3.eth.send_transaction(submit_value_txn)
    receipt = w3.eth.wait_for_transaction_receipt(submit_value_hash)
    assert receipt["status"] == 1

    eth_usd_median_feed.source = FakeDataSource()
    eth_config = {
        "feeds": [
            {"query_id": eth_query_id, "threshold": {"type": "Percentage", "amount": 0.75}},
        ]
    }
    config_patches = [
        patch("builtins.open", side_effect=custom_open_side_effect),
        patch("yaml.safe_load", return_value=eth_config),
        patch("disputable_values_monitor.data.get_feed_from_catalog", return_value=eth_usd_median_feed),
        patch(
            "disputable_values_monitor.data.send_discord_msg",
            side_effect=lambda _: print("Spot price value length is not 32 bytes"),
        ),
    ]
    await setup_and_start(False, core.config, config_patches)
    assert "Spot price value length is not 32 bytes" in capsys.readouterr().out
