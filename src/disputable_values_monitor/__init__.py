"""Disputable Values Monitor - CLI dashboard & alerts for potential
bad values reported to Tellor oracles."""
from hexbytes import HexBytes
from web3.datastructures import AttributeDict

WAIT_PERIOD = 7  # seconds between checks for new events

ALWAYS_ALERT_QUERY_TYPES = ("AutopayAddresses", "TellorOracleAddress")


# https://goerli.etherscan.io/tx/0x3cb2ac6017b9c2282aba271ac658c55db428edcdd391df646a1928bbe28dd9bd
EXAMPLE_NEW_REPORT_EVENT = AttributeDict(
    {
        "address": "0xf3fa4536396a486c0490ea506dd4630f73d1ab9d",
        "blockHash": HexBytes("0xa9298605ae7fa6cb33700eb0e005a72217dd6a2d06db0ce365764fae4ec5493c"),
        "blockNumber": 7798200,
        "logIndex": 101,
        "removed": False,
        "topics": [HexBytes("0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95")],
        "transactionHash": HexBytes("0x3cb2ac6017b9c2282aba271ac658c55db428edcdd391df646a1928bbe28dd9bd"),
        "transactionIndex": 1,
    }
)

# OHM/ETH SpotPrice
EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT = (
    AttributeDict(
        {
            "args": AttributeDict(
                {
                    "_queryId": b"\xeeO\xcd\xee\xd7s\x93\x1a\xf0\xbc\xd1l\xfc"
                    b"\xea[6f\x82\xff\xbdI\x94\xcfx\xb4\xf0\xa6\xa4\x0bW\x03@",
                    "_time": 1647451884,
                    "_value": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$\x8c7\xb2\x0e\xfb\xff",
                    "_nonce": 58,
                    "_queryData": b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03ohm\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03eth\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
                    "_reporter": "0xd5f1Cc896542C111c7Aa7D7fae2C3D654f34b927",
                }
            ),
            "event": "NewReport",
            "logIndex": 101,
            "transactionIndex": 1,
            "transactionHash": HexBytes("0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4"),
            "address": "0x41b66dd93b03e89D29114a7613A6f9f0d4F40178",
            "blockHash": HexBytes("0x61967b410ac2ef5352e1bc0c06ab63fb84ba9161276a4645aca389fd01409ef7"),
            "blockNumber": 25541322,
        }
    ),
)


LEGACY_ASSETS = {
    1: "ETH",
    2: "BTC",
    10: "AMPL",
    50: "TRB",
    59: "ETH",
}


LEGACY_CURRENCIES = {
    1: "USD",
    2: "USD",
    10: "USD",
    50: "USD",
    59: "JPY",
}

NEW_REPORT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "internalType": "bytes32", "name": "_queryId", "type": "bytes32"},
        {"indexed": True, "internalType": "uint256", "name": "_time", "type": "uint256"},
        {"indexed": False, "internalType": "bytes", "name": "_value", "type": "bytes"},
        {"indexed": False, "internalType": "uint256", "name": "_nonce", "type": "uint256"},
        {"indexed": False, "internalType": "bytes", "name": "_queryData", "type": "bytes"},
        {"indexed": True, "internalType": "address", "name": "_reporter", "type": "address"},
    ],
    "name": "NewReport",
    "type": "event",
}
