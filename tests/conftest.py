import warnings

import pytest
from twilio.base.exceptions import TwilioException

from tellor_disputables.alerts import get_twilio_client


@pytest.fixture
def check_twilio_configured() -> None:
    try:
        _ = get_twilio_client()
    except TwilioException as e:
        warnings.warn(str(e), stacklevel=2)
        pytest.skip(str(e))
