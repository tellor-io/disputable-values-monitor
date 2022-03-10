from dataclasses import dataclass
import json
import uuid
import random
from web3 import Web3
import os
from telliot_core.directory import contract_directory
import asyncio



def get_infura_node_url(chain_id: int) -> str:
    urls = {
        1: "https://mainnet.infura.io/v3/",
        4: "https://rinkeby.infura.io/v3/",
        137: "https://polygon-mainnet.infura.io/v3/",
        80001: "https://polygon-mumbai.infura.io/v3/",
    }
    return f'{urls[chain_id]}{os.environ.get("INFURA_API_KEY")}'


def get_contract_info(chain_id):
    name = "tellorx-oracle" if chain_id in (1, 4) else "tellorflex-oracle"
    contract_info = contract_directory.find(chain_id=chain_id, name=name)[0]
    addr = contract_info.address[chain_id]
    abi = contract_info.get_abi(chain_id=chain_id)
    return addr, abi

def get_contract(chain_id: int):
    node_url = get_infura_node_url(chain_id)
    web3 = Web3(Web3.HTTPProvider(node_url))
    addr, abi = get_contract_info(chain_id)

    return web3.eth.contract(
        address=addr,
        abi=abi,
    )


# define function to handle events and print to the console
def handle_event(event):
    print(Web3.toJSON(event))
    # print(event)
    # and whatever


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "PairCreated" event
# this loop runs on a poll interval
async def eth_log_loop(event_filter, poll_interval):
    while True:
        for new_report in event_filter.get_new_entries():
            handle_event(new_report)
        await asyncio.sleep(poll_interval)


async def poly_log_loop(event_filter, poll_interval, chain_id, loop_name):
    node_url = get_infura_node_url(chain_id)
    web3 = Web3(Web3.HTTPProvider(node_url))

    addr, _ = get_contract_info(chain_id)

    while True:
        num = web3.eth.get_block_number()
        events = web3.eth.get_logs({
            'fromBlock':num,
            'toBlock': num+100,
            'address':addr
        })

        unique_events = {}
        for event in events:
            txhash = event["transactionHash"]
            if txhash not in unique_events:
                unique_events[txhash] = event
                print('LOOP NAME:', loop_name)
                handle_event(event)

        await asyncio.sleep(poll_interval)


def get_new_reports():
    pass


def get_value_by_query_id(query_id):
    pass


# def is_disputable(reported_val, trusted_val, conf_threshold):
def is_disputable(val: float, query_data: str):
    return random.random() > .995


@dataclass
class NewReport:
    # NewReport (bytes32 _queryId, uint256 _time, bytes _value, uint256 _reward, uint256 _nonce, bytes _queryData, address _reporter)
    transaction_hash: str
    value: float
    chain_id: int 
    query_type: str 


def get_new_report(event_json: str):
    event = json.loads(event_json)
    event = {
        "txhash": uuid.uuid4().hex,
        "value": f"${round(random.uniform(2000, 3500), 2)}",
        "chain_id": random.choice([1, 137]),
        "query_type": "SpotPrice"
    }
    return NewReport(
        event["txhash"],
        event["value"],
        event["chain_id"],
        query_type=event["query_type"],
    )

def create_eth_event_filter(chain_id):
    contract = get_contract(chain_id=chain_id)
    return contract.events.NewReport.createFilter(fromBlock='latest')

def create_polygon_event_filter(chain_id):
    return None


# when main is called
# create a filter for the latest block and look for the "PairCreated" event for the uniswap factory contract
# run an async loop
# try to run the log_loop function above every 2 seconds
def main():
    eth_mainnet_filter = create_eth_event_filter(1)
    eth_testnet_filter = create_eth_event_filter(4)
    polygon_mainnet_filter = create_polygon_event_filter(137)
    polygon_testnet_filter = create_polygon_event_filter(80001)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                eth_log_loop(eth_mainnet_filter, 2),
                eth_log_loop(eth_testnet_filter, 2),
                poly_log_loop(polygon_mainnet_filter, 2, 137, "tammy"),
                poly_log_loop(polygon_testnet_filter, 2, 80001, "bob"),
            ))
    finally:
        # close loop to free up system resources
        loop.close()


if __name__ == "__main__":
    main()