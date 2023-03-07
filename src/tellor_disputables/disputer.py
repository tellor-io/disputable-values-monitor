"""Utilities for the auto-disputer on Tellor on any EVM network"""
import logging
from dataclasses import dataclass
from chained_accounts import ChainedAccount


from telliot_core.apps.telliot_config import TelliotConfig


from tellor_disputables.data import get_contract
from tellor_disputables.utils import NewReport

async def dispute(cfg: TelliotConfig, account: ChainedAccount, new_report: NewReport) -> None:
    """Main dispute logic for auto-disputer"""

    cfg.main.chain_id = new_report.chain_id

    token = get_contract(cfg, name="trb-token") #TODO test
    governance = get_contract(cfg, name="tellor-governance")

    if token is None:
        logging.log("Unable to find token contract")
        return None
    
    if governance is None:
        logging.log("Unable to find governance contract")
        return None


    # read balance of user and log it
    user_token_balance, status = await token.read(func_name="balanceOf", _address=account.address)

    # read dispute fee and log it
    dispute_fee, status = await governance.read(func_name="disputeFee")

    # if balanceOf(user) < disputeFee, log "need more tokens to initiate dispute"
    if user_token_balance < dispute_fee:
        logging.info("User balance is below dispute fee: need more tokens to initiate dispute")
        return None

    # write approve(governance contract, disputeFee) and log "token approved" if successful
    tx_receipt, status = await token.write(func_name="approve", _spender=governance.address, _amount=dispute_fee)

    if not status.ok:
        logging.error("unable to approve tokens for dispute fee:" + status.msg)
        return None

    logging.info("Approval Tx Receipt: ", tx_receipt)

    # Write beginDispute(queryId, timestamp) and log “chain id <chain id>: dispute #(number of disputeId) initiated on query <Decoded Query Type w/ Parameters> – <queryId> at timestamp <Timestamp>
    tx_receipt, status = await governance.write(func_name="beginDispute", _queryId=new_report.query_id, _timestamp=new_report.submission_timestamp)

    if not status.ok:
        logging.error(f"unable to begin dispute on {new_report.query_id} at submission timestamp {new_report.submission_timestamp}:" + status.msg)
        return None

    logging.info("Dispute Tx Receipt: ", tx_receipt)
