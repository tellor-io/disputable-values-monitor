"""test AutoDisputerConfig"""

from unittest import mock
from tellor_disputables.config import AutoDisputerConfig
from tellor_disputables.data import Metrics

def test_build_single_feed_from_yaml():
    """test building an AutoDisputerConfig from a yaml file describing a single MonitoredFeed"""

    yaml_content =  \
    """
    feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types for examples of QueryTypes w/ Query Parameters
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type: Percentage
        amount: 0.95 # 75%
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig()
    
    assert isinstance(auto_disp_cfg, AutoDisputerConfig)
    assert len(auto_disp_cfg.monitored_feeds) == 1
    assert auto_disp_cfg.box.feeds
    assert auto_disp_cfg.monitored_feeds[0].threshold.amount == 0.95
    assert auto_disp_cfg.monitored_feeds[0].threshold.metric == Metrics.Percentage

def test_build_multiple_feeds_from_yaml():
    """test building an AutoDisputerConfig from a yaml file describing multiple MonitoredFeeds"""

    yaml_content =  \
    """
    feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types for examples of QueryTypes w/ Query Parameters
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type: Percentage
        amount: 0.95 # 75%
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type: Range
        amount: 200
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig()
    
    assert isinstance(auto_disp_cfg, AutoDisputerConfig)
    assert len(auto_disp_cfg.monitored_feeds) == 2
    assert auto_disp_cfg.box.feeds
    assert auto_disp_cfg.monitored_feeds[0].threshold.amount == 0.95
    assert auto_disp_cfg.monitored_feeds[0].threshold.metric == Metrics.Percentage
    assert auto_disp_cfg.monitored_feeds[1].threshold.amount == 200
    assert auto_disp_cfg.monitored_feeds[1].threshold.metric == Metrics.Range


def test_invalid_yaml_config():
    """test that an invalid yaml file does not become an AutoDisputerConfig object"""
    
    yaml_content =  \
    """
    feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types for examples of QueryTypes w/ Query Parameters
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type: Percentage
        amount: 0.95 # 75%
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type____: Range
        amount&: 200
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig()


    assert not auto_disp_cfg.monitored_feeds