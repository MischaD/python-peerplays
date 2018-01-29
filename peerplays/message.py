import re
import json
import logging
from binascii import hexlify, unhexlify
from graphenebase.ecdsa import verify_message, sign_message
from peerplaysbase.account import PublicKey
from peerplays.instance import shared_peerplays_instance
from peerplays.account import Account
from .exceptions import (
    InvalidMessageSignature,
    AccountDoesNotExistsException
)
from .storage import configStorage as config


log = logging.getLogger(__name__)

MESSAGE_SPLIT = (
    "-----BEGIN PEERPLAYS SIGNED MESSAGE-----",
    "-----BEGIN META-----",
    "-----BEGIN SIGNATURE-----",
    "-----END PEERPLAYS SIGNED MESSAGE-----"
)

# This is the message that is actually signed
SIGNED_MESSAGE_META = """{message}
account={meta[account]}
memokey={meta[memokey]}
block={meta[block]}
timestamp={meta[timestamp]}"""

SIGNED_MESSAGE_ENCAPSULATED = """
{MESSAGE_SPLIT[0]}
{message}
{MESSAGE_SPLIT[1]}
account={meta[account]}
memokey={meta[memokey]}
block={meta[block]}
timestamp={meta[timestamp]}
{MESSAGE_SPLIT[2]}
{signature}
{MESSAGE_SPLIT[3]}
"""


class Message():

    def __init__(self, message, peerplays_instance=None):
        self.peerplays = peerplays_instance or shared_peerplays_instance()
        self.message = message

    def sign(self, account=None, **kwargs):
        """ Sign a message with an account's memo key

            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)
            :raises ValueError: If not account for signing is provided

            :returns: the signed message encapsulated in a known format
        """
        if not account:
            if "default_account" in config:
                account = config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        # Data for message
        account = Account(account, peerplays_instance=self.peerplays)
        info = self.peerplays.info()
        meta = dict(
            timestamp=info["time"],
            block=info["head_block_number"],
            memokey=account["options"]["memo_key"],
            account=account["name"])

        # wif key
        wif = self.peerplays.wallet.getPrivateKeyForPublicKey(
            account["options"]["memo_key"]
        )

        # We strip the message here so we know for sure there are no trailing
        # whitespaces or returns
        message = self.message.strip()

        enc_message = SIGNED_MESSAGE_META.format(**locals())

        # signature
        signature = hexlify(sign_message(
            enc_message,
            wif
        )).decode("ascii")

        return SIGNED_MESSAGE_ENCAPSULATED.format(
            MESSAGE_SPLIT=MESSAGE_SPLIT,
            **locals()
        )

    def verify(self, **kwargs):
        """ Verify a message with an account's memo key

            :param str account: (optional) the account that owns the bet
                (defaults to ``default_account``)

            :returns: True if the message is verified successfully
            :raises InvalidMessageSignature if the signature is not ok
        """
        # Split message into its parts
        parts = re.split("|".join(MESSAGE_SPLIT), self.message)
        parts = [x for x in parts if x.strip()]

        assert len(parts) > 2, "Incorrect number of message parts"

        # Strip away all whitespaces before and after the message
        message = parts[0].strip()
        signature = parts[2].strip()
        # Parse the meta data
        meta = dict(re.findall(r'(\S+)=(.*)', parts[1]))

        log.info("Message is: {}".format(message))
        log.info("Meta is: {}".format(json.dumps(meta)))
        log.info("Signature is: {}".format(signature))

        # Ensure we have all the data in meta
        assert "account" in meta, "No 'account' could be found in meta data"
        assert "memokey" in meta, "No 'memokey' could be found in meta data"
        assert "block" in meta, "No 'block' could be found in meta data"
        assert "timestamp" in meta, "No 'timestamp' could be found in meta data"

        account_name = meta.get("account").strip()
        memo_key = meta["memokey"].strip()

        try:
            PublicKey(memo_key)
        except Exception:
            raise InvalidMemoKeyException(
                "The memo key in the message is invalid"
            )

        # Load account from blockchain
        try:
            account = Account(
                account_name,
                peerplays_instance=self.peerplays)
        except AccountDoesNotExistsException:
            raise AccountDoesNotExistsException(
                "Could not find account {}. Are you connected to the right chain?".format(
                    account_name
                ))

        # Test if memo key is the same as on the blockchain
        if not account["options"]["memo_key"] == memo_key:
            log.error(
                "Memo Key of account {} on the Blockchain".format(
                    account["name"]) +
                "differs from memo key in the message: {} != {}".format(
                    account["options"]["memo_key"], memo_key
                )
            )

        # Reformat message
        enc_message = SIGNED_MESSAGE_META.format(**locals())

        # Verify Signature
        pubkey = verify_message(enc_message, unhexlify(signature))

        # Verify pubky
        pk = PublicKey(hexlify(pubkey).decode("ascii"))
        if format(pk, self.peerplays.prefix) != memo_key:
            raise InvalidMessageSignature

        return True