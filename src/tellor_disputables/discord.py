"""Send text messages using Twilio."""
import os
from typing import List
from typing import Optional
from typing import Tuple

import click
from discordwebhook import Discord

from tellor_disputables import ALWAYS_ALERT_QUERY_TYPES
from tellor_disputables.data import NewReport


def generic_alert(msg: str) -> None:
    """Send a Discord message via webhook."""
    alert_bot = get_alert_bot()
    alert_bot.post(content=msg)
    return


def get_alert_bot() -> Tuple[Optional[str], Optional[List[str]]]:
    """Read the Discord webhook url from the environment."""
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    alert_bot = Discord(url=DISCORD_WEBHOOK_URL)
    return alert_bot if alert_bot is not None else None


def dispute_alert(msg: str) -> None:
    """send an alert that the dispute was successful to the user"""
    alert_bot = get_alert_bot()
    alert_bot.post(content=msg)
    print(msg)
    return


def alert(all_values: bool, new_report: NewReport, alert_bot: Discord) -> None:

    alert_bot = get_alert_bot()

    if new_report.query_type in ALWAYS_ALERT_QUERY_TYPES:
        msg = generate_alert_msg(False, new_report.link)
        send_discord_msg(alert_bot, msg)

        return

    # Account for unsupported queryIDs
    if new_report.disputable is not None:
        if new_report.disputable:
            msg = generate_alert_msg(True, new_report.link)

    # If user wants ALL NewReports
    if all_values:
        msg = generate_alert_msg(False, new_report.link)
        send_discord_msg(alert_bot, msg)

    else:
        if new_report.disputable:
            msg = generate_alert_msg(True, new_report.link)
            send_discord_msg(alert_bot, msg)


def generate_alert_msg(disputable: bool, link: str) -> str:
    """Generate an alert message string that
    includes a link to a relevant expolorer."""

    if disputable:
        return f"\n❗DISPUTABLE VALUE❗\n{link}"
    else:
        return f"\n❗NEW VALUE❗\n{link}"


def send_discord_msg(alert_bot: Discord, msg: str) -> None:
    """Send Discord alert."""
    try:
        click.echo("Alert sent!")
        alert_bot = get_alert_bot()
        alert_bot.post(content=msg)
    except Exception as e:
        print(f"No Webhook URL found. See documentation or try 'source vars.sh' commamnd. Also: {e}")

    return
