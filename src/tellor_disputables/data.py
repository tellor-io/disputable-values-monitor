"""Get and parse NewReport events from Tellor oracles."""
import asyncio
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from enum import Enum
from typing import Any
from typing import Optional
from typing import Union
from chained_accounts import ChainedAccount

from telliot_core.model.base import Base
from telliot_feeds.datafeed import DataFeed

from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.directory import contract_directory
from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.json_query import JsonQuery
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.queries.query import OracleQuery
from web3 import Web3
from web3._utils.events import get_event_data
from web3.types import LogReceipt

from tellor_disputables import ALWAYS_ALERT_QUERY_TYPES
from tellor_disputables import NEW_REPORT_ABI
from tellor_disputables import WAIT_PERIOD
from tellor_disputables.utils import disputable_str
from tellor_disputables.utils import get_logger
from tellor_disputables.utils import get_tx_explorer_url
from tellor_disputables.utils import NewReport

from telliot_core.contract.contract import Contract

logger = get_logger(__name__)

class Metrics(Enum):
    Percentage = "percentage"
    Equality = "equality"
    Range = "range"


@dataclass
class Threshold(Base):
    """
    A Threshold for sending a dispute.

    amount (Optional[int]) -- amount of tolerated difference between
    submitted on-chain values and trusted values from telliot.

    metric (Metrics) -- type of threshold

    If self.metric == "percentage", amount is a percent with a minimum of 0
    If self.metric == "equality", amount is None
    If self.metric == "range", amount is the maximum distance an on-chain value can have from
    the trusted value from telliot
    """

    metric: Metrics
    amount: Union[int, float, None]

    def __post_init__(self) -> None:

        if self.metric == Metrics.Equality:
            logger.warning("Equality threshold selected, ignoring amount")
            self.amount = None

        if self.metric != Metrics.Equality:
            if self.amount is None:
                raise ValueError(f"{self.metric} threshold selected, amount cannot be None")

            if self.amount < 0:
                raise ValueError(f"{self.metric} threshold selected, amount cannot be negative")


@dataclass
class MonitoredFeed(Base):
    feed: DataFeed[Any]
    threshold: Threshold
    query_id: Optional[str] = None

    async def is_disputable(
        self,
        reported_val: Union[str, bytes, float, int, None],
    ) -> Optional[bool]:
        """Check if the reported value is disputable."""
        if reported_val is None:
            logger.error("Need reported value to check disputability")
            return None

        trusted_val, _ = await general_fetch_new_datapoint(self.feed)
        if not trusted_val:
            logger.warning("trusted val was " + str(trusted_val))
            return None

        if isinstance(trusted_val, (str, int, float, bytes)):

            if self.threshold.metric == Metrics.Percentage:

                if isinstance(trusted_val, (str, bytes)) or isinstance(reported_val, (str, bytes)):
                    logger.error("Cannot evaluate percent difference on text/addresses/bytes")
                    return None
                if self.threshold.amount is None:
                    logger.error("Please set a threshold amount to measure percent difference")
                    return None
                percent_diff: float = (reported_val - trusted_val) / trusted_val
                return float(abs(percent_diff)) >= self.threshold.amount

            elif self.threshold.metric == Metrics.Range:

                if isinstance(trusted_val, (str, bytes)) or isinstance(reported_val, (str, bytes)):
                    logger.error("Cannot evaluate range on text/addresses/bytes")

                if self.threshold.amount is None:
                    logger.error("Please set a threshold amount to measure range")
                    return None
                range_: float = abs(reported_val - trusted_val)
                return range_ >= self.threshold.amount

            elif self.threshold.metric == Metrics.Equality:

                # if we have two bytes strings (not raw bytes)
                if (
                    (isinstance(reported_val, str))
                    and (isinstance(trusted_val, str))
                    and reported_val.startswith("0x")
                    and trusted_val.startswith("0x")
                ):
                    return trusted_val.lower() != reported_val.lower()
                return trusted_val != reported_val

            else:
                logger.error("Attemping comparison with unknown threshold metric")
                return None
        else:
            logger.error("Unable to fetch new datapoint from feed")
            return None


