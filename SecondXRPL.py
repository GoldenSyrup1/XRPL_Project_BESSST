import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.core.keypairs import generate_seed, derive_keypair
from xrpl.account import get_balance
from xrpl.wallet import Wallet

from xrpl.wallet import generate_faucet_wallet
from xrpl.transaction import submit_and_wait
from xrpl.models import Payment, Tx
from xrpl.models.requests import AccountInfo
from xrpl.utils import xrp_to_drops
from xrpl.models.transactions import TrustSet
from xrpl.models.amounts import IssuedCurrencyAmount

# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

class XRPAccount():
    def __init__(self, username):
        self.username = username
        self.wallet = Wallet.create()
        self.address = self.wallet.classic_address
        self.seed = self.wallet.seed
        self.private_key = self.wallet.private_key
        self.public_key = self.wallet.public_key
        generate_faucet_wallet(client = client, wallet = self.wallet)

    def send_xrp(self, xrp_amount, recieving_wallet):
        if float(xrp_amount) > float(recieving_wallet.get_account_balance()):
            return ("Sorry. You are sending more XRP than you have in your wallet. If you wish" +
                    " to send XRP, try lowering the amount.")
        payment = Payment(
            account=self.address,
            amount=xrpl.utils.xrp_to_drops(float(xrp_amount)),
            destination=recieving_wallet.address,
        )
        try:
            payment_response = submit_and_wait(payment, client, self.wallet)
            print("Transaction was submitted.")

            # Create a "Tx" request to look up the transaction on the ledger
            tx_response = client.request(Tx(transaction=payment_response.result["hash"]))

            # Check whether the transaction was actually validated on ledger
            print("Validated:", tx_response.result["validated"])
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            return f"Submit failed: {e}"



    def get_account_balance(self):
        acct_info_request = AccountInfo(
            account=self.wallet.classic_address,
            ledger_index="validated",
        )

        # Send the request and get the response
        response = client.request(acct_info_request)
        balance_drops = response.result['account_data']['Balance']

        balance_xrp = balance_drops / 1000000
        return balance_xrp
    def create_TrustSet(self, currency_type, value, recipient):
        trust_set_tx = TrustSet(
            account=self.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_type,
                issuer=recipient.address,
                value=value  # I am willing to hold up to value [currency type]
            )
        )
        response = submit_and_wait(trust_set_tx, client, recipient.address)
        print(f"Transaction Result: {response.result['meta']['TransactionResult']}")


acct1 = XRPAccount("Joe Biden")
acct2 = XRPAccount("Obama69")
print(acct1.get_account_balance())
print(acct2.get_account_balance())
acct1.send_xrp(5, acct2)
print(acct1.get_account_balance())
print(acct2.get_account_balance())









