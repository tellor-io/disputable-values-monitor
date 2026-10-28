"""Utilities for the auto-disputer on Tellor on any EVM network"""

import asyncio
from typing import Any
from typing import Callable
from typing import Coroutine
from typing import Optional
from typing import Tuple

from chained_accounts import ChainedAccount
from telliot_core.apps.telliot_config import TelliotConfig
from web3 import Web3
from web3.exceptions import ContractLogicError

from disputable_values_monitor.config import AutoDisputerConfig
from disputable_values_monitor.data import get_contract
from disputable_values_monitor.utils import NewReport
from disputable_values_monitor.utils import get_logger

logger = get_logger(__name__)

DISPUTE_TX_RETRIES = 3
DISPUTE_RETRY_DELAY_SECONDS = 2.0


async def _submit_tx_with_retries(
    send: Callable[[], Coroutine[Any, Any, Tuple[Optional[Any], Any]]],
    label: str,
    chain_id: int,
    attempts: int = DISPUTE_TX_RETRIES,
    delay: float = DISPUTE_RETRY_DELAY_SECONDS,
) -> Tuple[Optional[Any], Any]:
    """Submit a dispute-related tx, retrying transient send/confirm failures.

    telliot_core's Contract.write returns a receipt whenever the tx was mined,
    including reverts. So a failed write with no receipt means the tx may never
    have been sent (or its receipt was never confirmed) and it is safe to build
    and submit again. A reverted tx mined on-chain is deterministic: never
    re-broadcast it.
    """

    tx_receipt, status = None, None
    for attempt in range(1, attempts + 1):
        tx_receipt, status = await send()
        if status.ok or tx_receipt is not None:
            return tx_receipt, status
        if attempt < attempts:
            logger.warning(
                f"{label} tx on chain_id {chain_id} not sent/confirmed"
                f" (attempt {attempt}/{attempts}): {status.error}; retrying"
            )
            await asyncio.sleep(delay * attempt)

    return tx_receipt, status


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
            " outside selected Monitored Feeds, skipping dispute"
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
    w3 = endpoint.web3
    token = get_contract(cfg, name="trb-token", account=account)
    governance = get_contract(cfg, name="tellor-governance", account=account)

    if token is None:
        logger.error(f"Unable to find token contract on chain_id {new_report.chain_id}")
        return ""

    if governance is None:
        logger.error(f"Unable to find governance contract on chain_id {new_report.chain_id}")
        return ""

    # read balance of user and log it
    user_token_balance, status = await token.read("balanceOf", Web3.to_checksum_address(account.address))

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
        acc_nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(account.address))
    except Exception as e:
        logger.error(f"Unable to dispute on chain_id {new_report.chain_id}: could not retrieve account nonce: {e}")
        return ""

    # write approve(governance contract, disputeFee) and log "token approved" if successful
    tx_receipt, status = await _submit_tx_with_retries(
        lambda: token.write(
            "approve",
            spender=governance.address,
            amount=dispute_fee * 100,
            gas_limit=60000,
            legacy_gas_price=w3.from_wei(w3.eth.gas_price, "gwei"),
            acc_nonce=acc_nonce,
        ),
        label="Approval",
        chain_id=new_report.chain_id,
    )

    if not status.ok or tx_receipt is None:
        logger.error(f"unable to approve tokens on chain_id {new_report.chain_id} for dispute fee: " + status.error)
        return ""

    logger.info("Approval Tx Hash: " + str(tx_receipt.transactionHash.hex()))

    begin_dispute_function = governance.contract.get_function_by_name("beginDispute")
    begin_dispute_tx = begin_dispute_function(
        _queryId=new_report.query_id,
        _timestamp=new_report.submission_timestamp,
    )
    msg = f"Unable to estimate gas usage for dispute on chain_id {new_report.chain_id}:"
    gas_limit: Optional[int] = None
    for attempt in range(1, DISPUTE_TX_RETRIES + 1):
        try:
            # Estimate gas usage amount
            gas_limit = begin_dispute_tx.estimate_gas({"from": Web3.to_checksum_address(account.address)})
            break
        except ContractLogicError as e:
            # deterministic revert on-chain: retrying cannot help
            logger.error(f"{msg} {e}")
            return ""
        except Exception as e:
            if attempt == DISPUTE_TX_RETRIES:
                logger.error(f"{msg} {e}")
                return ""
            logger.warning(
                f"Gas estimation for dispute on chain_id {new_report.chain_id} failed"
                f" (attempt {attempt}/{DISPUTE_TX_RETRIES}): {e}; retrying"
            )
            await asyncio.sleep(DISPUTE_RETRY_DELAY_SECONDS * attempt)

    assert gas_limit is not None  # every loop exit above either breaks or returns

    tx_receipt, status = await _submit_tx_with_retries(
        lambda: governance.write(
            func_name="beginDispute",
            _queryId=new_report.query_id,
            _timestamp=new_report.submission_timestamp,
            gas_limit=int(gas_limit * 1.2),
            legacy_gas_price=w3.from_wei(w3.eth.gas_price, "gwei"),
            acc_nonce=acc_nonce + 1,
        ),
        label="Dispute",
        chain_id=new_report.chain_id,
    )

    if not status.ok or tx_receipt is None:
        logger.error(
            f"unable to begin dispute on {new_report.query_id}"
            + f"at submission timestamp {new_report.submission_timestamp}:"
            + status.error
        )
        return ""

    new_report.disputable_str += ": disputed!"
    new_report.alertable_str += ": alerted!"
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

    stake_amount, status = await oracle.read(func_name="getStakeAmount")

    if not status.ok:
        logger.error(f"Unable to retrieve Stake Amount on chain_id {new_report.chain_id}")
        return None

    # Governance keys vote rounds by keccak256(abi.encodePacked(queryId, timestamp)),
    # not by the raw query id
    try:
        identifier_hash = Web3.solidity_keccak(
            ["bytes32", "uint256"],
            [bytes.fromhex(new_report.query_id[2:]), int(new_report.submission_timestamp)],
        )
    except Exception as e:
        logger.error(f"Unable to hash query id/timestamp for dispute fee on chain_id {new_report.chain_id}: {e}")
        return None

    vote_rounds, status = await governance.read("getVoteRounds", _hash=identifier_hash)

    if not status.ok:
        logger.error(
            f"Unable to count Vote Rounds on chain_id {new_report.chain_id} on query id " + new_report.query_id
        )
        return None

    # Replicate the on-chain fee calculation in Governance.beginDispute, which
    # pushes the new round (and increments openDisputesOnId for round 1 of a
    # report) BEFORE computing the fee: the on-chain round count is always one
    # higher than what the read contracts return.
    if len(vote_rounds) == 0:
        # first dispute round for this report: fee scales with open disputes
        # on the query id (counted after governance's increment)
        open_disputes_on_id, status = await governance.read(
            func_name="getOpenDisputesOnId", _queryId=new_report.query_id
        )

        if not status.ok:
            logger.error(
                f"Unable to count open disputes on chain_id {new_report.chain_id} on query id " + new_report.query_id
            )
            return None

        rounds = int(open_disputes_on_id) + 1
    else:
        # a dispute already exists for this report: this would be the next round
        rounds = len(vote_rounds) + 1

    if rounds > 4:
        dispute_fee = stake_amount
    else:
        dispute_fee = dispute_fee * 2 ** (rounds - 1)

    if dispute_fee > stake_amount:
        dispute_fee = stake_amount

    return int(dispute_fee)
