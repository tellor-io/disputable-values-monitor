"""Send text messages using Twilio."""
import os

from twilio.rest import Client

# import json


def generate_alert_msg(link: str) -> str:
    """Generate an alert message string that
    includes a link to a relevant expolorer."""
    return f"\n❗DISPUTABLE VALUE❗\n{link}"


def get_from_number() -> str:
    """Read the Twilio from number from the environment."""
    return os.environ.get("TWILIO_FROM")


def get_twilio_client():
    """Get a Twilio client."""
    return Client(os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))


def get_phone_numbers() -> list[str]:
    """Get the phone numbers to send text messages to."""
    print("ALERT RECIPIENTS:", os.environ.get("ALERT_RECIPIENTS"))
    # return json.loads(os.environ.get("ALERT_RECIPIENTS"))
    return os.environ.get("ALERT_RECIPIENTS").split(",")


def send_text_msg(client, recipients, from_number, msg):
    """Send a text message to the recipients."""
    # print(type(recipients))
    for num in recipients:
        # print('num', num)
        client.messages.create(
            to=num,
            from_=from_number,
            body=msg,
        )
