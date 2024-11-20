"""contains AutoDisputerConfig class for adjusting the settings of the auto-disputer"""
import logging
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional

import yaml
from box import Box
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.queries.query_catalog import query_catalog

from disputable_values_monitor.data import AlertThreshold
from disputable_values_monitor.data import DisputeThreshold
from disputable_values_monitor.data import Metrics
from disputable_values_monitor.data import MonitoredFeed
from disputable_values_monitor.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AutoDisputerConfig:

    monitored_feeds: Optional[List[MonitoredFeed]]

    def __init__(self, is_disputing: bool, is_alerting: bool, confidence_flag: float) -> None:
        self.confidence = None if is_disputing or is_alerting else confidence_flag

        try:
            with open("disputer-config.yaml", "r") as f:
                self.box = Box(yaml.safe_load(f))
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
            logging.error(f"YAML file error: {e}")
            return
        except AttributeError as e:
            logging.error(f"Python Box object error: {e}")
            return
        except KeyError as e:
            logging.error(f"Dictionary-style indexing error: {e}")
            return

        self.monitored_feeds = self.build_monitored_feeds_from_yaml()

    def build_monitored_feeds_from_yaml(self) -> Optional[List[MonitoredFeed]]:
        """
        Build a List[MonitoredFeed] from YAML input

        For each query id in the disputer-config.yaml...

        This function reads the selected query Ids from disputer-config.yaml,
        then selects the matching DataFeed from telliot_feeds.query_catalog
        dict.

        It also reads the query Id's selected threshold from disputer-config.yaml
        then creates a Threshold object representing the treshold.

        Returns: List[MonitoredFeed]

        """

        monitored_feeds = []

        for i in range(len(self.box.feeds)):
            try:
                # parse query type from YAML
                try:
                    if hasattr(self.box.feeds[i], "query_id"):
                        query_id = self.box.feeds[i].query_id[2:]
                        catalog_entry = query_catalog.find(query_id=query_id)
                        if not catalog_entry:
                            logger.error(f"No corresponding datafeed found for query id: {query_id}")
                            return None
                        # if catalog entry exists for query id, feed exists
                        datafeed: DataFeed[Any] = CATALOG_FEEDS.get(catalog_entry[0].tag)
                    elif hasattr(self.box.feeds[i], "query_type"):
                        query_type = self.box.feeds[i].query_type
                        datafeed = DATAFEED_BUILDER_MAPPING[query_type]
                    else:
                        logger.error("Invalid query id or query type provided in disputer-config.yaml")
                except AttributeError as e:
                    logger.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logger.error(f"Python Box type error: {e}")
                    return None

            except KeyError:
                logger.error(f"No corresponding datafeed found for query id: {query_id}\n")
                return None

            try:
                # parse disputer type and threshold
                try:
                    disp_threshold_type = self.box.feeds[i].disp_threshold.type
                    if disp_threshold_type.lower() == "equality":
                        disp_threshold_amount = None
                    else:
                        disp_threshold_type = (
                            self.box.feeds[i].disp_threshold.amount if self.confidence is None else self.confidence
                        )
                except AttributeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None

                disp_threshold: DisputeThreshold = DisputeThreshold(
                    Metrics[disp_threshold_type], amount=disp_threshold_amount
                )
            except KeyError:
                logging.error("Unsupported dispute threshold. \n")
                return None

            try:
                # parse alerter type and threshold
                try:
                    alrt_threshold_type = self.box.feeds[i].alrt_threshold.type
                    if alrt_threshold_type.lower() == "equality":
                        alrt_threshold_amount = None
                    else:
                        alrt_threshold_type = (
                            self.box.feeds[i].alrt_threshold.amount if self.confidence is None else self.confidence
                        )
                except AttributeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None

                alrt_threshold: AlertThreshold = AlertThreshold(
                    Metrics[alrt_threshold_type], amount=alrt_threshold_amount
                )
            except KeyError:
                logging.error("Unsupported alert threshold. \n")
                return None

            monitored_feeds.append(MonitoredFeed(datafeed, disp_threshold, alrt_threshold))

        return monitored_feeds


if __name__ == "__main__":

    print(AutoDisputerConfig(is_disputing=True, is_alerting=True, confidence_flag=0.1))
