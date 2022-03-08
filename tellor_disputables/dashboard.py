import streamlit as st
from tellor_disputables.utils import check_password
from tellor_disputables.alerts import send_text_msg
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_from_number
import os
from time import sleep


def dashboard():
    if check_password():
        st.write("🔎 Disputable Values Monitor 🧮")
        st.write(f'Sending alerts to: {", ".join(get_phone_numbers())}')

        twilio_client = get_twilio_client()
        recipients = get_phone_numbers()
        from_number = get_from_number()

        while True:
            send_text_msg(twilio_client, recipients, from_number)
            sleep(10)
