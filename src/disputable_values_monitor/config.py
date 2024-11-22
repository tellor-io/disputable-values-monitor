"""contains AutoDisputerConfig class for adjusting the settings of the auto-disputer"""
import logging
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional

import click
import yaml
from box import Box
from telliot_feeds.feeds import CATALOG_FEEDS
from telliot_feeds.feeds import DataFeed
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.queries.query_catalog import query_catalog

from disputable_values_monitor.data import Metrics
from disputable_values_monitor.data import MonitoredFeed
from disputable_values_monitor.data import Threshold
from disputable_values_monitor.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AutoDisputerConfig:

    monitored_feeds: Optional[List[MonitoredFeed]]

    def __init__(self, is_disputing: bool, is_alerting: bool) -> None:
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
                # parse disputer type and alerter type and thresholds
                try:
                    threshold_type = self.box.feeds[i].threshold.type
                    if threshold_type.lower() == "equality":
                        global_alert_percentage = None
                        alrt_threshold_amount = None
                        disp_threshold_amount = None
                    else:
                        global_alert_percentage = self.box.global_alert_percentage
                        disp_threshold_amount = self.box.feeds[i].threshold.disp_amount
                        alrt_threshold_amount = self.box.feeds[i].threshold.alrt_amount
                except AttributeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None

                threshold: Threshold = Threshold(
                    Metrics.Percentage, global_alert_percentage, alrt_threshold_amount, disp_threshold_amount
                )

            except KeyError as e:
                logging.error(f"Unsupported dispute threshold:{e} \n")
                return None

            monitored_feeds.append(MonitoredFeed(datafeed, threshold))

        return monitored_feeds


if __name__ == "__main__":

    print(AutoDisputerConfig(is_disputing=False, is_alerting=False))
