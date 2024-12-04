"""test AutoDisputerConfig"""
from unittest import mock

from telliot_feeds.feeds import evm_call_feed

from disputable_values_monitor.config import AutoDisputerConfig
from disputable_values_monitor.data import Metrics
from disputable_values_monitor.data import MonitoredFeed
from disputable_values_monitor.data import Thresholds


def test_build_single_feed_from_yaml():
    """test building an AutoDisputerConfig from a yaml file describing a single MonitoredFeed"""

    yaml_content = """
    feeds:
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      thresholds:
        type: Percentage
        alrt_amount: 0.15
        disp_amount: 0.95
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)
    print(f"auto_disp_cfg = {auto_disp_cfg}")
    assert isinstance(auto_disp_cfg, AutoDisputerConfig)
    assert len(auto_disp_cfg.monitored_feeds) == 1
    assert auto_disp_cfg.box.feeds
    assert auto_disp_cfg.monitored_feeds[0].thresholds.alrt_amount == 0.15
    assert auto_disp_cfg.monitored_feeds[0].thresholds.disp_amount == 0.95
    assert auto_disp_cfg.monitored_feeds[0].thresholds.metric == Metrics.Percentage


def test_build_multiple_feeds_from_yaml():
    """test building an AutoDisputerConfig from a yaml file describing multiple MonitoredFeeds"""

    yaml_content = """
    feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      thresholds:
        type: Percentage
        alrt_amount: 0.15 # 95%
        disp_amount: 0.95 # 95%
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      thresholds:
        type: Range
        alrt_amount: 20
        disp_amount: 200
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    assert isinstance(auto_disp_cfg, AutoDisputerConfig)
    assert len(auto_disp_cfg.monitored_feeds) == 2
    assert auto_disp_cfg.box.feeds
    assert auto_disp_cfg.monitored_feeds[0].thresholds.alrt_amount == 0.15
    assert auto_disp_cfg.monitored_feeds[0].thresholds.disp_amount == 0.95
    assert auto_disp_cfg.monitored_feeds[0].thresholds.metric == Metrics.Percentage
    assert auto_disp_cfg.monitored_feeds[1].thresholds.alrt_amount == 20
    assert auto_disp_cfg.monitored_feeds[1].thresholds.disp_amount == 200
    assert auto_disp_cfg.monitored_feeds[1].thresholds.metric == Metrics.Range


def test_invalid_yaml_config():
    """test that an invalid yaml file does not become an AutoDisputerConfig object"""

    yaml_content = """
    feeds:
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      thresholds:
        type: Percentage
        alrt_amount: 0.15
        disp_amount: 0.95
    - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
      threshold:
        type____: Range
        alrt_amount: 20
        disp_amount&: 200
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    assert not auto_disp_cfg.monitored_feeds


def test_form_evm_call_feed_from_yaml():
    """test building EVMCall source without parameters from config"""

    yaml_content = """
    feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types
    - query_type: "EVMCall"
      thresholds:
        type: Equality
    """

    with mock.patch("builtins.open", mock.mock_open(read_data=yaml_content)):
        auto_disp_cfg = AutoDisputerConfig(is_disputing=True, confidence_threshold=None)

    assert auto_disp_cfg.monitored_feeds

    thresholds = Thresholds(Metrics.Equality, alrt_amount=None, disp_amount=None)
    assert auto_disp_cfg.monitored_feeds[0] == MonitoredFeed(evm_call_feed, thresholds)
