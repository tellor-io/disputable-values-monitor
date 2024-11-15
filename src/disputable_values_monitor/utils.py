"""Helper functions."""
import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from typing import Optional
from typing import Union

import click
from chained_accounts import ChainedAccount
from chained_accounts import find_accounts
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_feeds.utils.cfg import setup_account


def get_tx_explorer_url(tx_hash: str, cfg: TelliotConfig) -> str:
    """Get transaction explorer URL."""
    explorer: str = cfg.get_endpoint().explorer
    if explorer is not None:
        return explorer + "/tx/" + tx_hash
    else:
        return f"Explorer not defined for chain_id {cfg.main.chain_id}"


@dataclass
class Topics:
    """Topics for Tellor events."""

    # sha3("NewReport(bytes32,uint256,uint256,uint256,uint256)")
    NEW_REPORT: str = "0x48e9e2c732ba278de6ac88a3a57a5c5ba13d3d8370e709b3b98333a57876ca95"  # oracle.NewReport
    # sha3("NewOracleAddress(address,uint256)")
    NEW_ORACLE_ADDRESS: str = (
        "0x31f30a38b53d085dbe09f68f490447e9032b29de8deb5aae4ccd3577a09ff284"  # oracle.NewOracleAddress
    )
    # sha3("NewProposedOracleAddress(address,uint256)")
    NEW_PROPOSED_ORACLE_ADDRESS: str = (
        "0x8fe6b09081e9ffdaf91e337aba6769019098771106b34b194f1781b7db1bf42b"  # oracle.NewProposedOracleAddress
    )


@dataclass
class NewReport:
    """NewReport event."""

    tx_hash: str = ""
    submission_timestamp: int = 0  # timestamp attached to NewReport event (NOT the time retrieved by the DVM)
    chain_id: int = 0
    link: str = ""
    query_type: str = ""
    value: Union[str, bytes, float, int] = 0
    asset: str = ""
    currency: str = ""
    query_id: str = ""
    disputable: Optional[bool] = None
    status_str: str = ""


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


def select_account(
    cfg: TelliotConfig, account: Optional[str], password: Optional[str], skip_confirmations: Optional[bool]
) -> Optional[ChainedAccount]:
    """Select an account for disputing, allow no account to be chosen."""
    accounts = None
    if account is None:
        if skip_confirmations:
            return None
        else:
            run_alerts_only = click.confirm("Missing an account to send disputes. Run alerts only?")
            if not run_alerts_only:
                new_account = setup_account(cfg.main.chain_id)
                if new_account is not None:
                    click.echo(f"{new_account.name} selected!")
                    return new_account
                return None
            else:
                return None
    else:
        accounts = find_accounts(name=account)
        if password is None:
            accounts[0].unlock()
            click.echo(f"Your account name: {accounts[0].name if accounts else None}")
        else:
            accounts[0].unlock(password=password)
    return accounts[0]


def get_logger(name: str) -> logging.Logger:
    """DVM logger

    Returns a logger that logs to file. The name arg
    should be the current file name. For example:
    _ = get_logger(name=__name__)
    """
    log_format = "%(levelname)-7s | %(name)s | %(message)s"
    fh = logging.FileHandler("log.txt")
    formatter = logging.Formatter(log_format)
    fh.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)
    return logger


def are_all_attributes_none(obj: object) -> bool:
    """Check if all attributes of an object are None."""
    if not hasattr(obj, "__dict__"):
        return False
    for attr in obj.__dict__:
        if getattr(obj, attr) is not None:
            return False
    return True


def format_values(val: Any) -> Any:
    """shorten values for cli display"""
    if isinstance(val, float):
        return Decimal(f"{val:.4f}")
    elif len(str(val)) > 10:
        return f"{str(val)[:6]}...{str(val)[-5:]}"
    else:
        return val
