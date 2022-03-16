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
from tellor_disputables.data import get_events
from tellor_disputables.data import get_web3
from tellor_disputables.data import get_contract_info
from tellor_disputables.data import parse_new_report_event
from tellor_disputables.data import get_contract
from tellor_disputables.utils import EXAMPLE_NEW_REPORT_EVENT
from time import sleep
import uuid
import random
import asyncio


def dashboard():
    st.title("Disputable Values Monitor 📒🔎📲")
    st.write("get text alerts when potentially bad data is reported to Tellor oracles")

    st.markdown("[source code](https://github.com/tellor-io/disputable-values-monitor)")

    st.write("(only checks disputability of SpotPrice and LegacyRequest query types")

    # st.write(f'Sending alerts to: {get_phone_numbers()}')
    # st.write(os.environ.get("TWILIO_FROM"))

    twilio_client = get_twilio_client()
    recipients = get_phone_numbers()
    from_number = get_from_number()

    @st.cache(allow_output_mutation=True)
    def Rows():
        return []

    display_rows = Rows()
    table = st.empty()
    displayed_events = set()

    # Get contract addresses & web3 instances
    eth_chain_id = 1
    eth_web3 = get_web3(eth_chain_id)
    eth_addr, eth_abi = get_contract_info(eth_chain_id)
    eth_contract = get_contract(eth_web3, eth_addr, eth_abi)
    poly_chain_id = 80001
    poly_web3 = get_web3(poly_chain_id)
    poly_addr, poly_abi = get_contract_info(poly_chain_id)
    poly_contract = get_contract(poly_web3, poly_addr, poly_abi)


    while True:
        # Fetch NewReport events
        event_lists = asyncio.run(get_events(
            eth_web3,
            eth_addr,
            eth_abi,
            poly_web3,
            poly_addr,
        ))

        for event_list in event_lists:
            # event_list = [(80001, EXAMPLE_NEW_REPORT_EVENT)]
            for event_info in event_list:
                chain_id, event = event_info
                if chain_id == eth_chain_id:
                    new_report = parse_new_report_event(event, eth_web3, eth_contract)
                elif chain_id == poly_chain_id:
                    new_report = parse_new_report_event(event, poly_web3, poly_contract)
                else:
                    print("unsupported chain!")
                    continue

                # Skip duplicate events
                if new_report.tx_hash in displayed_events:
                    continue
                displayed_events.add(new_report.tx_hash)

                # Determine if value disputable
                disputable = is_disputable(new_report.value, "")
                link = get_tx_explorer_url(
                    tx_hash=new_report.tx_hash,
                    chain_id=new_report.chain_id)
                
                # Alert via text msg
                msg = generate_alert_msg(link)
                if disputable:
                    send_text_msg(twilio_client, recipients, from_number, msg)
            
                display_rows.append((
                    new_report.tx_hash,
                    new_report.eastern_time,
                    link,
                    new_report.query_type,
                    new_report.value,
                    disputable_str(disputable),
                    new_report.asset,
                    new_report.currency
                    ))

                # Prune display
                if len(display_rows) > 10:
                    # TODO FIX
                    displayed_events.remove(display_rows[0][0])
                    del(display_rows[0])

                # Display table
                _, times, links, _, values, disputable_strs, assets, currencies = zip(*display_rows)
                dataframe_state = dict(
                    When=times,
                    Transaction=links,
                    # QueryType=query_types,
                    Asset=assets,
                    Currency=currencies,
                    Value=values,
                    Disputable=disputable_strs)
                table.dataframe(dataframe_state)

        sleep(1)
