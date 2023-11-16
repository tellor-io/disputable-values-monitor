"""Send text messages using Twilio."""
import os

import click
from discordwebhook import Discord

from tellor_disputables import ALWAYS_ALERT_QUERY_TYPES
from tellor_disputables.data import NewReport


def generic_alert(msg: str) -> None:
    """Send a Discord message via webhook."""
    send_discord_msg(msg)
    return


def get_alert_bot() -> Discord:
    """Read the Discord webhook url from the environment."""
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    if DISCORD_WEBHOOK_URL is None:
        raise Exception("No DISCORD_WEBHOOK_URL found. See documentation or try 'source vars.sh' command.")
    alert_bot = Discord(url=DISCORD_WEBHOOK_URL)
    return alert_bot


def dispute_alert(msg: str) -> None:
    """send an alert that the dispute was successful to the user"""
    send_discord_msg(msg)
    print(msg)
    return


def alert(all_values: bool, new_report: NewReport) -> None:

    if new_report.query_type in ALWAYS_ALERT_QUERY_TYPES:
        msg = generate_alert_msg(False, new_report.link)
        send_discord_msg(msg)

        return

    # Account for unsupported queryIDs
    if new_report.disputable is not None:
        if new_report.disputable:
            msg = generate_alert_msg(True, new_report.link)

    # If user wants ALL NewReports
    if all_values:
        msg = generate_alert_msg(False, new_report.link)
        send_discord_msg(msg)

    else:
        if new_report.disputable:
            msg = generate_alert_msg(True, new_report.link)
            send_discord_msg(msg)


def generate_alert_msg(disputable: bool, link: str) -> str:
    """Generate an alert message string that
    includes a link to a relevant expolorer."""

    if disputable:
        return f"\n❗DISPUTABLE VALUE❗\n{link}"
    else:
        return f"\n❗NEW VALUE❗\n{link}"


def send_discord_msg(msg: str) -> None:
    """Send Discord alert."""
    get_alert_bot().post(content=msg)
    click.echo("Alert sent!")
    return
