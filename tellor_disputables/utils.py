import streamlit as st 
import os
from web3.datastructures import AttributeDict
from hexbytes import HexBytes


def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.environ.get("PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True


def remove_default_index_col():
    # CSS to inject contained in a string
    hide_table_row_index = """
                <style>
                tbody th {display:none}
                .blank {display:none}
                </style>
                """

    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)


def get_tx_explorer_url(tx_hash: str, chain_id: int) -> str:
    explorers = {
        1: "https://etherscan.io/",
        4: "https://rinkeby.etherscan.io/",
        137: "https://polygonscan.com/",
        80001: "https://mumbai.polygonscan.com/",
    }
    base_url = explorers[chain_id]
    return f"{base_url}tx/{tx_hash}"


def disputable_str(disputable: bool) -> str:
    return "yes ❗📲" if disputable else "no ✔️"


# OHM/ETH SpotPrice
EXAMPLE_NEW_REPORT_EVENT = AttributeDict({
    'address': '0x41b66dd93b03e89D29114a7613A6f9f0d4F40178',
    'blockHash': HexBytes('0x61967b410ac2ef5352e1bc0c06ab63fb84ba9161276a4645aca389fd01409ef7'),
    'blockNumber': 25541322,
    'data': '0xee4fcdeed773931af0bcd16cfcea5b366682ffbd4994cf78b4f0a6a40b5703400000000000000000000000000000000000000000000000000000000062321eec00000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000003a0000000000000000000000000000000000000000000000000000000000000100000000000000000000000000d5f1cc896542c111c7aa7d7fae2c3d654f34b927000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000248c37b20efbff000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000953706f745072696365000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000036f686d000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000036574680000000000000000000000000000000000000000000000000000000000',
    'logIndex': 101,
    'removed': False,
    'topics': [HexBytes('0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95')],
    'transactionHash': HexBytes('0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4'),
    'transactionIndex': 1
})

# OHM/ETH SpotPrice
EXAMPLE_NEW_REPORT_EVENT_TX_RECEIPT = (AttributeDict({
    'args': AttributeDict({
        '_queryId': b'\xeeO\xcd\xee\xd7s\x93\x1a\xf0\xbc\xd1l\xfc\xea[6f\x82\xff\xbdI\x94\xcfx\xb4\xf0\xa6\xa4\x0bW\x03@',
        '_time': 1647451884,
        '_value': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00$\x8c7\xb2\x0e\xfb\xff',
        '_nonce': 58,
        '_queryData': b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\tSpotPrice\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00@\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03ohm\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03eth\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
        '_reporter': '0xd5f1Cc896542C111c7Aa7D7fae2C3D654f34b927'
        }),
    'event': 'NewReport',
    'logIndex': 101,
    'transactionIndex': 1,
    'transactionHash': HexBytes('0x0b91b05c53c527918615be6914ec087275d80a454a468977409da1634f25cbf4'),
    'address': '0x41b66dd93b03e89D29114a7613A6f9f0d4F40178',
    'blockHash': HexBytes('0x61967b410ac2ef5352e1bc0c06ab63fb84ba9161276a4645aca389fd01409ef7'),
    'blockNumber': 25541322})
,)