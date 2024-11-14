from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.feeds import mimicry_nft_market_index_usd_feed
from web3 import Web3

from disputable_values_monitor.config import AutoDisputerConfig
from disputable_values_monitor.data import get_contract
from disputable_values_monitor.data import parse_new_report_event


def increase_time(w3, seconds):
    w3.provider.make_request("evm_increaseTime", [seconds])
    w3.provider.make_request("evm_mine", [])


def take_snapshot(w3):
    return w3.provider.make_request("evm_snapshot", [])


def revert_to_snapshot(w3, snapshot_id):
    w3.provider.make_request("evm_revert", [snapshot_id])


@pytest.mark.skip  # mimicry integration was depricated
@pytest.mark.asyncio
async def test_disputability_mimicry_nft_index_type(setup, disputer_account):
    """test if an incorrect mimicry data report is detected"""
    # get a snapshot of chain to revert to

    cfg = setup

    cfg.main.chain_id = 1
    endpoint = cfg.endpoints.endpoints[0]
    endpoint.url = "http://127.0.0.1:8545"
    endpoint.connect()
    w3 = endpoint.web3
    snapshot_id = take_snapshot(w3)
    oracle = get_contract(cfg, name="tellor360-oracle", account=disputer_account)
    token = get_contract(cfg, name="trb-token", account=disputer_account)

    # fake val to avoid hitting api since api requires key
    val = 11287512.476225
    value = mimicry_nft_market_index_usd_feed.query.value_type.encode(val)
    wallet = Web3.toChecksumAddress("0x39e419ba25196794b595b2a595ea8e527ddc9856")
    tellorflex = w3.eth.contract(address=oracle.address, abi=oracle.abi)
    token = w3.eth.contract(address=token.address, abi=token.abi)
    approve_txn = token.functions.approve(spender=oracle.address, amount=int(5000e18)).buildTransaction(
        {"gas": 350000, "gasPrice": w3.eth.gas_price, "nonce": w3.eth.get_transaction_count(wallet), "from": wallet}
    )
    approve_hash = w3.eth.send_transaction(approve_txn)
    assert approve_hash

    deposit_txn = tellorflex.functions.depositStake(_amount=int(5000e18)).buildTransaction(
        {"gas": 350000, "gasPrice": w3.eth.gas_price, "nonce": w3.eth.get_transaction_count(wallet), "from": wallet}
    )
    deposit_hash = w3.eth.send_transaction(deposit_txn)
    assert deposit_hash

    first_submit_txn = tellorflex.functions.submitValue(
        _queryId=mimicry_nft_market_index_usd_feed.query.query_id,
        _value=value,
        _nonce=0,
        _queryData=mimicry_nft_market_index_usd_feed.query.query_data,
    ).buildTransaction(
        {"gas": 350000, "gasPrice": w3.eth.gas_price, "nonce": w3.eth.get_transaction_count(wallet), "from": wallet}
    )
    submit_hash = w3.eth.send_transaction(first_submit_txn)
    assert submit_hash

    first_receipt = w3.eth.wait_for_transaction_receipt(submit_hash.hex())
    # bypass reporter lock
    increase_time(w3, 86400)
    bad_value = val + (val * 0.9)
    bad_val_encoded = mimicry_nft_market_index_usd_feed.query.value_type.encode(bad_value)
    second_submit_txn = tellorflex.functions.submitValue(
        _queryId=mimicry_nft_market_index_usd_feed.query.query_id,
        _value=bad_val_encoded,
        _nonce=0,
        _queryData=mimicry_nft_market_index_usd_feed.query.query_data,
    ).buildTransaction(
        {"gas": 350000, "gasPrice": w3.eth.gas_price, "nonce": w3.eth.get_transaction_count(wallet), "from": wallet}
    )
    second_submit_hash = w3.eth.send_transaction(second_submit_txn)
    second_receipt = w3.eth.wait_for_transaction_receipt(second_submit_hash.hex())
    # revert the chain
    revert_to_snapshot(w3, snapshot_id["result"])
    with patch(
        "telliot_feeds.sources.mimicry.nft_market_index.NFTGoSource.fetch_new_datapoint",
        AsyncMock(side_effect=lambda: (val, datetime_now_utc())),
    ):
        parse_first_event = await parse_new_report_event(
            cfg,
            monitored_feeds=AutoDisputerConfig(is_disputing=True, confidence_flag=None).monitored_feeds,
            confidence_threshold=0.75,
            log=first_receipt["logs"][1],
        )
        parse_second_event = await parse_new_report_event(
            cfg,
            monitored_feeds=AutoDisputerConfig(is_disputing=True, confidence_flag=None).monitored_feeds,
            confidence_threshold=0.75,
            log=second_receipt["logs"][1],
        )
        # good report
        assert not parse_first_event.disputable
        # bad report
        assert parse_second_event.disputable
