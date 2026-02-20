import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.core.keypairs import generate_seed, derive_keypair
from xrpl.wallet import Wallet
from xrpl.wallet import generate_faucet_wallet
from xrpl.transaction import autofill_and_sign, submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops

# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

class WalletAccount():
    def __init__(self):
        self.seed = generate_seed()






