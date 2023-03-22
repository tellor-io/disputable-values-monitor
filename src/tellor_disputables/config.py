"""contains AutoDisputerConfig class for adjusting the settings of the auto-disputer"""
import logging
from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Optional

import yaml
from box import Box
from telliot_feeds.feeds import DataFeed

from tellor_disputables import DATAFEED_LOOKUP
from tellor_disputables.data import Metrics
from tellor_disputables.data import MonitoredFeed
from tellor_disputables.data import Threshold


@dataclass
class AutoDisputerConfig:

    monitored_feeds: Optional[List[MonitoredFeed]]

    def __init__(self) -> None:

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
        then selects the matching DataFeed from tellor_disputables.DATAFEED_LOOKUP
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
                    query_id = self.box.feeds[i].query_id[2:]
                except AttributeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None

                datafeed: DataFeed[Any] = DATAFEED_LOOKUP[query_id]
            except KeyError:
                logging.error(f"No corresponding datafeed found for query id: {query_id}\n")
                return None

            try:
                # parse query type from YAML
                try:
                    threshold_type = self.box.feeds[i].threshold.type
                    threshold_amount = self.box.feeds[i].threshold.amount
                except AttributeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None
                except TypeError as e:
                    logging.error(f"Python Box attribute error: {e}")
                    return None

                threshold: Threshold = Threshold(Metrics[threshold_type], amount=threshold_amount)
            except KeyError:
                logging.error(f"Unsupported threshold: {threshold}\n")
                return None

            monitored_feeds.append(MonitoredFeed(datafeed, threshold, query_id))

        return monitored_feeds


if __name__ == "__main__":

    print(AutoDisputerConfig())
