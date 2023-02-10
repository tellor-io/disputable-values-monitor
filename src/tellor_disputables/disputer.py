"""Utilities for the auto-disputer on Tellor on any EVM network"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Optional, Union

from telliot_feeds.datafeed import DataFeed

from tellor_disputables.data import general_fetch_new_datapoint


class ThresholdType(Enum):
    Percentage = "percentage"
    Equality = "equality"
    Range = "range"


@dataclass
class Threshold:
    """
    A Threshold for sending a dispute.

    amount (Optional[int]) -- amount of tolerated difference between
    submitted on-chain values and trusted values from telliot.

    If self.type == "percentage", amount is a percent with a minimum of 0
    If self.type == "equality", amount is None
    If self.type == "range", amount is the maximum distance an on-chain value can have from 
    the trusted value from telliot
    """
    type: ThresholdType
    amount: Optional[int]

    def __post_init__(self) -> None:

        self.safe_value_checks()
    
    def __setattr__(self, __name: str, __value: Union[ThresholdType, int, None]) -> None:

        if (__name == "type") and (not isinstance(__value, ThresholdType)):
            raise ValueError("type must be of enum ThresholdType: Percentage, Equality, or Range")

        self.safe_value_checks()

    def safe_value_checks(self):
        if self.type == ThresholdType.Equality:
            logging.warn("Equality threshold selected, ignoring amount")
            self.amount = None

        if self.type != ThresholdType.Equality:
            if self.amount is None:
                raise ValueError(f"{self.type} threshold selected, amount cannot be None")
            if self.amount < 0:
                raise ValueError(f"{self.type} threshold selected, amount cannot be negative")

@dataclass
class MonitoredFeed:
    feed: DataFeed[Any]
    threshold: Threshold

    async def is_disputable(
        self, reported_val: Union[str, bytes, float, int],
    ) -> Optional[bool]:
        """Check if the reported value is disputable."""
        if reported_val is None:
            logging.error("Need reported value to check disputability")
            return None

        trusted_val, _ = await general_fetch_new_datapoint(self.feed)
        if trusted_val is not None:

            if self.threshold.type == ThresholdType.Percentage:
                percent_diff: float = (reported_val - trusted_val) / trusted_val
                return float(abs(percent_diff)) > self.threshold.amount

            elif self.threshold.type == ThresholdType.Range:
                range_: float = reported_val - trusted_val
                return range_ > self.threshold.amount

            elif self.threshold.type == ThresholdType.Equality:
                return trusted_val == reported_val

            else:
                logging.error("Reported value is an unsupported data type")
                return None
        else:
            logging.error("Unable to fetch new datapoint from feed")
            return None
