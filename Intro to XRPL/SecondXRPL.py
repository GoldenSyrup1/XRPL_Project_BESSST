from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.models.transactions import NFTokenMint, Payment
from xrpl.models.requests import AccountLines
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex, xrp_to_drops
import uuid

client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Registry of accounts: phone -> XRPAccount object
accounts_registry = {}

class XRPAccount:
    registry = {}
    def __init__(self, username):
        self.username = username
        self.wallet = Wallet.create()
        self.address = self.wallet.classic_address
        self.nft_uri = str_to_hex(f"urn:uuid:{uuid.uuid4()}")
        generate_faucet_wallet(client=client, wallet=self.wallet)
        XRPAccount.registry[username] = self

    def get_xrp_balance(self):
        from xrpl.models.requests import AccountInfo
        request = AccountInfo(account=self.address, ledger_index="validated")
        response = client.request(request)
        drops = response.result["account_data"]["Balance"]
        return int(drops)/1_000_000

    def send_xrp(self, amount, destination):
        tx = Payment(account=self.address, destination=destination.address, amount=xrp_to_drops(amount))
        response = submit_and_wait(tx, client, self.wallet)
        return response.is_successful()

    def create_nft_xrp_token(self, royalty=1000):
        from xrpl.models.transactions import NFTokenMint
        if royalty > 50000: royalty = 50000
        mint = NFTokenMint(
            account=self.address,
            uri=self.nft_uri,
            nftoken_taxon=0,
            transfer_fee=royalty,
            flags=8
        )
        response = submit_and_wait(mint, client, self.wallet)
        return response.is_successful(), self.nft_uri

# Helper functions
def create_xrp_account(phone, username):
    if phone in accounts_registry:
        return accounts_registry[phone]
    account = XRPAccount(username)
    accounts_registry[phone] = account
    return account

def get_account_by_phone(phone):
    return accounts_registry.get(phone)