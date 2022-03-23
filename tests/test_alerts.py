import pytest
from twilio.rest import Client
import os

from tellor_disputables.alerts import generate_alert_msg
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import get_phone_numbers


def test_generate_alert_msg():
    link = "example transaction link"
    msg = generate_alert_msg(link)

    assert isinstance(msg, str)
    assert "example transaction link" in msg
    assert "DISPUTABLE VALUE" in msg


def test_get_from_number():
    os.environ["TWILIO_FROM"] = "+19035029327"
    num = get_from_number()

    assert num is not None
    assert isinstance(num, str)
    assert num == "+19035029327"


def test_get_twilio_client():
    client = get_twilio_client()

    assert isinstance(client, Client)


def test_get_phone_numbers():
    os.environ["ALERT_RECIPIENTS"] = "+17897894567,+17897894567,+17897894567"
    numbers = get_phone_numbers()

    assert isinstance(numbers, list)
    assert numbers == ["+17897894567", "+17897894567", "+17897894567"]