async def general_fetch_new_datapoint(feed: DataFeed) -> Optional[Any]:
    """Fetch a new datapoint from a datafeed."""
    return await feed.source.fetch_new_datapoint()


def get_contract_info(chain_id: int, name: str) -> Tuple[Optional[str], Optional[str]]:
    """Get the contract address and ABI for the given chain ID."""
    contracts = contract_directory.find(chain_id=chain_id, name=name)

    if len(contracts) > 0:
        contract_info = contracts[0]
        addr = contract_info.address[chain_id]
        abi = contract_info.get_abi(chain_id=chain_id)
        return addr, abi

    else:
        logger.info(f"Could not find contract info for chain_id {chain_id}")
        return None, None
    
def get_contract(cfg: TelliotConfig, account: ChainedAccount, name: str) -> Optional[Contract]:
    """Build Contract object from abi and address"""

    chain_id = cfg.main.chain_id
    addr, abi = get_contract_info(chain_id, name)

    if (addr is None) or (abi is None):
        logger.error(f"Could not find contract {name} on chain_id {chain_id}")
        return None
        
    
    c = Contract(addr, abi, cfg.get_endpoint(), account)

    try:
        connected_to_node = cfg.get_endpoint().connect()
    except (ValueError, ConnectionError) as e:
        logger.error(f"Could not connect to endpoint {cfg.get_endpoint()} for chain_id {chain_id}: " + str(e))
        return None
    
    if not connected_to_node:
        logger.error(f"Could not connect to endpoint {cfg.get_endpoint()} for chain_id {chain_id}: " + status.error)
        return None
    
    status = c.connect()

    if not status.ok:
        logger.error(f"Could not connect to contract {name} on chain_id {chain_id}: " + status.error)
        return None
    
    return c


def get_query_type(q: OracleQuery) -> str:
    """Get query type from class name"""
    return type(q).__name__


def mk_filter(
    from_block: int, to_block: Union[str, int], addr: str, topics: list[str]
) -> dict[str, Union[int, str, list[str]]]:
    """Create a dict with the given parameters."""
    return {
        "fromBlock": from_block,
        "toBlock": to_block,
        "address": addr,
        "topics": topics,
    }


async def log_loop(web3: Web3, addr: str, topics: list[str], wait: int) -> list[tuple[int, Any]]:
    """Generate a list of recent events from a contract."""
    # go back 20 blocks; 10 for possible reorgs, the other 10 should cover for even the fastest chains. block/sec
    # 1000 is the max number of blocks that can be queried at once
    blocks = min(20 * (wait / WAIT_PERIOD), 1000)
    try:
        block_number = web3.eth.get_block_number()
    except Exception as e:
        if "server rejected" in str(e):
            logger.info("Attempted to connect to deprecated infura network. Please check configs!" + str(e))
        else:
            logger.warning("unable to retrieve latest block number:" + str(e))
        return []

    event_filter = mk_filter(block_number - int(blocks), "latest", addr, topics)

    try:
        events = web3.eth.get_logs(event_filter)  # type: ignore
    except Exception as e:
        msg = str(e)
        if "unknown block" in msg:
            logger.error("waiting for new blocks")
        elif "request failed or timed out" in msg:
            logger.error("request for eth event logs failed")
        elif "Too Many Requests" in msg:
            logger.info(f"Too many requests to node on chain_id {web3.eth.chain_id}")
        else:
            logger.error("unknown RPC error gathering eth event logs \n" + msg)
        return []

    unique_events_list = []
    for event in events:
        if (web3.eth.chain_id, event) not in unique_events_list:
            unique_events_list.append((web3.eth.chain_id, event))

    return unique_events_list


async def chain_events(
    cfg: TelliotConfig, chain_addy: dict[int, str], topics: list[list[str]], wait: int
) -> List[List[tuple[int, Any]]]:
    """"""
    events_loop = []
    for topic in topics:
        for chain_id, address in chain_addy.items():
            try:
                endpoint = cfg.endpoints.find(chain_id=chain_id)[0]
                if endpoint.url.endswith("{INFURA_API_KEY}"):
                    continue
                endpoint.connect()
                w3 = endpoint.web3
            except (IndexError, ValueError) as e:
                logger.error(f"Unable to connect to endpoint on chain_id {chain_id}: " + str(e))
                continue
            events_loop.append(log_loop(w3, address, topic, wait))
    events: List[List[tuple[int, Any]]] = await asyncio.gather(*events_loop)

    return events


