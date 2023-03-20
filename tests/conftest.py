import os
import warnings
from chained_accounts import ChainedAccount, find_accounts
from dotenv import load_dotenv

import pytest
from twilio.base.exceptions import TwilioException

from web3 import Web3

from tellor_disputables.alerts import get_twilio_client

load_dotenv()        

@pytest.fixture
def disputer_account():

    account_name = "disputer-test-acct"

    if not find_accounts(account_name, 1337):
        ChainedAccount.add(account_name, 1337, os.getenv("PRIVATE_KEY"), "")

    disputer = find_accounts(account_name, 1337)[0]

    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

    w3.eth.send_transaction({
        "from": w3.eth.coinbase,
        "to": Web3.toChecksumAddress(disputer.address),
        "value": 100000000000000000000
    })


    return disputer


@pytest.fixture
def check_twilio_configured() -> None:
    try:
        _ = get_twilio_client()
    except TwilioException as e:
        warnings.warn(str(e), stacklevel=2)
        pytest.skip(str(e))