
import pytest

from tellor_disputables.disputer import Metrics, Threshold


def test_setting_invalid_metric():
    """test setting Threshold.metric to something other than Metrics enum"""

    thres = Threshold(metric=Metrics.Equality, amount=0)

    msg = "metric must be of enum Metrics: Percentage, Equality, or Range"
    with pytest.raises(ValueError) as err:
        thres.metric = 42

    assert str(err.value) == msg

    with pytest.raises(ValueError) as err:
        thres.metric = "threshold metric cannot be a string"

    assert msg in str(err.value)



def test_safety_checks_in_constructor():
    """test safe value checks in constructor"""

    #log message when metric is set to "equality"

    #raise value error if metric is not "equality" and amount is None
    msg = "threshold selected, amount cannot be None"
    with pytest.raises(ValueError) as err:
        _ = Threshold(Metrics.Percentage, None)

    assert msg in str(err.value)
    

    #raise value error if metric is not "equality" and amount is negative
    msg = "threshold selected, amount cannot be negative"
    with pytest.raises(ValueError) as err:
        _ = Threshold(Metrics.Range, -10)

    assert msg in str(err.value)

"""test safe value checks in attribute setters"""

"""test reported value is None should return None"""

"""test is disputable returns None if can't retrieve value"""

"""test return type of metrics"""

"""test example percentage on ETH/USD"""

"""test example range on SHIB/USD"""

"""test example equality on TellorOracleAddress type"""


@pytest.mark.asyncio
async def test_is_disputable(caplog):
    """test check for disputability for a float value"""
    val = 1000.0
    threshold = 0.05

    # ETH/USD
    current_feed = eth_usd_median_feed

    # Is disputable
    disputable = await is_disputable(val, current_feed, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    # No reported value
    disputable = await is_disputable(reported_val=None, current_feed=current_feed, conf_threshold=threshold)
    assert disputable is None
    assert "Need reported value to check disputability" in caplog.text

    # Unable to fetch price
    with patch("tellor_disputables.data.general_fetch_new_datapoint", return_value=(None, None)):
        disputable = await is_disputable(val, current_feed, threshold)
        assert disputable is None
        assert "Unable to fetch new datapoint from feed" in caplog.text


@pytest.mark.asyncio
async def test_different_conf_thresholds():
    """test if a value is dispuable under different confindence thresholds"""

    # ETH/USD
    feed = eth_usd_median_feed
    val = 666
    threshold = 0.05

    # Is disputable
    disputable = await is_disputable(val, feed, threshold)
    assert isinstance(disputable, bool)
    assert disputable

    threshold = 0.99
    # Is now not disputable
    disputable = await is_disputable(val, feed, threshold)
    assert isinstance(disputable, bool)
    assert not disputable