async def get_events(
    cfg: TelliotConfig, contract_name: str, topics: list[str], wait: int
) -> List[List[tuple[int, Any]]]:
    """Get all events from all live Tellor networks"""

    log_loops = []

    for endpoint in cfg.endpoints.endpoints:
        if endpoint.url.endswith("{INFURA_API_KEY}"):
            continue
        try:
            endpoint.connect()
        except Exception as e:
            logger.warning("unable to connect to endpoint: " + str(e))

        w3 = endpoint.web3

        if not w3:
            continue

        addr, _ = get_contract_info(endpoint.chain_id, contract_name)

        if not addr:
            continue

        log_loops.append(log_loop(w3, addr, topics, wait))

    events_lists: List[List[tuple[int, Any]]] = await asyncio.gather(*log_loops)

    return events_lists


def get_query_from_data(query_data: bytes) -> Optional[Union[AbiQuery, JsonQuery]]:
    for q_type in (JsonQuery, AbiQuery):
        try:
            return q_type.get_query_from_data(query_data)
        except ValueError:
            pass
    return None


async def parse_new_report_event(
    cfg: TelliotConfig,
    log: LogReceipt,
    monitored_feeds: List[MonitoredFeed],
    see_all_values: bool = False,
) -> Optional[NewReport]:
    """Parse a NewReport event."""

    q_ids_to_monitored_feeds = {"0x" + monitored_feed.feed.query.query_id.hex(): monitored_feed for monitored_feed in monitored_feeds}

    chain_id = cfg.main.chain_id
    endpoint = cfg.endpoints.find(chain_id=chain_id)[0]

    new_report = NewReport()

    if not endpoint:
        logger.error(f"Unable to find a suitable endpoint for chain_id {chain_id}")
        return None
    else:

        try:
            endpoint.connect()
            w3 = endpoint.web3
        except ValueError as e:
            logger.error(f"Unable to connect to endpoint on chain_id {chain_id}: " + str(e))
            return None

        codec = w3.codec
        event_data = get_event_data(codec, NEW_REPORT_ABI, log)

    q = get_query_from_data(event_data.args._queryData)

    if q is None:
        logger.error("Unable to form query from query data")
        return None

    new_report.tx_hash = event_data.transactionHash.hex()
    new_report.chain_id = endpoint.web3.eth.chain_id
    new_report.query_id = "0x" + event_data.args._queryId.hex()
    new_report.query_type = get_query_type(q)
    new_report.value = q.value_type.decode(event_data.args._value)
    new_report.link = get_tx_explorer_url(tx_hash=new_report.tx_hash, cfg=cfg)
    new_report.submission_timestamp = event_data.args._time # in unix time

    if new_report.query_type in ALWAYS_ALERT_QUERY_TYPES:
        new_report.status_str = "❗❗❗❗ VERY IMPORTANT DATA SUBMISSION ❗❗❗❗"
        return new_report
    
    if new_report.query_id not in q_ids_to_monitored_feeds: #TODO ensure both has 0x or none have 0x
        logger.info("skipping undesired NewReport event")
        return None
    else:
        monitored_feed = q_ids_to_monitored_feeds[new_report.query_id]

    if isinstance(q, SpotPrice):
        new_report.asset = q.asset.upper()
        new_report.currency = q.currency.upper()
    else:
        logger.error("unsupported query type")
        return None

    disputable = await monitored_feed.is_disputable(new_report.value)
    if disputable is None:

        if see_all_values:

            new_report.status_str = disputable_str(disputable, new_report.query_id)
            new_report.disputable = disputable

            return new_report
        else:
            logger.info("unable to check disputability")
            return None
    else:
        new_report.status_str = disputable_str(disputable, new_report.query_id)
        new_report.disputable = disputable

        return new_report