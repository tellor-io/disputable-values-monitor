"""Get and parse NewReport events from Tellor oracles."""
import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Union

from dateutil import tz
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.directory import contract_directory
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries import SpotPrice
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.legacy_query import LegacyRequest
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import TransactionNotFound

from tellor_disputables import CONFIDENCE_THRESHOLD
from tellor_disputables import DATAFEED_LOOKUP
from tellor_disputables import LEGACY_ASSETS
from tellor_disputables import LEGACY_CURRENCIES
from tellor_disputables.utils import disputable_str
from tellor_disputables.utils import get_tx_explorer_url


def get_node_url() -> Optional[str]:
    """Get the node URL for the given chain ID."""
    return os.environ.get("NODE_URL", None)


def get_contract_info(chain_id: int) -> tuple[str, str]:
    """Get the contract address and ABI for the given chain ID."""
    name = "tellor360-oracle"
    contract_info = contract_directory.find(chain_id=chain_id, name=name)[0]
    addr = contract_info.address[chain_id]
    abi = contract_info.get_abi(chain_id=chain_id)
    return addr, abi


def get_web3() -> Web3:
    """Get a Web3 instance for the given chain ID."""
    node_url = get_node_url()
    if not node_url:
        raise ValueError("No node url found. Please set the environment variable NODE_URL.")
    return Web3(Web3.HTTPProvider(node_url))


def get_contract(web3: Web3, addr: str, abi: str) -> Contract:
    """Get a contract instance for the given address and ABI."""
    return web3.eth.contract(  # type: ignore
        address=addr,
        abi=abi,
    )


async def eth_log_loop(event_filter: Any, chain_id: int) -> list[tuple[int, Any]]:
    """Generate a list of NewReport events given a
    polling interval and an event filter."""
    unique_events = {}
    unique_events_lis = []

    for event in event_filter.get_new_entries():
        txhash = event["transactionHash"]

        if txhash not in unique_events:
            unique_events[txhash] = event
            unique_events_lis.append((chain_id, event))

    return unique_events_lis


async def log_loop(web3: Web3, addr: str) -> list[tuple[int, Any]]:
    """Generate a list of recent events from a contract."""
    num = web3.eth.get_block_number()
    try:
        events = web3.eth.get_logs({"fromBlock": num - 100, "toBlock": "latest", "address": addr})  # type: ignore
    except ValueError as e:
        msg = str(e)
        if "unknown block" in msg:
            logging.error("waiting for new blocks")
        elif "request failed or timed out" in msg:
            logging.error("request for eth event logs failed")
        else:
            logging.error("unknown RPC error gathering eth event logs \n" + msg)

        return []
    unique_events = {}
    unique_events_list = []

    for event in events:
        txhash = event["transactionHash"]

        if txhash not in unique_events:
            unique_events[txhash] = event
            unique_events_list.append((web3.eth.chain_id, event))

    return unique_events_list


async def general_fetch_new_datapoint(feed: DataFeed) -> Optional[Any]:
    """Fetch a new datapoint from a datafeed."""
    return await feed.source.fetch_new_datapoint()


async def is_disputable(reported_val: float, query_id: str, conf_threshold: float = 0.05) -> Optional[bool]:
    """Check if the reported value is disputable."""
    if reported_val is None:
        logging.error("Need reported value to check disputability")
        return None

    if query_id not in DATAFEED_LOOKUP:
        logging.info(f"new report for unsupported query ID: {query_id}")
        return None

    current_feed: DataFeed[Any] = DATAFEED_LOOKUP[query_id]
    trusted_val, _ = await general_fetch_new_datapoint(current_feed)
    if trusted_val is not None:
        percent_diff = (reported_val - trusted_val) / trusted_val
        return float(abs(percent_diff)) > conf_threshold
    else:
        logging.error("Unable to fetch new datapoint from feed")
        return None


@dataclass
class NewReport:
    """NewReport event."""

    tx_hash: str
    eastern_time: str
    chain_id: int
    link: str
    query_type: str
    value: float
    asset: str
    currency: str
    query_id: str
    disputable: Optional[bool]
    status_str: str


