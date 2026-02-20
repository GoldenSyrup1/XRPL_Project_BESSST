import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.core.keypairs import generate_seed, derive_keypair
from xrpl.account import get_balance
from xrpl.wallet import Wallet
from xrpl.wallet import generate_faucet_wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.utils import xrp_to_drops

# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

class XRPAccount():
    def __init__(self):
        self.wallet = Wallet.create()
        self.address = self.wallet.classic_address
        self.seed = self.wallet.seed
        self.private_key = self.wallet.private_key
        self.public_key = self.wallet.public_key
        self.xrp_amount = get_balance(self.address, client) / 1,000,000
    def send_xrp(self, xrp_amount, recieving_wallet):
        payment = xrpl.models.transactions.Payment(
            account=self.address,
            amount=xrpl.utils.xrp_to_drops(int(xrp_amount)),
            destination=recieving_wallet.address,
        )
        try:
            response = submit_and_wait(payment, client, self.wallet)
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            response = f"Submit failed: {e}"
        return response









