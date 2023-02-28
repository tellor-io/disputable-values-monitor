"""Utilities for the auto-disputer on Tellor on any EVM network"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any
from typing import Optional
from typing import Union

from telliot_core.model.base import Base

from telliot_feeds.datafeed import DataFeed


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
            logging.warning("Equality threshold selected, ignoring amount")
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
    query_id: str

    async def is_disputable(
        self,
        reported_val: Union[str, bytes, float, int, None],
    ) -> Optional[bool]:
        """Check if the reported value is disputable."""
        if reported_val is None:
            logging.error("Need reported value to check disputability")
            return None

        trusted_val, _ = await general_fetch_new_datapoint(self.feed)
        if isinstance(trusted_val, (str, int, float, bytes)):

            if self.threshold.metric == Metrics.Percentage:

                if isinstance(trusted_val, (str, bytes)) or isinstance(reported_val, (str, bytes)):
                    logging.error("Cannot evaluate percent difference on text/addresses/bytes")
                    return None
                if self.threshold.amount is None:
                    logging.error("Please set a threshold amount to measure percent difference")
                    return None
                percent_diff: float = (reported_val - trusted_val) / trusted_val
                return float(abs(percent_diff)) >= self.threshold.amount

            elif self.threshold.metric == Metrics.Range:

                if isinstance(trusted_val, (str, bytes)) or isinstance(reported_val, (str, bytes)):
                    logging.error("Cannot evaluate range on text/addresses/bytes")

                if self.threshold.amount is None:
                    logging.error("Please set a threshold amount to measure range")
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
                logging.error("Attemping comparison with unknown threshold metric")
                return None
        else:
            logging.error("Unable to fetch new datapoint from feed")
            return None


async def general_fetch_new_datapoint(feed: DataFeed) -> Optional[Any]:
    """Fetch a new datapoint from a datafeed."""
    return await feed.source.fetch_new_datapoint()
