"""Tests for generating alert messages."""
import time
from unittest import mock
from unittest import TestCase

from discordwebhook import Discord

from disputable_values_monitor.data import NewReport
from disputable_values_monitor.discord import alert
from disputable_values_monitor.discord import generate_alert_msg
from disputable_values_monitor.discord import get_alert_bot_1


def test_notify_typical_disputable(capsys):
    """Test a typical disputable value on ETH/USD feed"""

    def first_alert():
        print("alert sent")

    with (mock.patch("disputable_values_monitor.discord.send_discord_msg", side_effect=[first_alert()])):
        r = NewReport(
            "0xabc123",
            time.time(),
            1,
            "etherscan.io/abc",
            "query type",
            15.5,
            "eth",
            "usd",
            "query id",
            True,
            "status ",
        )

        alert(False, r)

        assert "alert sent" in capsys.readouterr().out


def test_generate_alert_msg():
    link = "example transaction link"
    msg = generate_alert_msg(True, link)

    assert isinstance(msg, str)
    assert "example transaction link" in msg
    assert "DISPUTABLE VALUE" in msg


@mock.patch("os.getenv")
def test_get_alert_bot(mock_getenv):
    mock_getenv.return_value = "a"
    alert_bot = get_alert_bot_1()

    assert isinstance(alert_bot, Discord)


def test_notify_non_disputable(capsys):
    """test sending an alert on any new value event if all_values flag is True"""

    def first_alert():
        print("alert sent")

    def second_alert():
        print("second alert sent")

    with (
        mock.patch("disputable_values_monitor.discord.send_discord_msg", side_effect=[first_alert(), second_alert()])
    ):
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
        alert(True, r)

        assert "alert sent" in capsys.readouterr().out

        alert(False, r)

        assert "second alert sent" not in capsys.readouterr().out


def test_notify_always_alertable_value(capsys):
    """test sending an alert for a NewReport event
    if the query type is always alertable"""

    def first_alert():
        print("alert sent")

    def second_alert():
        print("second alert sent")

    with (
        mock.patch("disputable_values_monitor.discord.send_discord_msg", side_effect=[first_alert(), second_alert()])
    ):
        r = NewReport(
            "0xabc123",
            time.time(),
            1,
            "etherscan.io/abc",
            "TellorOracleAddress",
            "0xabcNewTellorAddress",
            None,
            None,
            "query id",
            None,
            "status ",
        )
        alert(True, r)

        assert "alert sent" in capsys.readouterr().out

        alert(False, r)

        assert "second alert sent" not in capsys.readouterr().out


def test_discord_object_return_if_no_webhook():
    """test that None is returned if no webhook"""
    alert_bot = Discord(url=None)
    assert isinstance(alert_bot, Discord)
    assert alert_bot is not None


@mock.patch("os.getenv")
def test_alert_bot_if_no_webhook(mock_getenv):
    """test that None is returned if no webhook"""
    mock_getenv.return_value = None
    with TestCase().assertRaises(Exception) as context:
        get_alert_bot_1()
    assert "At least one DISCORD_WEBHOOK_URL is required. See docs or try source 'vars.sh'." in str(context.exception)
    mock_getenv.return_value = "a"
    alert_bot = get_alert_bot_1()
    assert isinstance(alert_bot, Discord)
    assert alert_bot.url == "a"
    assert alert_bot.url is not None
