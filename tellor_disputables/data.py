from dataclasses import dataclass
import json
import uuid
import random
from web3 import Web3
import os
from telliot_core.directory import contract_directory
import asyncio
# from web3.datastructures import AttributeDict
# from hexbytes import HexBytes
from datetime import datetime
from dateutil import tz


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


def get_web3(chain_id: int):
    node_url = get_infura_node_url(chain_id)
    return Web3(Web3.HTTPProvider(node_url))


def get_contract(web3, addr, abi):
    return web3.eth.contract(
        address=addr,
        abi=abi,
    )


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "PairCreated" event
# this loop runs on a poll interval
async def eth_log_loop(event_filter, poll_interval, chain_id):
    # while True:
    unique_events = {}
    unique_events_lis = []
    for event in event_filter.get_new_entries():
        txhash = event["transactionHash"]
        if txhash not in unique_events:
            unique_events[txhash] = event
            unique_events_lis.append((chain_id, event))
        # await asyncio.sleep(poll_interval)
    return unique_events_lis


async def poly_log_loop(web3, addr): #, event_filter, poll_interval, chain_id, loop_name):
    # while True:
    num = web3.eth.get_block_number()
    events = web3.eth.get_logs({
        'fromBlock':num,
        'toBlock': num+100,
        'address':addr
    })

    unique_events = {}
    unique_events_lis = []
    for event in events:
        txhash = event["transactionHash"]
        if txhash not in unique_events:
            unique_events[txhash] = event
            unique_events_lis.append((web3.eth.chain_id, event))
            # print('LOOP NAME:', loop_name)
            # handle_event(event)
        # await asyncio.sleep(poll_interval)
    
    return unique_events_lis


def get_new_reports():
    pass


def get_value_by_query_id(query_id):
    pass


# def is_disputable(reported_val, trusted_val, conf_threshold):
def is_disputable(val: float, query_data: str):
    # get feed based on query id
    # feed.fetch_new_datapoint
    # compare reporter_val to datpoint val
    return random.random() > .995


@dataclass
class NewReport:
    # NewReport (bytes32 _queryId, uint256 _time, bytes _value, uint256 _reward, uint256 _nonce, bytes _queryData, address _reporter)
    tx_hash: str
    eastern_time: str
    chain_id: int
    link: str
    query_type: str 
    value: float 
    


def timestamp_to_eastern(timestamp: int) -> str:
    est = tz.gettz("EST")
    dt = datetime.fromtimestamp(timestamp).astimezone(est)

    return str(dt)


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


def create_eth_event_filter(web3, addr, abi):
    contract = get_contract(web3, addr, abi)
    return contract.events.NewReport.createFilter(fromBlock='latest')


def create_polygon_event_filter(chain_id):
    return None


async def get_events(eth_web3, eth_oracle_addr, eth_abi, poly_web3, poly_oracle_addr):
    eth_mainnet_filter = create_eth_event_filter(eth_web3, eth_oracle_addr, eth_abi)
    # eth_testnet_filter = create_eth_event_filter(4)
    # polygon_mainnet_filter = create_polygon_event_filter(137)
    # polygon_testnet_filter = create_polygon_event_filter(80001)

    events_lists = await asyncio.gather(
                eth_log_loop(eth_mainnet_filter, 1, chain_id=1),
                # eth_log_loop(eth_testnet_filter, 2),
                # poly_log_loop(polygon_mainnet_filter, 2, 137, "tammy"),
                poly_log_loop(poly_web3, poly_oracle_addr),
    )
    return events_lists


def parse_new_report_event(event, web3, contract):
    # d = AttributeDict({
    #     'address': '0x41b66dd93b03e89D29114a7613A6f9f0d4F40178',
    #     'blockHash': HexBytes('0xa35a46281697bc9ddd4f19e2c2ea3d84ba2e7f9449a3aaae083e936b7f01265e'),
    #     'blockNumber': 25471196,
    #     'data': '0x000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000622b8b5400000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000590000000000000000000000000000000000000000000000000000000000000100000000000000000000000000d5f1cc896542c111c7aa7d7fae2c3d654f34b92700000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000908625e1000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000d4c6567616379526571756573740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000002',
    #     'logIndex': 103,
    #     'removed': False,
    #     'topics': [HexBytes('0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95')],
    #     'transactionHash': HexBytes('0x47b3add1a2492760675aebcf0e4c4f953265dee0fc52fd608d12e827138ff948'),
    #     'transactionIndex': 2})
    # addr, abi = get_contract_info(80001)
    # web3 = get_web3(80001)
    # contract = get_contract(web3, addr, abi)
    # x = contract.events.NewReport.processLog(d)
    tx_hash = event['transactionHash']
    receipt = web3.eth.getTransactionReceipt(tx_hash)
    receipt = contract.events.NewReport().processReceipt(receipt)
    print('RECEIPT', receipt)
    
    args = receipt[0]["args"]
    query_id = args["_queryId"]
    print('QUERY ID', query_id)
    query_id_decoded = "as;dlfkja;sdlfkj"#query_id.decode('utf8') # TODO replace with telliot_core decoder
    print('QUERY ID DECODED', query_id_decoded)
    est = timestamp_to_eastern(args["_time"])
    # value = args["_value"].decode('utf8') # TODO replace with telliot_core decoder
    value = 20.
    cid = web3.eth.chain_id
    query_type = query_id_decoded
    # TODO: return None if args['event'] != NewReport

    return NewReport(
        chain_id=cid,
        eastern_time=est,
        tx_hash=str(tx_hash),
        link="link",
        query_type=query_type,
        value=value)


def main():
    # _ = asyncio.run(get_events())
    # test_parse_new_report()
    pass


if __name__ == "__main__":
    main()