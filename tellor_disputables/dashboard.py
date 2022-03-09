import streamlit as st
from tellor_disputables.alerts import send_text_msg
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import generate_alert_msg
from tellor_disputables.utils import get_tx_explorer_url
from tellor_disputables.utils import disputable_str
from tellor_disputables.data import get_new_report
from tellor_disputables.data import is_disputable
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
        new_report = get_new_report('{"blah":42}')

        disputable = is_disputable(new_report.value, "")
        link = get_tx_explorer_url(
            new_report.transaction_hash,
            new_report.chain_id)
        
        msg = generate_alert_msg(link)
        if disputable:
            send_text_msg(twilio_client, recipients, from_number, msg)
        
        txs.append((
            new_report.chain_id,
            link,
            new_report.query_type,
            new_report.value,
            disputable_str(disputable)))

        if len(txs) > 10:
            del(txs[0])

        chain_ids, links, query_types, values, disputable_strs = zip(*txs)
        dataframe_state = dict(
            Chain=chain_ids,
            Link=links,
            QueryType=query_types,
            ReportedValue=values,
            Disputable=disputable_strs)
        table.dataframe(dataframe_state)

        sleep(3)
