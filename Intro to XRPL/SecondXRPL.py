from xrpl.clients import JsonRpcClient
from xrpl.models import Payment
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.requests import AccountInfo, AccountLines
from xrpl.models.transactions import NFTokenMint
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex
from xrpl.utils import xrp_to_drops
from xrpl.wallet import Wallet, generate_faucet_wallet
import uuid
# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

class XRPAccount:
    registry = {}  # address -> XRPAccount object
    def __init__(self, username):
        self.username = username
        self.wallet = Wallet.create()
        self.address = self.wallet.classic_address
        self.nft_uri = str_to_hex(f"urn:uuid:{uuid.uuid4()}")
        # Fund account with 100 Test XRP
        # Register automatically
        XRPAccount.registry[self.address] = self
        generate_faucet_wallet(client=client, wallet=self.wallet)

    def get_xrp_balance(self):
        request = AccountInfo(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)
        drops = response.result["account_data"]["Balance"]

        return int(drops) / 1_000_000

    def send_xrp(self, amount, destination):

        tx = Payment(
            account=self.address,
            destination=destination.address,
            amount=xrp_to_drops(amount)
        )

        response = submit_and_wait(tx, client, self.wallet)

        if response.is_successful():
            print(f"{self.username} sent {amount} XRP to {destination.username}")
        else:
            print("XRP send failed")


    def create_trustline(self, currency, issuer, limit):

        tx = TrustSet(
            account=self.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value=str(limit)
            )
        )

        response = submit_and_wait(tx, client, self.wallet)

        if response.is_successful():
            print(f"{self.username}: Trustline created for {currency}")
        else:
            print(f"{self.username}: Trustline failed")

    def send_token(self, currency, amount, destination):

        tx = Payment(
            account=self.address,
            destination=destination.address,
            amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=self.address,
                value=str(amount)
            )
        )

        response = submit_and_wait(tx, client, self.wallet)

        if response.is_successful():
            print(f"{self.username} sent {amount} {currency} to {destination.username}")
        else:
            print("Token send failed")

    def create_nft_xrp_token(self, royalty):
        if royalty > 50000:
            royalty = 50000
        mint = NFTokenMint(
        account=self.address,
        uri=self.nft_uri,
        nftoken_taxon=0,
        transfer_fee=royalty,
        flags=8
    )
        # deducts 0.2 xrp for setting up nft
        response = submit_and_wait(mint, client, self.wallet)
        if response.is_successful():
            print(f"{self.username} has created an NFT.")
        else:
            print("NFT Token creation failed.")
    def create_offer_nft(self, buyer_of_nft, xrp_amount):
        
        return
    def get_token_balance(self, currency, issuer):

        request = AccountLines(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)

        for line in response.result.get("lines", []):
            if line["currency"] == currency and line["account"] == issuer.address:
                return float(line["balance"])

        return 0.0

    def create_offer(
        self,
        pay_currency,
        pay_amount,
        get_currency,
        get_amount,
        pay_issuer=None,
        get_issuer=None
    ):

        if pay_currency == "XRP":
            taker_pays = xrp_to_drops(pay_amount)
        else:
            taker_pays = IssuedCurrencyAmount(
                currency=pay_currency,
                issuer=pay_issuer.address,
                value=str(pay_amount)
            )

        if get_currency == "XRP":
            taker_gets = xrp_to_drops(get_amount)
        else:
            taker_gets = IssuedCurrencyAmount(
                currency=get_currency,
                issuer=get_issuer.address,
                value=str(get_amount)
            )

        tx = OfferCreate(
            account=self.address,
            taker_pays=taker_pays,
            taker_gets=taker_gets
        )

        response = submit_and_wait(tx, client, self.wallet)

        if response.is_successful():
            print(
                f"{self.username} created offer: "
                f"Pay {pay_amount} {pay_currency} "
                f"for {get_amount} {get_currency}"
            )
        else:
            print("Offer failed")

    def print_holdings(self):

        print(f"\n{self.username} holdings:")

        print("XRP:", self.get_xrp_balance())

        request = AccountLines(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)

        for line in response.result.get("lines", []):
            issuer_address = line["account"]

            # Instant lookup
            issuer = XRPAccount.registry.get(issuer_address)

            issuer_name = issuer.username if issuer else issuer_address

            print(f"{line['currency']} issued by {issuer_name}: {line['balance']}")


# standard account will always have 100 xrp
# ============================
# CREATE ACCOUNTS
# ============================

issuer = XRPAccount("Issuer")
alice = XRPAccount("Alice")
bob = XRPAccount("Bob")

print("\nInitial XRP balances: ")
print("Issuer:", issuer.get_xrp_balance())
print("Alice:", alice.get_xrp_balance())
print("Bob:", bob.get_xrp_balance())


# ============================
# CREATE TRUSTLINE
# ============================

alice.create_trustline("AUD", issuer, 10000)
bob.create_trustline("AUD", issuer, 10000)


# ============================
# ISSUE TOKENS
# ============================

issuer.send_token("AUD", 5000, alice)
issuer.send_token("AUD", 2000, bob)


# ============================
# SEND XRP
# ============================

issuer.send_xrp(10, alice)


# ============================
# CREATE DEX OFFER
# Alice sells AUD for XRP
# ============================

alice.create_offer(
    pay_currency="AUD",
    pay_amount=1000,
    get_currency="XRP",
    get_amount=500,
    pay_issuer=issuer
)


# ============================
# FINAL HOLDINGS
# ============================

issuer.print_holdings()
alice.print_holdings()
bob.print_holdings()