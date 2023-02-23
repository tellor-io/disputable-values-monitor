import time
from unittest.mock import patch

import pytest
from telliot_feeds.feeds.eth_usd_feed import eth_usd_median_feed

from tellor_disputables.disputer import Metrics
from tellor_disputables.disputer import MonitoredFeed
from tellor_disputables.disputer import Threshold


def test_safety_checks_in_constructor(caplog):
    """test safe value checks in constructor"""

    # log message when metric is set to "equality"
    msg = "Equality threshold selected, ignoring amount"

    thres = Threshold(Metrics.Equality, 20)
    assert msg in caplog.text
    assert thres.amount is None

    # raise value error if metric is not "equality" and amount is None
    msg = "threshold selected, amount cannot be None"
    with pytest.raises(ValueError) as err:
        _ = Threshold(Metrics.Percentage, None)

    assert msg in str(err.value)

    # raise value error if metric is not "equality" and amount is negative
    msg = "threshold selected, amount cannot be negative"
    with pytest.raises(ValueError) as err:
        _ = Threshold(Metrics.Range, -10)

    assert msg in str(err.value)


@pytest.mark.asyncio
async def test_percentage():
    """test example percentage calculation"""
    reported_val = 750
    telliot_val = 1000
    percentage = 0.25
    threshold = Threshold(Metrics.Percentage, percentage)
    mf = MonitoredFeed(eth_usd_median_feed, threshold)

    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert disputable

    telliot_val = 751
    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert not disputable


@pytest.mark.asyncio
async def test_range():
    """test example range calculation"""

    reported_val = 500
    telliot_val = 1000
    range = 500
    threshold = Threshold(Metrics.Range, range)
    mf = MonitoredFeed(eth_usd_median_feed, threshold)

    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert disputable

    telliot_val = 501
    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert not disputable


@pytest.mark.asyncio
async def test_equality():
    """test example equality calculation"""

    reported_val = "0xa7654E313FbB25b2cF367730CB5c2759fAf831a1"  # checksummed
    telliot_val = "0xa7654e313fbb25b2cf367730cb5c2759faf831a1"  # not checksummed
    threshold = Threshold(Metrics.Equality, 20)  # amount will be disregarded!

    assert threshold.amount is None

    mf = MonitoredFeed(eth_usd_median_feed, threshold)

    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert not disputable

    telliot_val = 501  # throw a completely different data type at the equality operator
    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(telliot_val, time.time())):
        disputable = await mf.is_disputable(reported_val)
        assert disputable


@pytest.mark.asyncio
async def test_is_disputable(caplog):
    """test check for disputability for a float value"""
    val = 1000.0
    threshold = Threshold(metric=Metrics.Percentage, amount=0.05)

    # ETH/USD
    mf = MonitoredFeed(eth_usd_median_feed, threshold)

    # Is disputable
    disputable = await mf.is_disputable(val)
    assert isinstance(disputable, bool)
    assert disputable

    # No reported value
    disputable = await mf.is_disputable(reported_val=None)
    assert disputable is None
    assert "Need reported value to check disputability" in caplog.text

    # Unable to fetch price
    with patch("tellor_disputables.disputer.general_fetch_new_datapoint", return_value=(None, None)):
        disputable = await mf.is_disputable(val)
        assert disputable is None
        assert "Unable to fetch new datapoint from feed" in caplog.text


@pytest.mark.asyncio
async def test_different_conf_thresholds():
    """test if a value is dispuable under different confindence thresholds"""

    # ETH/USD
    threshold = Threshold(Metrics.Percentage, 0.05)
    mf = MonitoredFeed(eth_usd_median_feed, threshold)
    val = 666

    # Is disputable
    disputable = await mf.is_disputable(val)
    assert isinstance(disputable, bool)
    assert disputable

    mf.threshold.amount = 2.0
    # Is now not disputable
    disputable = await mf.is_disputable(val)
    assert isinstance(disputable, bool)
    assert not disputable
