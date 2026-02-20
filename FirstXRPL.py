import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.core.keypairs import generate_seed, derive_keypair
from xrpl.account import get_balance
from xrpl.wallet import Wallet
from xrpl.wallet import generate_faucet_wallet
from xrpl.transaction import submit_and_wait
from xrpl.models.transactions import Payment
from xrpl.models.requests import AccountInfo
from xrpl.utils import xrp_to_drops

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
        payment = xrpl.models.transactions.Payment(
            account=self.address,
            amount=xrpl.utils.xrp_to_drops(float(xrp_amount)),
            destination=recieving_wallet.address,
        )
        try:
            response = submit_and_wait(payment, client, self.wallet)
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            response = f"Submit failed: {e}"
        print(response.result)
        print(f"Congratulations. {self.username} has sent {xrp_amount} to {recieving_wallet.username}")
        return response
    def get_account_balance(self):
        acct_info_request = AccountInfo(
            account=self.wallet.classic_address,
            ledger_index="validated",
        )

        # Send the request and get the response
        response = client.request(acct_info_request)
        balance_drops = response.result['account_data']['Balance']

        balance_xrp = int(balance_drops) / 1000000
        return balance_xrp


acct1 = XRPAccount("Joe Biden")
acct2 = XRPAccount("Obama69")
print(acct1.get_account_balance())
print(acct2.get_account_balance())
acct1.send_xrp(5, acct2)
print(acct1.get_account_balance())
print(acct2.get_account_balance())









