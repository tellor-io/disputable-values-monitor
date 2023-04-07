"""Utilities for the auto-disputer on Tellor on any EVM network"""
from typing import Optional

from chained_accounts import ChainedAccount
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.gas.legacy_gas import fetch_gas_price
from web3 import Web3

from tellor_disputables.config import AutoDisputerConfig
from tellor_disputables.data import get_contract
from tellor_disputables.utils import get_logger
from tellor_disputables.utils import NewReport

logger = get_logger(__name__)


async def dispute(
    cfg: TelliotConfig, disp_cfg: AutoDisputerConfig, account: Optional[ChainedAccount], new_report: NewReport
) -> str:
    """Main dispute logic for auto-disputer"""

    if not disp_cfg.monitored_feeds:
        logger.info("Currently not auto-dispuing on any feeds. See ./disputer-config.yaml")
        return ""

    meant_to_dispute = new_report.query_id[2:] in [feed.feed.query.query_id.hex() for feed in disp_cfg.monitored_feeds]

    if not meant_to_dispute:
        logger.info("Found disputable new report outside selected Monitored Feeds, skipping dispute")
        return ""

    if account is None:
        logger.info("No account provided, skipping eligible dispute")
        return ""

    cfg.main.chain_id = new_report.chain_id

    token = get_contract(cfg, name="trb-token", account=account)
    governance = get_contract(cfg, name="tellor-governance", account=account)

    if token is None:
        logger.error("Unable to find token contract")
        return ""

    if governance is None:
        logger.error("Unable to find governance contract")
        return ""

    # read balance of user and log it
    user_token_balance, status = await token.read("balanceOf", Web3.toChecksumAddress(account.address))

    if not status.ok:
        logger.error("Unable to retrieve Disputer account balance")
        return ""

    logger.info(f"Disputer ({account.address}) balance: " + str(user_token_balance))

    dispute_fee = await get_dispute_fee(cfg, new_report)

    if dispute_fee is None:
        logger.error("Unable to calculate Dispute Fee from contracts")
        return ""

    logger.info("Dispute Fee: " + str(dispute_fee / 1e18) + " TRB")

    # if balanceOf(user) < disputeFee, log "need more tokens to initiate dispute"
    if user_token_balance < dispute_fee:
        logger.info("User balance is below dispute fee: need more tokens to initiate dispute")
        return ""

    # write approve(governance contract, disputeFee) and log "token approved" if successful
    gas_price = await fetch_gas_price()
    tx_receipt, status = await token.write(
        "approve", spender=governance.address, amount=dispute_fee * 100, gas_limit=60000, legacy_gas_price=gas_price
    )

    if not status.ok:
        logger.error("unable to approve tokens for dispute fee: " + status.error)
        return ""

    logger.info("Approval Tx Hash: " + str(tx_receipt.transactionHash.hex()))

    tx_receipt, status = await governance.write(
        func_name="beginDispute",
        _queryId=new_report.query_id,
        _timestamp=new_report.submission_timestamp,
        gas_limit=800000,
        legacy_gas_price=gas_price,
    )

    if not status.ok:
        logger.error(
            f"unable to begin dispute on {new_report.query_id}"
            + f"at submission timestamp {new_report.submission_timestamp}:"
            + status.error
        )
        return ""

    new_report.status_str += ": disputed!"
    explorer = cfg.get_endpoint().explorer
    if not explorer:
        dispute_tx_link = str(tx_receipt.transactionHash.hex())
    else:
        dispute_tx_link = explorer + str(tx_receipt.transactionHash.hex())

    logger.info("Dispute Tx Link: " + dispute_tx_link)
    return "Dispute Tx Link: " + dispute_tx_link


async def get_dispute_fee(cfg: TelliotConfig, new_report: NewReport) -> Optional[int]:
    """Calculate dispute fee on a Tellor network"""

    governance = get_contract(cfg, name="tellor-governance", account=None)
    oracle = get_contract(cfg, name="tellor360-oracle", account=None)

    if governance is None:
        logger.error("Unable to find governance contract")
        return None

    if oracle is None:
        logger.error("Unable to find oracle contract")
        return None

    # simple dispute fee
    dispute_fee, status = await governance.read(func_name="getDisputeFee")

    if not status.ok:
        logger.error("Unable to retrieve Dispute Fee")
        return None

    vote_rounds, status = await governance.read("getVoteRounds", _hash=new_report.query_id)

    if not status.ok:
        logger.error("Unable to count Vote Rounds on query id " + new_report.query_id)

    if len(vote_rounds) == 1:
        # dispute fee with open disputes on the ID
        open_disputes_on_id, status = await governance.read(
            func_name="getOpenDisputesOnId", _queryId=new_report.query_id
        )

        if not status.ok:
            logger.error("Unable to count open disputes on query id " + new_report.query_id)
            return None

        multiplier = open_disputes_on_id - 1 if open_disputes_on_id > 0 else 0
        dispute_fee = dispute_fee * 2 ** (multiplier)
    else:
        multiplier = len(vote_rounds) - 1 if len(vote_rounds) > 0 else 0
        dispute_fee = dispute_fee * 2 ** (multiplier)

    stake_amount, status = await oracle.read(func_name="getStakeAmount")

    if not status.ok:
        logger.error("Unable to retrieve Stake Amount")
        return None

    if dispute_fee > stake_amount:
        dispute_fee = stake_amount

    return int(dispute_fee)
