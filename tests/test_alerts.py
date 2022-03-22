import pytest
from twilio.rest import Client
import os

from src.tellor_disputables.alerts import generate_alert_msg
from src.tellor_disputables.alerts import get_from_number
from src.tellor_disputables.alerts import get_twilio_client
from src.tellor_disputables.alerts import get_phone_numbers


def test_generate_alert_msg():
    link = "example transaction link"
    msg = generate_alert_msg(link)
    assert isinstance(msg, str)


def test_get_from_number():
    get_from_num = get_from_number()
    assert isinstance(get_from_num, str)
    assert get_from_num == "+19035029327"


def test_get_twilio_client():
    client = get_twilio_client()
    assert isinstance(client, Client)


def test_get_phone_numbers():
    numbers = get_phone_numbers()
    assert isinstance(numbers, list)
    assert numbers == ["+17897894567", "+17897894567", "+17897894567"]
