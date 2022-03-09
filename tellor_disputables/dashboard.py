import streamlit as st
# from tellor_disputables.utils import check_password
from tellor_disputables.alerts import send_text_msg
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import generate_alert_msg
from tellor_disputables.utils import get_tx_explorer_url
# from tellor_disputables.utils import remove_default_index_col
import os
from time import sleep
import uuid
import random


def dashboard():
    st.title("Disputable Values Monitor 📒🔎📲")
    st.write("get text alerts when potentially bad data is reported to Tellor oracles")

    st.markdown("[source code](https://github.com/oraclown/tellor_disputes_monitor)")

    # st.write(f'Sending alerts to: {get_phone_numbers()}')
    # st.write(os.environ.get("TWILIO_FROM"))

    twilio_client = get_twilio_client()
    recipients = get_phone_numbers()
    from_number = get_from_number()

    @st.cache(allow_output_mutation=True)
    def Txs():
        return []

    txs=Txs()
    table = st.empty()

    while True:
        # get fake data
        tx_hash = uuid.uuid4().hex
        value = f"${round(random.uniform(2000, 3500), 2)}"
        disputable = random.random() > .995
        disputable_str = "yes ❗📲" if disputable else "no ✔️"
        chain_id = random.choice([1, 137])
        link = get_tx_explorer_url(tx_hash, chain_id)
        query_type = "SpotPrice"
        
        msg = generate_alert_msg(link)
        if disputable:
            send_text_msg(twilio_client, recipients, from_number, msg)
        
        txs.append((chain_id, link, query_type, value, disputable_str))

        if len(txs) > 10:
            del(txs[0])

        chain_id, link, query_type, value, disputable_str = zip(*txs)
        txs1 = dict(
            Chain=chain_id,
            Link=link,
            QueryType=query_type,
            ReportedValue=value,
            Disputable=disputable_str)
        table.dataframe(txs1)

        sleep(3)
