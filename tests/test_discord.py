"""Tests for generating alert messages."""
import os
#import time
#from unittest import mock

from discordwebhook import Discord

#from tellor_disputables.discord import alert
#from tellor_disputables.discord import generate_alert_msg
from tellor_disputables.discord import get_alert_bot
#from tellor_disputables.data import NewReport


def test_get_alert_bot():
    os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/your/webhook/url"
    alert_bot = get_alert_bot()

    assert alert_bot is not None
    assert isinstance(alert_bot, str)
    assert alert_bot == "https://discord.com/api/webhooks/your/webhook/url"
