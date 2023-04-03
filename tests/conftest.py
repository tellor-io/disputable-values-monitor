import os
import warnings

import pytest
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from dotenv import load_dotenv
from hexbytes import HexBytes
from telliot_core.apps.core import TelliotConfig
from telliot_core.directory import contract_directory
from telliot_core.directory import ContractInfo
from telliot_core.model.endpoints import RPCEndpoint
from twilio.base.exceptions import TwilioException
from web3 import Web3
from web3.datastructures import AttributeDict

from tellor_disputables.alerts import get_twilio_client

load_dotenv()


@pytest.fixture
def log():
    return AttributeDict(
        {
            "address": "0xB3B662644F8d3138df63D2F43068ea621e2981f9",
            "topics": [
                HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"),
                HexBytes("0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"),
                HexBytes("0x000000000000000000000000000000000000000000000000000000006387ddcf"),
                HexBytes("0x0000000000000000000000000021053b73a20cb418d0458f543ac3e46d24137e"),
            ],
            "data": "0x000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000009e800000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000461f0eabb0b7870000000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003657468000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000037573640000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            "blockNumber": 16085880,
            "transactionHash": HexBytes("0xbf71154020b6e96c6c5db54ab97c40db3b73cf80ddda235b5204cf6d63ef5da7"),
            "transactionIndex": 16,
            "blockHash": HexBytes("0xcf720f24b1793eb4d58c6137535e6512b7e62794d1ef4db61eff9dc7c67ef03b"),
            "logIndex": 63,
            "removed": False,
        }
    )


@pytest.fixture
def disputer_account():

    account_name = "disputer-test-acct"

    if not find_accounts(account_name, 1337):
        ChainedAccount.add(account_name, 1337, os.getenv("PRIVATE_KEY"), "")

    disputer = find_accounts(account_name, 1337)[0]

    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    multisig = Web3.toChecksumAddress("0x39e419ba25196794b595b2a595ea8e527ddc9856")

    w3.eth.send_transaction(
        {
            "chainId": 1337,
            "gasPrice": w3.eth.gas_price,
            "from": multisig,
            "to": Web3.toChecksumAddress(disputer.address),
            "value": int(1e19),
        }
    )

    return disputer


@pytest.fixture
def check_twilio_configured() -> None:
    try:
        _ = get_twilio_client()
    except TwilioException as e:
        warnings.warn(str(e), stacklevel=2)
        pytest.skip(str(e))


@pytest.fixture
def setup():

    token_contract_info = contract_directory.find(name="trb-token", chain_id=1)[0]
    governance_contract_info = contract_directory.find(name="tellor-governance", chain_id=1)[0]
    oracle_contract_info = contract_directory.find(name="tellor360-oracle", chain_id=1)[0]

    contract_directory.entries["tellor360-oracle"].address[1337] = oracle_contract_info.address[1]

    forked_token = ContractInfo(
        "trb-token-fork", "Ganache", {1337: token_contract_info.address[1]}, token_contract_info.abi_file
    )
    forked_governance = ContractInfo(
        "tellor-governance-fork",
        "Ganache",
        {1337: governance_contract_info.address[1]},
        governance_contract_info.abi_file,
    )

    contract_directory.add_entry(forked_token)
    contract_directory.add_entry(forked_governance)

    cfg = TelliotConfig()
    cfg.main.chain_id = 1337
    ganache_endpoint = RPCEndpoint(1337, url="http://localhost:8545")
    cfg.endpoints.endpoints.append(ganache_endpoint)

    yield cfg

    del contract_directory.entries["trb-token-fork"], contract_directory.entries["tellor-governance-fork"]
    cfg.endpoints.endpoints.remove(ganache_endpoint)
