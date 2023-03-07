"""test AutoDisputerConfig"""

from unittest import mock
from tellor_disputables.config import AutoDisputerConfig
from tellor_disputables.data import Metrics

def test_build_feeds_from_yaml():

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
    assert auto_disp_cfg.monitored_feeds
    assert auto_disp_cfg.box.feeds
    assert auto_disp_cfg.monitored_feeds[0].threshold.amount == 0.95
    assert auto_disp_cfg.monitored_feeds[0].threshold.metric == Metrics.Percentage