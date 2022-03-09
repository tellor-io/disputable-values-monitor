from twilio.rest import Client
import os
import json


def generate_alert_msg(link: str) -> str:
    return f"\n❗DISPUTABLE VALUE❗\n{link}"


def get_from_number() -> str:
    return os.environ.get("TWILIO_FROM")


def get_twilio_client():
    return Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )


def get_phone_numbers() -> list[str]:
    return json.loads(os.environ.get("ALERT_RECIPIENTS"))


def send_text_msg(client, recipients, from_number, msg):
    # print(type(recipients))
    for num in recipients:
        # print('num', num)
        client.messages.create(
            to=num,
            from_=from_number,
            body=msg,
        )
