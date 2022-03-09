from dataclasses import dataclass
import json
import uuid
import random


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