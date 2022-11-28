"""Tests for generating alert messages."""
import os
import time
from unittest import mock

from twilio.rest import Client

from tellor_disputables.alerts import alert
from tellor_disputables.alerts import generate_alert_msg
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.data import NewReport


def test_generate_alert_msg():
    link = "example transaction link"
    msg = generate_alert_msg(True, link)

    assert isinstance(msg, str)
    assert "example transaction link" in msg
    assert "DISPUTABLE VALUE" in msg


def test_get_from_number():
    os.environ["TWILIO_FROM"] = "+19035029327"
    num = get_from_number()

    assert num is not None
    assert isinstance(num, str)
    assert num == "+19035029327"


def test_get_twilio_client(check_twilio_configured):
    client = get_twilio_client()

    assert isinstance(client, Client)


def test_get_phone_numbers():
    os.environ["ALERT_RECIPIENTS"] = "+17897894567,+17897894567,+17897894567"
    numbers = get_phone_numbers()

    assert isinstance(numbers, list)
    assert numbers == ["+17897894567", "+17897894567", "+17897894567"]


def test_notify_non_disputable(capsys):
    """test sending an alert on any new value event if all_values flag is True"""

    def first_alert():
        print("alert sent")

    def second_alert():
        print("second alert sent")

    with (mock.patch("tellor_disputables.alerts.send_text_msg", side_effect=[first_alert(), second_alert()])):
        r = NewReport(
            "0xabc123",
            time.time(),
            1,
            "etherscan.io/abc",
            "query type",
            15.5,
            "trb",
            "usd",
            "query id",
            None,
            "status ",
        )
        alert(True, r, "", "")

        assert "alert sent" in capsys.readouterr().out

        alert(False, r, "", "")

        assert "second alert sent" not in capsys.readouterr().out


def test_notify_always_alertable_value(capsys):
    """test sending an alert for a NewReport event
    if the query type is always alertable"""

    def first_alert():
        print("alert sent")

    def second_alert():
        print("second alert sent")

    with (mock.patch("tellor_disputables.alerts.send_text_msg", side_effect=[first_alert(), second_alert()])):
        r = NewReport(
            "0xabc123",
            time.time(),
            1,
            "etherscan.io/abc",
            "TellorOracleAddress",
            15.5,
            "trb",
            "usd",
            "query id",
            None,
            "status ",
        )
        alert(True, r, "", "")

        assert "alert sent" in capsys.readouterr().out

        alert(False, r, "", "")

        assert "second alert sent" not in capsys.readouterr().out
