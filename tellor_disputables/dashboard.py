import streamlit as st
# from tellor_disputables.utils import check_password
from tellor_disputables.alerts import send_text_msg
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_from_number
import os
from time import sleep
import uuid
import random


def dashboard():
    # if check_password():
    # st.write(f'Sending alerts to: {", ".join(get_phone_numbers())}')
    # st.write(os.environ.get("TWILIO_FROM"))

    # twilio_client = get_twilio_client()
    # recipients = get_phone_numbers()
    # from_number = get_from_number()
    # send_text_msg(twilio_client, recipients, from_number)

    @st.cache(allow_output_mutation=True)
    def Txs():
        return []

    txs=Txs()

    st.write("Disputable Values Monitor 🧮🔎")
    table = st.empty()

    while True:
        tx_hash = uuid.uuid4().hex
        data = f"${round(random.uniform(2000, 3500), 2)}"
        disputable = "yes ❗" if random.random()>.8 else "no ✔️"
        txs.append((tx_hash,data,disputable))

        if len(txs) > 10:
            del(txs[0])

        tx_hash, data, disputable = zip(*txs)
        txs1 = dict(TxHash=tx_hash, ReportedValue=data, Disputable=disputable)
        table.dataframe(txs1)

        sleep(3)
