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

    disputable_query_ids = []
    for feed in disp_cfg.monitored_feeds:
        try:
            disputable_query_id = feed.feed.query.query_id.hex()
        except Exception:
            pass
        disputable_query_ids.append(disputable_query_id)

    meant_to_dispute = new_report.query_id[2:] in disputable_query_ids

    if not meant_to_dispute:
        logger.info(
            f"Found disputable new report on chain_id {new_report.chain_id}"
            "outside selected Monitored Feeds, skipping dispute"
        )
        return ""

    if account is None:
        logger.info(f"No account provided, skipping eligible dispute on chain_id {new_report.chain_id}")
        return ""

    cfg.main.chain_id = new_report.chain_id

    try:
        endpoint = cfg.get_endpoint()
    except ValueError:
        logger.error(f"Unable to dispute: can't find an endpoint on chain id {new_report.chain_id}")
        return ""

    try:
        endpoint.connect()
    except ValueError:
        logger.error(f"Unable to dispute: can't connect to endpoint on chain id {new_report.chain_id}")
        return ""

    token = get_contract(cfg, name="trb-token", account=account)
    governance = get_contract(cfg, name="tellor-governance", account=account)

    if token is None:
        logger.error(f"Unable to find token contract on chain_id {new_report.chain_id}")
        return ""

    if governance is None:
        logger.error(f"Unable to find governance contract on chain_id {new_report.chain_id}")
        return ""

    # read balance of user and log it
    user_token_balance, status = await token.read("balanceOf", Web3.toChecksumAddress(account.address))

    if not status.ok:
        logger.error("Unable to retrieve Disputer account balance")
        return ""

    logger.info(f"Disputer ({account.address}) balance on chain_id {new_report.chain_id}: " + str(user_token_balance))

    dispute_fee = await get_dispute_fee(cfg, new_report)

    if dispute_fee is None:
        logger.error(f"Unable to calculate Dispute Fee from contracts on chain_id {new_report.chain_id}")
        return ""

    logger.info(f"Dispute Fee on chain_id {new_report.chain_id}: " + str(dispute_fee / 1e18) + " TRB")

    # if balanceOf(user) < disputeFee, log "need more tokens to initiate dispute"
    if user_token_balance < dispute_fee:
        logger.info(
            f"User balance on chain_id {new_report.chain_id} is below dispute fee: need more tokens to initiate dispute"
        )
        return ""

    try:
        acc_nonce = endpoint.web3.eth.get_transaction_count(Web3.toChecksumAddress(account.address))
    except Exception as e:
        logger.error(f"Unable to dispute on chain_id {new_report.chain_id}: could not retrieve account nonce: {e}")
        return ""

    # write approve(governance contract, disputeFee) and log "token approved" if successful
    gas_price = await fetch_gas_price()
    tx_receipt, status = await token.write(
        "approve",
        spender=governance.address,
        amount=dispute_fee * 100,
        gas_limit=60000,
        legacy_gas_price=gas_price,
        acc_nonce=acc_nonce,
    )

    if not status.ok:
        logger.error(f"unable to approve tokens on chain_id {new_report.chain_id} for dispute fee: " + status.error)
        return ""

    logger.info("Approval Tx Hash: " + str(tx_receipt.transactionHash.hex()))

    tx_receipt, status = await governance.write(
        func_name="beginDispute",
        _queryId=new_report.query_id,
        _timestamp=new_report.submission_timestamp,
        gas_limit=800000,
        legacy_gas_price=gas_price,
        acc_nonce=acc_nonce + 1,
    )

    if not status.ok:
        logger.error(
            f"unable to begin dispute on {new_report.query_id}"
            + f"at submission timestamp {new_report.submission_timestamp}:"
            + status.error
        )
        return ""

    new_report.status_str += ": disputed!"
    explorer = endpoint.explorer
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
        logger.error(f"Unable to find governance contract on chain_id {new_report.chain_id}")
        return None

    if oracle is None:
        logger.error(f"Unable to find oracle contract on chain_id {new_report.chain_id}")
        return None

    # simple dispute fee
    dispute_fee, status = await governance.read(func_name="getDisputeFee")

    if not status.ok:
        logger.error(f"Unable to retrieve Dispute Fee on chain_id {new_report.chain_id}")
        return None

    vote_rounds, status = await governance.read("getVoteRounds", _hash=new_report.query_id)

    if not status.ok:
        logger.error(
            f"Unable to count Vote Rounds on chain_id {new_report.chain_id} on query id " + new_report.query_id
        )

    if len(vote_rounds) == 1:
        # dispute fee with open disputes on the ID
        open_disputes_on_id, status = await governance.read(
            func_name="getOpenDisputesOnId", _queryId=new_report.query_id
        )

        if not status.ok:
            logger.error(
                f"Unable to count open disputes on chain_id {new_report.chain_id} on query id " + new_report.query_id
            )
            return None

        multiplier = open_disputes_on_id - 1 if open_disputes_on_id > 0 else 0
        dispute_fee = dispute_fee * 2 ** (multiplier)
    else:
        multiplier = len(vote_rounds) - 1 if len(vote_rounds) > 0 else 0
        dispute_fee = dispute_fee * 2 ** (multiplier)

    stake_amount, status = await oracle.read(func_name="getStakeAmount")

    if not status.ok:
        logger.error(f"Unable to retrieve Stake Amount on chain_id {new_report.chain_id}")
        return None

    if dispute_fee > stake_amount:
        dispute_fee = stake_amount

    return int(dispute_fee)
