"""Tests for eth_getLogs block-range chunking."""
import asyncio
from typing import Any
from typing import Dict
from typing import List

import pytest

from disputable_values_monitor.data import get_logs_chunked
from disputable_values_monitor.data import log_loop
from disputable_values_monitor.data import start_block


ADDR = "0x88dF592F8eb5D7Bd38bFeF7dEb0fBc02cf3778a0"
TOPICS = ["0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"]


class FakeEth:
    def __init__(self, max_range: int, block_number: int = 0) -> None:
        self.max_range = max_range
        self.block_number = block_number
        self.calls: List[Dict[str, Any]] = []

    def get_block_number(self) -> int:
        return self.block_number

    def get_logs(self, event_filter: Dict[str, Any]) -> List[Dict[str, int]]:
        self.calls.append(event_filter)
        from_block = event_filter["fromBlock"]
        to_block = event_filter["toBlock"]
        span = to_block - from_block + 1
        if span > self.max_range:
            raise Exception(
                "{'code': -32602, 'message': "
                f"'query block range exceeds server limit, narrow your filter: {self.max_range}'}}"
            )
        return [{"from": from_block, "to": to_block}]


class FakeWeb3:
    def __init__(self, max_range: int) -> None:
        self.eth = FakeEth(max_range)


@pytest.fixture(autouse=True)
def _clear_log_cursor() -> None:
    start_block.clear()
    yield
    start_block.clear()


def test_get_logs_chunked_splits_over_rpc_limit() -> None:
    web3 = FakeWeb3(max_range=1000)
    events = get_logs_chunked(web3, from_block=1, to_block=2500, addr=ADDR, topics=TOPICS)

    assert [c["fromBlock"] for c in web3.eth.calls] == [1, 1001, 2001]
    assert [c["toBlock"] for c in web3.eth.calls] == [1000, 2000, 2500]
    assert len(events) == 3


def test_get_logs_chunked_shrinks_when_limit_is_tighter_than_default() -> None:
    web3 = FakeWeb3(max_range=500)
    events = get_logs_chunked(
        web3, from_block=1, to_block=1200, addr=ADDR, topics=TOPICS, max_range=1000
    )

    spans = [c["toBlock"] - c["fromBlock"] + 1 for c in web3.eth.calls]
    assert spans[0] == 1000  # first attempt uses the default window and is rejected
    assert all(span <= 500 for span in spans[1:])
    assert events
    assert web3.eth.calls[-1]["toBlock"] == 1200


def test_log_loop_chunks_large_initial_offset() -> None:
    web3 = FakeWeb3(max_range=1000)
    web3.eth.block_number = 5000
    events = asyncio.run(log_loop(web3, 1, ADDR, TOPICS, 4000))

    assert events
    assert all(c["toBlock"] - c["fromBlock"] + 1 <= 1000 for c in web3.eth.calls)
    assert web3.eth.calls[0]["fromBlock"] == 990
    assert web3.eth.calls[-1]["toBlock"] == 5000


def test_get_logs_chunked_empty_when_from_after_to() -> None:
    web3 = FakeWeb3(max_range=1000)
    assert get_logs_chunked(web3, from_block=10, to_block=9, addr=ADDR, topics=TOPICS) == []
    assert web3.eth.calls == []
