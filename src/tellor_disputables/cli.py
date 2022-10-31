"""CLI dashboard to display recent values reported to Tellor oracles."""
import logging
import warnings
from time import sleep

import click
import pandas as pd
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.cli.utils import async_run

from tellor_disputables import WAIT_PERIOD
from tellor_disputables.alerts import alert
from tellor_disputables.alerts import get_from_number
from tellor_disputables.alerts import get_phone_numbers
from tellor_disputables.data import get_events
from tellor_disputables.data import parse_new_report_event
from tellor_disputables.utils import clear_console


warnings.simplefilter("ignore", UserWarning)


def print_title_info() -> None:
    """Prints the title info."""
    logging.basicConfig(filename="log.txt", level=logging.INFO, format="%(asctime)s %(message)s")
    click.echo("Disputable Values Monitor 📒🔎📲")
    # print("get text alerts when potentially bad data is reported to Tellor oracles")
    # print("(only checks disputability of SpotPrice and LegacyRequest query types)")


@click.command()
@click.option("-a", "--all-values", is_flag=True, show_default=True)
@click.option("-w", "--wait", help="how long to wait between checks", type=int)
@async_run
async def main(all_values: bool, wait: int) -> None:
    """CLI dashboard to display recent values reported to Tellor oracles."""
    await start(all_values=all_values, wait=wait)


async def start(all_values: bool, wait: int) -> None:
    # Fetch optional wait period
    wait_period = wait if wait else WAIT_PERIOD
    print_title_info()

    recipients = get_phone_numbers()
    from_number = get_from_number()
    if recipients is None or from_number is None:
        logging.error("Missing phone numbers. See README for required environment variables. Exiting.")
        return

    display_rows = []
    displayed_events = set()

    # Get contract addresses & web3 instances
    # eth_chain_id = ETHEREUM_CHAIN_ID
    # eth_web3 = get_web3()
    # eth_addr, eth_abi = get_contract_info(eth_chain_id)
    # eth_contract = get_contract(eth_web3, eth_addr, eth_abi)
    # poly_chain_id = POLYGON_CHAIN_ID
    # poly_web3 = get_web3()
    # poly_addr, poly_abi = get_contract_info(poly_chain_id)
    # poly_contract = get_contract(poly_web3, poly_addr, poly_abi)

    while True:

        cfg = TelliotConfig()
        # Fetch NewReport events
        event_lists = await get_events(cfg=cfg)

        for event_list in event_lists:
            # event_list = [(80001, EXAMPLE_NEW_REPORT_EVENT)]
            for event_info in event_list:

                chain_id, event = event_info
                cfg.main.chain_id = chain_id

                try:
                    new_report = await parse_new_report_event(cfg, event["txHash"])
                except Exception as e:
                    logging.error("unsupported chain! " + str(e))
                    continue

                # Skip duplicate & missing events
                if new_report is None or new_report.tx_hash in displayed_events:
                    continue
                displayed_events.add(new_report.tx_hash)

                # Refesh
                clear_console()
                print_title_info()

                alert(all_values, new_report, recipients, from_number)

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
                df.to_csv("table.csv")

        sleep(wait_period)


if __name__ == "__main__":
    main()
