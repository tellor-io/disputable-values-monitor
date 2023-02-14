"""Tellor Disputables - CLI dashboard & alerts for potential
bad values reported to Tellor oracles."""
from hexbytes import HexBytes
from telliot_feeds import feeds
from web3.datastructures import AttributeDict

WAIT_PERIOD = 7  # seconds between checks for new events

ALWAYS_ALERT_QUERY_TYPES = ("AutopayAddresses", "TellorOracleAddress")

DATAFEED_LOOKUP = {
    "0d12ad49193163bbbeff4e6db8294ced23ff8605359fd666799d4e25a3aa0e3a": feeds.ampl_usd_vwap_feed,
    "35e083af947a4cf3bc053440c3b4f753433c76acab6c8b1911ee808104b72e85": feeds.bct_usd_feed.bct_usd_median_feed,
    "a6f013ee236804827b77696d350e9f0ac3e879328f2a3021d473a0b778ad78ac": feeds.btc_usd_feed.btc_usd_median_feed,
    "d913406746edf7891a09ffb9b26a12553bbf4d25ecf8e530ec359969fe6a7a9c": feeds.dai_usd_feed.dai_usd_median_feed,
    "ba3452d8acca69e530308515f4a0cb01da604dd077801db619800e7d3a7b5f8c": feeds.eth_jpy_feed.eth_jpy_median_feed,
    "83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992": feeds.eth_usd_feed.eth_usd_median_feed,
    "7239909c0aa5d3e89efb2dce06c80811e93ab18413110b8c0435ee32c52cc4fb": feeds.idle_usd_feed.idle_usd_median_feed,
    "40aa71e5205fdc7bdb7d65f7ae41daca3820c5d3a8f62357a99eda3aa27244a3": feeds.matic_usd_feed.matic_usd_median_feed,
    "b9d5e25dabd5f0a48f45f5b6b524bac100df05eaf5311f3e5339ac7c3dd0a37e": feeds.mkr_usd_feed.mkr_usd_median_feed,
    "ee4fcdeed773931af0bcd16cfcea5b366682ffbd4994cf78b4f0a6a40b570340": feeds.olympus.ohm_eth_median_feed,
    "5c13cd9c97dbb98f2429c101a2a8150e6c7a0ddaff6124ee176a3a411067ded0": feeds.trb_usd_feed.trb_usd_median_feed,
    "612ec1d9cee860bb87deb6370ed0ae43345c9302c085c1dfc4c207cbec2970d7": feeds.uspce_feed,
    "2e0aa9e19f5c3e1d3e086b34fe90072b43889382f563e484e8e1e3588b19ef14": feeds.eur_usd_feed.eur_usd_median_feed,
    "8ee44cd434ed5b0e007eee581fbe0855336f3f84484e8d9989a620a4a49aa0f7": feeds.usdc_usd_feed.usdc_usd_median_feed,
    "a9b17c33422e2e576fb664d1d11d38c377b614d62f92653d006eca7bb2af1656": feeds.vesq.vsq_usd_median_feed,
    "6e5122118ce52cc9b97c359c1f174a3c21c71d810f7addce3484cc28e0be0f29": feeds.ric_usd_feed.ric_usd_median_feed,
    "3f640bf607feb4455c3eb10629385d823341cd18fef6f9f87b8bcfbeafc44eeb": feeds.sushi_usd_feed.sushi_usd_median_feed,
    "83245f6a6a2f6458558a706270fbcc35ac3a81917602c1313d3bfa998dcc2d4b": feeds.pls_usd_feed,
    "12906c5e9178631dba86f1f750f7ab7451c61e6357160eb890029b9eac1fb235": feeds.albt_usd_median_feed,
    "9e1b8afa9d013a06cc4048d1abc5d09b2509a53116db8b3e4a9aad0c88687c8a": feeds.aave_usd_median_feed,
    "0ea9091cc51722124ea273d517d3d3f7165559e7775e3dc3d086a305bad26e3b": feeds.avax_usd_median_feed,
    "7ea0d1d673fe38fcdff322c115b0031cdc56696928226701192052c05f00f613": feeds.badger_usd_median_feed,
    "efa84ae5ea9eb0545e159f78f0a44911ac5a81ecb6ff0c4e32107bcfc66c4baa": feeds.bch_usd_median_feed,
    "d34bdbc3f48515d7c3be63775e8e5657c5c281c0cf519e7f999b7020ae326b69": feeds.comp_usd_median_feed,
    "4212eec9815e6acb627893967d9ab4d81a5bd4d4ed24d9e3812ba5c54dce38c6": feeds.crv_usd_median_feed,
    "15d3cb16e8175919781af07b2ce06714d24f168284b1b47b14b6bfbe9a5a02ff": feeds.doge_usd_median_feed,
    "8810ffb0cfcb6131da29ed4b229f252d6bac6fc98fc4a61ffbde5b48131e0228": feeds.dot_usd_median_feed,
    "60723147b1b97df5ff4e69cf99b6a414acc7da119109811af59fe417730945fe": feeds.eth_btc_median_feed,
    "541e673f520d0d57fa13e38cc510e5e8752005b03030e1d3b843b85f5eb5a411": feeds.eul_usd_median_feed,
    "537422e5383888586f8f9bca62c5bfd8eb0f8c1bcd335b1a691e6b550c92dcce": feeds.fil_usd_median_feed,
    "791387543068bca4b983782967bc8e72b80d3e5a5bdf8250796377ec88b227aa": feeds.gno_usd_median_feed,
    "c138a64c42a40eb5ba8f64de1e62884a0e4259d8c34872c5d5d52a8fa426d697": feeds.link_usd_median_feed,
    "19585d912afb72378e3986a7a53f1eae1fbae792cd17e1d0df063681326823ae": feeds.ltc_usd_median_feed,
    "5a81384fbb9313d56e1510a0fd7e51617a796e2d5f8806e4a2f3b4e5d9999617": feeds.rai_usd_median_feed,
    "a3b64986889b3a1817db443d3846f9af51d6dc3058b13920afb37590f36b9ba1": feeds.shib_usd_median_feed,
    "b44a64a8c4f1006949b8f471594074e97c5f30ff86acffb2d2a13c00f3aa2da0": feeds.uni_usd_median_feed,
    "17408737cc4a2657852d14af840811cce2aa3ebb0c9176d2fdfd6abfa9400033": feeds.xdai_usd_median_feed,
    "c5acb66f4e3e0f6f9e5f52a45ccb9a8b2aef8366bf50f62faaa51248c4f67c41": feeds.yfi_usd_median_feed
    # "": feeds.diva_protocol_feed.assemble_diva_datafeed
}


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
