"""Helper functions."""
import os
from typing import Optional

from telliot_core.apps.telliot_config import TelliotConfig


def get_tx_explorer_url(tx_hash: str, cfg: TelliotConfig) -> str:
    """Get transaction explorer URL."""
    explorer: str = cfg.get_endpoint().explorer
    if explorer is not None:
        return explorer + "/tx/" + tx_hash
    else:
        return ""


def disputable_str(disputable: Optional[bool], query_id: str) -> str:
    """Return a string indicating whether the query is disputable."""
    if disputable is not None:
        return "yes ❗📲" if disputable else "no ✔️"
    return f"❗unsupported query ID: {query_id}"


def clear_console() -> None:
    """Clear the console."""
    # windows
    if os.name == "nt":
        _ = os.system("cls")
    # mac, linux (name=="posix")
    else:
        _ = os.system("clear")
