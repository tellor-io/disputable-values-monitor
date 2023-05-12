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


@pytest.fixture(scope="function", autouse=True)
def reset_chain():
    """Reset the chain after each test"""
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    snapshot_id = w3.provider.make_request("evm_snapshot", [])

    yield

    w3.provider.make_request("evm_revert", [snapshot_id["result"]])


@pytest.fixture
def eth_usd_report_log():
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
def evm_call_log():
    return AttributeDict(
        {
            "address": "0xD9157453E2668B2fc45b7A803D3FEF3642430cC0",
            "topics": [
                HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"),
                HexBytes("0xd7472d51b2cd65a9c6b81da09854efdeeeff8afcda1a2934566f54b731a922f3"),
                HexBytes("0x0000000000000000000000000000000000000000000000000000000064381849"),
                HexBytes("0x000000000000000000000000a7654e313fbb25b2cf367730cb5c2759faf831a1"),
            ],
            "data": "0x0000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000001b00000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000643818460000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000020c4abd206827e8190955000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000745564d43616c6c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000100000000000000000000000088df592f8eb5d7bd38bfef7deb0fbc02cf3778a00000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000418160ddd00000000000000000000000000000000000000000000000000000000",  # noqa: E501
            "blockNumber": 34326172,
            "transactionHash": HexBytes("0x8548eaa213e316fe837f97057694c2ab47e65b882f422a828a2429971d99119c"),
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
        ChainedAccount.add(account_name, 1337, "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d", "")

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
    autopay_contract_info = contract_directory.find(name="tellor360-autopay", chain_id=1)[0]

    contract_directory.entries["tellor360-oracle"].address[1337] = oracle_contract_info.address[1]
    contract_directory.entries["trb-token"].address[1337] = token_contract_info.address[1]
    contract_directory.entries["tellor360-autopay"].address[1337] = autopay_contract_info.address[1]

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
    mainnet_endpoint = cfg.endpoints.find(chain_id=1)
    if mainnet_endpoint and mainnet_endpoint[0].url.endswith("{INFURA_API_KEY}"):
        mainnet_endpoint[0].url = os.getenv("MAINNET_URL")

    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    token = w3.eth.contract(address=token_contract_info.address[1], abi=token_contract_info.get_abi(1))
    transfer = token.get_function_by_name("transfer")
    # transfer 100 TRB to the disputer account
    token_txn = transfer("0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1", int(100e18)).buildTransaction(
        {
            "gas": 500000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count("0x39E419bA25196794B595B2a595Ea8E527ddC9856"),
            "from": "0x39E419bA25196794B595B2a595Ea8E527ddC9856",
        }
    )
    w3.eth.send_transaction(token_txn)

    yield cfg

    del contract_directory.entries["trb-token-fork"], contract_directory.entries["tellor-governance-fork"]
    cfg.endpoints.endpoints.remove(ganache_endpoint)
