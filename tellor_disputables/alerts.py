from twilio.rest import Client
import os
import json


def generate_alert_msg(txhash: str) -> str:
    return f"\n❗DISPUTABLE VALUE❗\nhttps://rinkeby.etherscan.io/tx/0x{txhash}"


def get_from_number() -> str:
    return os.environ.get("TWILIO_FROM")


def get_twilio_client():
    return Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )


def get_phone_numbers() -> list[str]:
    return os.environ.get("ALERT_RECIPIENTS")


def send_text_msg(client, recipients, from_number, msg):
    for num in recipients:
        client.messages.create(
            to=num,
            from_=from_number,
            body=msg,
        )