def timestamp_to_eastern(timestamp: int) -> str:
    """Convert a timestamp to Eastern Standard time."""
    est = tz.gettz("EST")
    dt = datetime.fromtimestamp(timestamp).astimezone(est)

    return str(dt)


def create_eth_event_filter(web3: Web3, addr: str, abi: str) -> Any:
    """Create an event filter for the given address and ABI."""
    contract = get_contract(web3, addr, abi)
    return contract.events.NewReport.createFilter(fromBlock="latest")


async def get_events(cfg: TelliotConfig) -> tuple[list[tuple[int, Any]], list[tuple[int, Any]]]:
    """Get all events from all live Tellor networks"""

    log_loops = []

    for endpoint in cfg.endpoints.endpoints:
        w3 = endpoint.web3
        addr, _ = get_contract_info(endpoint.chain_id)

        log_loops.append(log_loop(w3, addr))

    events_lists: tuple[list[tuple[int, Any]], list[tuple[int, Any]]] = await asyncio.gather(*log_loops)

    return events_lists


def get_tx_receipt(tx_hash: str, web3: Web3, contract: Contract) -> Any:
    """Get the transaction receipt for the given transaction hash."""
    try:
        receipt = web3.eth.getTransactionReceipt(tx_hash)
    except TimeoutError:
        logging.warning(f"timeout getting transaction receipt for {tx_hash}")
        return None
    except TransactionNotFound:
        logging.warning(f"transcation hash {tx_hash} not found")
        return None

    try:
        receipt = contract.events.NewReport().processReceipt(receipt)[0]
    except (IndexError, OverflowError):
        logging.warning(f"Unable to process receipt for transaction {tx_hash}")
        return None
    return receipt


def get_query_from_data(query_data: bytes) -> Optional[Union[AbiQuery, JsonQuery]]:
    """Generate query from query data."""
    q = None
    for q_type in (AbiQuery, JsonQuery):
        try:
            q = q_type.get_query_from_data(query_data)
        except:  # noqa: E722 B001
            continue
    return q


def get_legacy_request_pair_info(legacy_id: int) -> Optional[tuple[str, str]]:
    """Retrieve asset and currency from legacy request ID."""
    return LEGACY_ASSETS[legacy_id], LEGACY_CURRENCIES[legacy_id]


async def parse_new_report_event(cfg: TelliotConfig, tx_hash: str) -> Optional[NewReport]:
    """Parse a NewReport event."""

    chain_id = cfg.main.chain_id
    endpoint = cfg.endpoints.find(chain_id=chain_id)[0]

    if not endpoint:
        logging.error(f"Unable to find a suitable endpoint for chain_id {chain_id}")
        return None
    else:

        try:
            endpoint.connect()
            endpoint = endpoint.web3
        except ValueError as e:
            logging.error(f"Unable to connect to endpoint on chain_id {chain_id}: " + str(e))
            return None

        addr, abi = get_contract_info(chain_id)
        contract = get_contract(endpoint, addr, abi)

    try:
        receipt = get_tx_receipt(tx_hash, endpoint, contract)
    except TransactionNotFound:
        logging.error("transaction not found")
        return None

    if receipt is None:
        return None

    if receipt["event"] != "NewReport":
        return None

    args = receipt["args"]
    q = get_query_from_data(args["_queryData"])
    if isinstance(q, SpotPrice):
        asset = q.asset.upper()
        currency = q.currency.upper()
    elif isinstance(q, LegacyRequest):
        asset, currency = get_legacy_request_pair_info(q.legacy_id)
    else:
        logging.error("unsupported query type")
        return None

    val = q.value_type.decode(args["_value"])
    link = get_tx_explorer_url(tx_hash=tx_hash, cfg=cfg)
    query_id = str(q.query_id.hex())
    disputable = await is_disputable(val, query_id, CONFIDENCE_THRESHOLD)
    if disputable is None:
        logging.info("unable to check disputability")
        return None
    else:
        status_str = disputable_str(disputable, query_id)

        return NewReport(
            chain_id=endpoint.eth.chain_id,
            eastern_time=args["_time"],
            tx_hash=tx_hash,
            link=link,
            query_type=type(q).__name__,
            value=val,
            asset=asset,
            currency=currency,
            query_id=query_id,
            disputable=disputable,
            status_str=status_str,
        )
