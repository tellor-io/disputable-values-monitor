from twilio.rest import Client
import os
import json


def generate_alert_msg():
    return "🔮 this is from tellor disputables app 🔮"


def get_from_number():
    return os.environ.get("TWILIO_FROM")


def get_twilio_client():
    return Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )


def get_phone_numbers():
    return json.loads(os.environ.get("ALERT_RECIPIENTS"))


def send_text_msg(client, recipients, from_number):
    msg = generate_alert_msg()

    for num in recipients:
        client.messages.create(
            to=num,
            from_=from_number,
            body=msg,
        )
