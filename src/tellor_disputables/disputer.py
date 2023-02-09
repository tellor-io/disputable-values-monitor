"""Utilities for the auto-disputer on Tellor on any EVM network"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Optional

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

        if self.type == ThresholdType.Equality:
            if self.amount != 0:
                logging.warn("Equality threshold selected, ignoring amount")
                self.amount = None

        if self.type != ThresholdType.Equality:
            if self.amount is None:
                raise ValueError(f"{self.type} threshold selected, amount cannot be None")
            if self.amount < 0:
                raise ValueError(f"{self.type} threshold selected, amount cannot be negative")

@dataclass
class MonitoredFeed:
    feed: DataFeed
    threshold: Threshold

    async def is_disputable(
        reported_val: Union[str, bytes, float, int], current_feed: DataFeed[Any], conf_threshold: float = 0.05
    ) -> Optional[bool]:
        """Check if the reported value is disputable."""
        if reported_val is None:
            logging.error("Need reported value to check disputability")
            return None

        trusted_val, _ = await general_fetch_new_datapoint(current_feed)
        if trusted_val is not None:

            if isinstance(trusted_val, (float, int)) and isinstance(reported_val, (float, int)):
                percent_diff: float = (reported_val - trusted_val) / trusted_val
                return float(abs(percent_diff)) > conf_threshold
            elif isinstance(trusted_val, (str, bytes)) and isinstance(reported_val, (str, bytes)):
                return trusted_val == reported_val
            else:
                logging.error("Reported value is an unsupported data type")
                return None
        else:
            logging.error("Unable to fetch new datapoint from feed")
            return None
