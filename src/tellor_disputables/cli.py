"""CLI dashboard to display recent values reported to Tellor oracles."""
import asyncio
import warnings
from time import sleep

import pandas as pd

from tellor_disputables.alerts import generate_alert_msg
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.alerts import get_twilio_client
from tellor_disputables.alerts import send_text_msg
from tellor_disputables.data import get_contract
from tellor_disputables.data import get_contract_info
from tellor_disputables.data import get_events
from tellor_disputables.data import get_web3
from tellor_disputables.data import parse_new_report_event
from tellor_disputables.utils import clear_console


warnings.simplefilter("ignore", UserWarning)


def print_title_info() -> None:
    """Prints the title info."""
    print("Disputable Values Monitor 📒🔎📲")
    # print("get text alerts when potentially bad data is reported to Tellor oracles")
    # print("(only checks disputability of SpotPrice and LegacyRequest query types)")


def cli() -> None:
    """CLI dashboard to display recent values reported to Tellor oracles."""
    print_title_info()

    recipients = get_phone_numbers()
    from_number = get_from_number()
    if recipients is None or from_number is None:
        print("Missing phone numbers. Exiting.")
        return
    twilio_client = get_twilio_client()

    display_rows = []
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
        event_lists = asyncio.run(
            get_events(
                eth_web3,
                eth_addr,
                eth_abi,
                poly_web3,
                poly_addr,
            )
        )

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

                # Skip duplicate & missing events
                if new_report is None or new_report.tx_hash in displayed_events:
                    continue
                displayed_events.add(new_report.tx_hash)

                # Refesh
                clear_console()
                print_title_info()

                # Account for unsupported queryIDs
                if new_report.disputable is not None:
                    # Alert via text msg
                    msg = generate_alert_msg(new_report.link)
                    if new_report.disputable:
                        send_text_msg(twilio_client, recipients, from_number, msg)

                display_rows.append(
                    (
                        new_report.tx_hash,
                        new_report.eastern_time,
                        new_report.link,
                        new_report.query_type,
                        new_report.value,
                        new_report.status_str,
                        new_report.asset,
                        new_report.currency,
                    )
                )

                # Prune display
                if len(display_rows) > 10:
                    displayed_events.remove(display_rows[0][0])
                    del display_rows[0]

                # Display table
                _, times, links, _, values, disputable_strs, assets, currencies = zip(*display_rows)
                dataframe_state = dict(
                    When=times,
                    Transaction=links,
                    # QueryType=query_types,
                    Asset=assets,
                    Currency=currencies,
                    Value=values,
                    Disputable=disputable_strs,
                )
                df = pd.DataFrame.from_dict(dataframe_state)
                print(df.to_markdown(), end="\r")

        sleep(1)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
