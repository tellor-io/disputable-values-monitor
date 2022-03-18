from typing import Optional


def get_tx_explorer_url(tx_hash: str, chain_id: int) -> str:
    explorers = {
        1: "https://etherscan.io/",
        4: "https://rinkeby.etherscan.io/",
        137: "https://polygonscan.com/",
        80001: "https://mumbai.polygonscan.com/",
    }
    base_url = explorers[chain_id]
    return f"{base_url}tx/{tx_hash}"


def disputable_str(disputable: Optional[bool], query_id: str) -> str:
    if disputable is not None:
        return "yes ❗📲" if disputable else "no ✔️"
    return f"❗unsupported query ID: {query_id}"
