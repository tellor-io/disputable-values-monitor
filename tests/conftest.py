import pytest
from tellor_disputables.data import get_web3
from twilio.base.exceptions import TwilioException
from tellor_disputables.alerts import get_twilio_client
import warnings


@pytest.fixture
def check_web3_configured() -> None:
    try:
        _ = get_web3(chain_id=1)
    except ValueError as e:
        warnings.warn(str(e))
        pytest.skip(str(e))

@pytest.fixture
def check_twilio_configured() -> None:
    try:
        _ = get_twilio_client()
    except TwilioException as e:
        warnings.warn(str(e))
        pytest.skip(str(e))