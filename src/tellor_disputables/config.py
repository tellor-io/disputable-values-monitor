"""contains AutoDisputerConfig class for adjusting the settings of the auto-disputer"""

from dataclasses import dataclass
import logging
from telliot_feeds.feeds import DataFeed
from typing import Any, List, Optional, get_args, get_type_hints
from box import Box
from telliot_feeds.feeds import DATAFEED_BUILDER_MAPPING
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed
import yaml
from tellor_disputables.disputer import Metrics, MonitoredFeed, Threshold

default_monitored_feeds_list = [
    MonitoredFeed(
        feed=eth_usd_median_feed,
        threshold=Threshold(
            metric=Metrics.Percentage,
            amount=0.75
        )
    )
]

@dataclass
class AutoDisputerConfig:

    freshness: int
    feeds: List[MonitoredFeed]

    def __init__(self) -> None:

        try:
            with open('disputer-config.yaml', 'r') as f:
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

        self.freshness = self.box.freshness
        self.feeds = self.build_feed_from_yaml()


    def build_feed_from_yaml(self) -> Optional[DataFeed[Any]]:
        """

        
        Build a DataFeed from YAML input

        This function takes input from the user for the QueryType
        and its matching QueryParameters, the builds a DataFeed
        object if the QueryType is supported and the QueryParameters
        can be casted to their appropriate data types from the YAML reference.

        Returns: DataFeed[Any]

        """
        try:
            # parse query type from YAML
            try:
                query_type = self.box.feeds[0].QueryType #TODO loop through all instead of only 0
            except AttributeError as e:
                logging.error(f"Python Box attribute error: {e}")
                return None
            except TypeError as e:
                logging.error(f"Python Box attribute error: {e}")
                return None

            feed: DataFeed[Any] = DATAFEED_BUILDER_MAPPING[query_type]
        except KeyError:
            logging.error(f"No corresponding datafeed found for QueryType: {query_type}\n")
            return None
        for query_param in feed.query.__dict__.keys():
            # accessing the datatype
            type_hints = get_type_hints(feed.query)

            # get param type if type isn't optional
            try:
                param_dtype = get_args(type_hints[query_param])[0]  # parse out Optional type
            except IndexError:
                param_dtype = type_hints[query_param]

            # parse box for query parameter's value
            try:
                query_param_value = self.box.feeds[0][query_param] #TODO loop through all
            except AttributeError as e:
                logging.error(f"Python Box attribute error: {e}")
                return None
            except TypeError as e:
                logging.error(f"Python Box attribute error: {e}")
                return None
            if query_param_value:
                try:
                    # cast input from string to datatype of query parameter
                    if param_dtype == bytes and query_param_value.startswith("0x"):
                        query_param_value = bytes.fromhex(query_param_value[2:])
                    query_param_value = param_dtype(query_param_value)
                    setattr(feed.query, query_param, query_param_value)
                    setattr(feed.source, query_param, query_param_value)
                except ValueError:
                    logging.error(f"Value {query_param_value} for QueryParameter {query_param} does not match type {param_dtype}")
                    return None

            else:
                logging.info(f"Must set QueryParameter {query_param} of QueryType {query_type}")
                return None

        return feed


if __name__ == "__main__":
    # cf = ConfigFile(name="disputer-config", config_type=AutoDisputerConfig, config_format="yaml", config_dir=os.getcwd())

    # config_endpoints = cf.get_config()

    # print(config_endpoints)

    print(AutoDisputerConfig())

    print(AutoDisputerConfig().feeds.source)