Wallet
~~~~~~

Create a new wallet
-------------------

A new wallet can be created by using:

.. code-block:: python

   from peerplays import PeerPlays
   peerplays = PeerPlays()
   peerplays.wallet.create("supersecret-passphrase")

This will raise an exception if you already have a wallet installed.

Unlocking the wallet for signing
--------------------------------

The wallet can be unlocked for signing using

.. code-block:: python

   from peerplays import PeerPlays
   peerplays = PeerPlays()
   peerplays.wallet.unlock("supersecret-passphrase")

Adding a Private Key
--------------------

A private key can be added by using the
:func:`peerplays.wallet.Wallet.addPrivateKey` method that is available
**after** unlocking the wallet with the correct passphrase:

.. code-block:: python

   from peerplays import PeerPlays
   peerplays = PeerPlays()
   peerplays.wallet.unlock("supersecret-passphrase")
   peerplays.wallet.addPrivateKey("5xxxxxxxxxxxxxxxxxxxx")

.. note:: The private key has to be either in hexadecimal or in wallet
          import format (wif) (starting with a ``5``).

API
---

.. automodule:: peerplays.wallet
   :members:
